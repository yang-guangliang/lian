#!/usr/bin/env python3

from pathlib import Path
import os,sys
import pprint
from ctypes import c_void_p, cdll
import tree_sitter
import importlib
from lian.apps.app_manager import AppManager
from lian.util import util
from lian.config import lang_config
from lian.config import config
from lian.config.constants import EventKind

from lian.apps.app_template import EventData
from lian.util.loader import Loader

EXTENSIONS_LANG = lang_config.EXTENSIONS_LANG

def determine_lang_by_path(file_path):
    ext = os.path.splitext(file_path)[1]
    return EXTENSIONS_LANG.get(ext, None)

@profile
def is_empty_strict_version(node):
    """
    严格模式检查数据结构是否为空：
    1. 递归遍历列表/集合元素
    2. 检查字典键值对存在性
    3. 所有嵌套结构均为空时返回True
    """
    if not node:
        return True

    if isinstance(node, list) or isinstance(node, set):
        for child in node:
            if not is_empty(child):
                return False
        return True

    elif isinstance(node, dict):
        for myvalue in node.values():
            if not is_empty(myvalue):
                return False
        return True

    return False

def is_empty(node):
    """
    快速检查数据结构是否为空：
    1. 直接判断空值或空集合
    2. 对字典仅检查键数量
    """
    if not node:
        return True

    if isinstance(node, list) or isinstance(node, set):
        for child in node:
            if not is_empty(child):
                return False
        return True

    elif isinstance(node, dict):
        if len(node) > 0:
            return False
        return True

    return False


class GIRProcessing:
    def __init__(self, node_id):
        self.node_id = node_id

    def assign_id(self):
        """
        生成连续唯一ID：
        1. 递增维护内部计数器
        2. 返回前一个ID值
        """
        previous = self.node_id
        self.node_id += 1
        return previous

    def get_id_from_node(self, node):
        """
        从节点提取或分配语句ID：
        1. 检查节点是否包含stmt_id字段
        2. 不存在时调用assign_id生成新ID
        """
        if "stmt_id" not in node:
            node["stmt_id"] = self.assign_id()
        return node["stmt_id"]

    def init_stmt_id(self, stmt, parent_stmt_id):
        stmt["parent_stmt_id"] = parent_stmt_id
        stmt["stmt_id"] = self.assign_id()

    def is_gir_format(self, stmts):
        """
        验证GIR格式有效性：
        1. 检查是否为非空列表
        2. 验证首个元素为字典类型
        """
        if stmts and isinstance(stmts, list) and len(stmts) > 0 \
           and stmts[0] and isinstance(stmts[0], dict):
            return True

        return False

    def flatten_stmt(self, stmt, last_node: dict, dataframe, parent_stmt_id = 0):
        """
        扁平化处理单个语句：
        1. 初始化扁平化节点结构
        2. 处理变量声明的from属性继承
        3. 递归处理子节点内容
        4. 构建操作类型到内容的映射
        """
        if not isinstance(stmt, dict):
            util.error("[Input format error] The input node should not be a dictionary: " + str(stmt))
            return

        flattened_node = {}
        dataframe.append(flattened_node)

        flattened_node["operation"] = list(stmt.keys())[0]
        stmt_content = stmt[flattened_node["operation"]]

        self.init_stmt_id(flattened_node, parent_stmt_id)

        if flattened_node["operation"] == "assign_stmt" and "operation" in last_node and last_node["operation"] == "variable_decl":
            last_node["from"] = flattened_node["stmt_id"]

        if not isinstance(stmt_content, dict):
            return

        for mykey, myvalue in stmt_content.items():
            if isinstance(myvalue, list):
                if not self.is_gir_format(myvalue):
                    if myvalue == []:
                        flattened_node[mykey] = None
                    else:
                        flattened_node[mykey] = str(myvalue)
                else:
                    block_id = self.flatten_block(myvalue, flattened_node["stmt_id"], dataframe)
                    flattened_node[mykey] = block_id

            elif isinstance(myvalue, dict):
                util.error_and_quit("[Input format error] Dictionary is not allowed: " + str(myvalue))
                continue
            else:
                flattened_node[mykey] = myvalue

        return flattened_node

    def flatten_block(self, block, parent_stmt_id, dataframe: list):
        """
        扁平化处理代码块：
        1. 创建块开始节点
        2. 递归处理所有子节点
        3. 创建块结束节点
        4. 返回块ID标识
        """
        block_id = self.assign_id()
        dataframe.append({"operation": "block_start", "stmt_id": block_id, "parent_stmt_id": parent_stmt_id})
        last_node = {}
        for child in block:
            last_node = self.flatten_stmt(child, last_node, dataframe, block_id)

        dataframe.append({"operation": "block_end", "stmt_id": block_id, "parent_stmt_id": parent_stmt_id})
        return block_id

    def flatten_gir(self, stmts):
        """
        执行完整GIR扁平化流程：
        1. 遍历所有语句节点
        2. 维护最近处理节点状态
        3. 返回扁平化节点列表
        """
        flattened_nodes = []
        last_node = {}
        for stmt in stmts:
            last_node = self.flatten_stmt(stmt, last_node, flattened_nodes)

        return flattened_nodes

    def flatten(self, stmts):
        """
        GIR扁平化入口方法：
        1. 验证输入格式有效性
        2. 调用flatten_gir执行转换
        3. 返回最终节点ID和扁平结构
        """
        if not self.is_gir_format(stmts):
            util.error_and_quit("The input fromat of GLang IR is not correct.")
            return
        flattened_nodes = self.flatten_gir(stmts)
        return (self.node_id, flattened_nodes)

class GIRParser:
    def __init__(self, options, app_manager, loader, output_path):
        self.options = options
        self.app_manager = app_manager
        self.loader = loader

        self.accumulated_rows = []
        self.output_path = output_path
        self.max_rows = config.MAX_ROWS
        self.count = 0
    def parse(self, file_path, lang_option, lang_table):
        """
        解析源代码生成GIR：
        1. 动态加载语言解析库
        2. 调用Tree-sitter生成AST
        3. 通过语言特定parser生成GIR语句
        """
        if lang_option is None:
            return

        lang = None
        for language in lang_table:
            if language.name == lang_option:
                lang = language
                break

        if not lang:
            util.error_and_quit("Unsupported language: " + self.options.lang)

        lib = cdll.LoadLibrary(lang.so_path)
        lang_function = getattr(lib, "tree_sitter_%s" % lang_option)
        lang_function.restype = c_void_p
        lang_id = lang_function()
        lang_inter = tree_sitter.Language(lang_id)
        tree_sitter_parser = tree_sitter.Parser(lang_inter)

        code = None
        tree = None
        try:
            with open(file_path, 'r') as f:
                code = f.read()
        except:
            util.error("Failed to read file:", file_path)
            return

        if util.is_empty(code):
            return

        if f"{config.DEFAULT_WORKSPACE}/{config.EXTERNS_DIR}" in file_path:
            event = EventData(lang_option, EventKind.MOCK_SOURCE_CODE_READY, code)
            self.app_manager.notify(event)
            code = event.out_data

        event = EventData(lang_option, EventKind.ORIGINAL_SOURCE_CODE_READY, code)
        self.app_manager.notify(event)
        try:
            tree = tree_sitter_parser.parse(bytes(event.out_data, 'utf8'))
        except:
            util.error("Failed to parse AST:", file_path)
            return

        gir_statements = []
        parser = lang.parser(self.options)
        parser.parse(tree.root_node, gir_statements)
        return gir_statements

    def deal_with_file_unit(self, current_node_id, file_unit, lang_table):
        """
        处理单个文件单元：
        1. 确定文件语言类型
        2. 解析生成GIR语句
        3. 执行扁平化转换
        4. 发送事件通知处理结果
        """
        lang_option = determine_lang_by_path(file_unit)

        if self.options.debug:
            util.debug("GIR-Parsing:", file_unit)

        gir_statements = self.parse(file_unit, lang_option, lang_table = lang_table)
        if not gir_statements:
            return (current_node_id, None)
        if self.options.debug and self.options.print_stmts:
            pprint.pprint(gir_statements, compact=True, sort_dicts=False)

        event = EventData(lang_option, EventKind.UNFLATTENED_GIR_LIST_GENERATED, gir_statements)
        self.app_manager.notify(event)
        current_node_id, flatten_nodes = GIRProcessing(current_node_id).flatten(event.out_data)
        if not flatten_nodes:
            return (current_node_id, flatten_nodes)

        event = EventData(lang_option, EventKind.GIR_LIST_GENERATED, flatten_nodes)
        self.app_manager.notify(event)
        if self.options.debug and self.options.print_stmts:
            pprint.pprint(event.out_data, compact=True, sort_dicts=False)

        return (current_node_id, event.out_data)

    @profile
    def add_unit_gir(self, unit_info, flatten_nodes):
        """
        存储处理后的GIR数据：
        1. 为节点添加单元ID标识
        2. 调用加载器持久化存储
        """
        if is_empty(flatten_nodes):
            return

        unit_id = unit_info.module_id
        for node in flatten_nodes:
            node["unit_id"] = unit_id
        self.loader.save_unit_gir(unit_id, flatten_nodes)

    def export(self):
        self.loader.export_gir()

class LangAnalysis:
    def __init__(self, lian):
        self.options = lian.options
        self.app_manager: AppManager = lian.app_manager
        self.loader: Loader = lian.loader
        self.lang_table = lian.lang_table

    def init_start_stmt_id(self):
        """
        初始化语句ID计数器：
        1. 根据符号表长度计算初始偏移
        2. 保证ID起始值对齐到10的倍数
        """
        symbol_table = self.loader.load_module_symbol_table()
        result = len(symbol_table)
        return self.adjust_node_id(result)

    def adjust_node_id(self, node_id):
        """
        调整节点ID间距：
        1. 按配置的最小ID间隔调整数值
        保证ID连续性和可读性
        """
        # remainder = node_id % 10
        # if remainder != 0:
        #     node_id += (10 - remainder)
        node_id += config.MIN_ID_INTERVAL
        remainder = node_id % 10
        if remainder != 0:
            node_id += (10 - remainder)
        return node_id

    def run(self):
        """
        语言分析主流程：
        1. 初始化GIR解析器
        2. 遍历所有代码单元
        3. 执行解析和扁平化处理
        4. 导出最终分析结果
        """
        if self.options.debug:
            util.debug("\n\t###########  # Language Parsing #  ###########")

        gir_parser = GIRParser(
            self.options,
            self.app_manager,
            self.loader,
            os.path.join(self.options.workspace, config.GIR_DIR)
        )
        all_units = self.loader.load_all_unit_info()
        #all_units = [unit for unit in all_units if unit.lang !='c' or (unit.lang == 'c' and unit.unit_ext == '.i')]

        if self.options.benchmark:
            all_units = all_units.slice(0, config.MAX_BENCHMARK_TARGET)
        if len(all_units) == 0:
            util.error_and_quit("No files found for analysis.")

        current_node_id = self.init_start_stmt_id()
        for unit_info in all_units:
            # if row.symbol_type == constants.SymbolKind.UNIT_SYMBOL and row.unit_ext in extensions:
            current_node_id, gir = gir_parser.deal_with_file_unit(
                current_node_id, unit_info.unit_path, lang_table = self.lang_table
            )
            gir_parser.add_unit_gir(unit_info, gir)
            current_node_id = self.adjust_node_id(current_node_id)
            # if self.options.debug:
            #     gir_parser.export()
        gir_parser.export()

        self.loader.export()