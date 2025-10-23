#!/usr/bin/env python3

import os,sys
from types import SimpleNamespace
import config1 as config

sys.path.extend([config.LIAN_DIR, config.TAINT_DIR])

from lian.interfaces.main import Lian
from lian.util.loader import Loader
from lian.util import util
from lian.semantic.semantic_structs import (
    APath,
    SimpleWorkList,
    State,
    Symbol,
    ComputeFrameStack,
    SymbolStateSpace,
)

from taint.taint_structs import PropagationResult, StmtTaintStatus, TaintEnv, MethodTaintFrame, TaintStateManager
from taint.propagation import TaintPropagationInMethod
from taint.global_propagation import GlobalPropagation


class TaintAnalysis:
    def __init__(self):
        self.lian = None
        self.loader: Loader = None
        self.phase = 2
        self.symbol_state_space_p3 = None

    def exist_source_sink(self, method_id):

        return False

    def exist_tag_in_method(self, method_id):
        all_used_symbols = self.loader.load_all_used_symbols(method_id)
        for symbol in all_used_symbols:
            if symbol.symbol_id in self.env:
                return True

        all_used_states = self.loader.load_all_used_states(method_id)
        for state in all_used_states:
            if state.state_id in self.env:
                return True

    def should_inspect_method_body(self, frame):
        return True

    def init_taint_frame(self, method_id, taint_env, frame_stack = None, call_graph = None, taint_state_manager = None, current_call_site = None, previous_call_site = None):
        if not taint_state_manager:
            taint_state_manager = TaintStateManager()
        frame = MethodTaintFrame(method_id=method_id, frame_stack=frame_stack, env=taint_env)
        frame.lian = self.lian
        frame.taint_state_manager = taint_state_manager
        method_decl, parameter_decls, method_body = self.loader.get_splitted_method_gir(method_id)
        frame.stmt_id_to_stmt[method_id] = method_decl
        if util.is_available(parameter_decls):
            for row in parameter_decls:
                frame.stmt_id_to_stmt[row.stmt_id] = row
                frame.stmt_counters[row.stmt_id] = 0
        if util.is_available(method_body):
            for row in method_body:
                frame.stmt_id_to_stmt[row.stmt_id] = row
                frame.stmt_counters[row.stmt_id] = 0

        frame.cfg = self.loader.get_method_cfg(method_id)
        if util.is_empty(frame.cfg):
            return

        frame.stmt_worklist = SimpleWorkList(graph = frame.cfg)
        frame.stmt_worklist.add(util.find_cfg_first_nodes(frame.cfg))
        # frame.stmts_with_symbol_update.add(util.find_cfg_first_nodes(frame.cfg))
        if call_graph:
            callee_ids = util.graph_successors(call_graph, method_id)
            # print(list(callee_ids))
            for u, v, key, attrs in call_graph.edges(keys=True, data=True):
                print(f"Edge: {u} -> {v}, Key: {key}, Attributes: {attrs}")
            edges = {}
            for callee in callee_ids:
                # 获取从 node 到 succ 的所有边（处理多重边）
                edges_data = call_graph.get_edge_data(method_id, callee)
                print(edges_data)
                for key in edges_data:
                    value = edges_data[key]
                    stmt_id = value['weight']
                    if stmt_id not in edges:
                        edges[stmt_id] = []
                    edges[stmt_id].append(callee)
            frame.stmt_id_to_callees = edges
            print(frame.stmt_id_to_callees)
        # print(method_id)
        # print(frame.stmt_id_to_callees)
        # print(8888888888888888888888)
        # 给个机会其他人加callee

        # 初始化state_id_to_access_path

        #frame.stmt_worklist.add(frame.cfg.nodes())

        # avoid changing the content of the loader
        frame.current_call_site = current_call_site
        frame.previous_call_site = previous_call_site
        if self.phase == 2:
            frame.stmt_id_to_status = self.loader.get_stmt_status_p2(method_id)
            frame.symbol_state_space = self.loader.get_symbol_state_space_p2(method_id)
            frame.symbol_graph = self.loader.get_method_symbol_graph_p2(method_id)
            frame.propagation = TaintPropagationInMethod(frame)
        elif self.phase == 3:
            frame.stmt_id_to_status = self.loader.get_stmt_status_p3(frame.previous_call_site)
            frame.symbol_state_space = self.loader.get_symbol_state_space_p3(0)
            frame.propagation = GlobalPropagation(frame)
            # frame.symbol_graph = self.loader.load_method_symbol_graph_p3(method_id)
        # 初始化state_id_to_access_path
        frame.state_id_to_access_path = {}
        for item in frame.symbol_state_space:
            if isinstance(item, Symbol) or item.state_id == -1:
                continue
            frame.state_id_to_access_path[item.state_id] = item.access_path

        return frame

    def apply_method_summary(self, frame):
        pass

    def obtain_state_id_from_state_index(self, state_index, frame):
        state = frame.symbol_state_space.get(state_index)
        if not isinstance(state, State):
            return -1
        return state.state_id

    def collect_taint_by_state_index(self, state_index, frame):
        """ 递归收集某个state及其所有子states的污点标签，并将这些标签通过按位或操作合并后返回。"""
        tag = config.NO_TAINT
        taint_env:TaintEnv = frame.taint_env
        worklist = [state_index]
        visited = set()
        while worklist:
            state_index = worklist.pop()
            if state_index in visited:
                continue
            visited.add(state_index)

            state: State = frame.symbol_state_space[state_index]
            if not isinstance(state, State):
                continue
            if taint_env.get_state_tag(state.state_id):
                tag |= taint_env.get_state_tag(state.state_id)
            fields_state = set()
            for s in state.fields.values():
                fields_state |= s
            all_internal_states = fields_state | state.tangping_elements
            for each_element in state.array:
                all_internal_states.update(state.array[each_element])
            for each_index in all_internal_states:
                worklist.append(each_index)

        return tag

    def prepare_in_taint(self, stmt_id, frame: MethodTaintFrame):
        """
        比较所有symbol在当前status中的old_in_taint和current_in_taint是否一样
        不一样则更新, 并返回True
        """
        is_changed_flag = False
        if not frame.stmt_id_to_status[stmt_id]:
            return False
        status = frame.stmt_id_to_status[stmt_id]
        if stmt_id not in frame.stmt_id_to_taint_status:
            frame.stmt_id_to_taint_status[stmt_id] = StmtTaintStatus(stmt_id=stmt_id)
        taint_status = frame.stmt_id_to_taint_status[stmt_id]
        taint_env = frame.taint_env

        old_taint = taint_status.in_taint
        for symbol_index in status.used_symbols + status.implicitly_used_symbols:
            symbol = frame.symbol_state_space[symbol_index]
            if not isinstance(symbol, Symbol):
                continue
            symbol_id = symbol.symbol_id
            # 收集该Symbol的旧taint
            old = old_taint.get(symbol_id, config.NO_TAINT)
            current = taint_env.get_symbol_tag(symbol_id)
            # 收集该Symbol的states的总taint
            for each_state in symbol.states:
                current |= self.collect_taint_by_state_index(each_state, frame)
            # 比较该symbol的old_in_taint和current_in_taint是否一样，不一样则更新
            if old != current:
                taint_status.in_taint[symbol_id] = current
                is_changed_flag = True
        return is_changed_flag

    def process_out_taint(self, stmt_id, frame:MethodTaintFrame, old_out_taint, new_out_taint):
        """更新taint_env的states_to_bv和symbols_to_bv字典"""
        # out_taint是个字典{symbol_id: tag_bv}
        if old_out_taint == new_out_taint:
            return False
        taint_env:TaintEnv = frame.taint_env
        stmt_status = frame.stmt_id_to_status[stmt_id]
        all_symbols_indexes = stmt_status.used_symbols + stmt_status.implicitly_used_symbols + stmt_status.implicitly_defined_symbols + [stmt_status.defined_symbol]

        # 构建symbol_id->symbols的映射
        symbol_id_to_symbols = {}
        for symbol_index in all_symbols_indexes:
            if symbol_index < 0:
                continue

            symbol  = frame.symbol_state_space[symbol_index]
            if isinstance(symbol, Symbol):
                symbol_id = symbol.symbol_id
                if symbol_id not in symbol_id_to_symbols:
                    symbol_id_to_symbols[symbol_id] = [symbol]
                else:
                    symbol_id_to_symbols[symbol_id].append(symbol)

        for symbol_id, tag_bv in new_out_taint.items():
            if symbol_id not in old_out_taint or old_out_taint[symbol_id] != tag_bv:
                # 更新taint_env.symbols_to_bv
                taint_env.set_symbols_tag([symbol_id], tag_bv)
                # 更新taint_env.states_to_bv
                if symbol_id in symbol_id_to_symbols:
                    symbols = symbol_id_to_symbols[symbol_id]
                    states = set()
                    for symbol in symbols:
                        states.update(symbol.states)
                    state_ids = set()
                    for state_index in states:
                        if state:= frame.symbol_state_space[state_index] :
                            if isinstance(state, State):
                                state_ids.add(state.state_id)
                    taint_env.set_states_tag(state_ids, tag_bv)

        # out有变化
        print(f"state taint_env: {taint_env.states_to_bv}")
        print(f"symbol taint_env: {taint_env.symbols_to_bv}")
        return True

    # def inspect_method_body(self, frame: MethodTaintFrame):
    #     """进入到一个方法内部，并进行污点分析"""
    #     pass

    def analyze_method(self, frame, ):
        """对单个方法进行分析"""
        is_done_flag = True
        # 判断是否需要深入到方法内部执行
        print(f"========= analyzing method: {frame.method_id} ============")
        if self.should_inspect_method_body(frame):
            # 收集函数参数的tag
            taint_propagation = frame.propagation
            taint_propagation.entry_method(frame)
            # print(frame.stmt_worklist)
            while len(frame.stmt_worklist) != 0:
                #1. prepare in taints: symbols, states <- frame.taint_env.symbols/states
                #2. taint propagation according to stmt operations
                #3. add more stmts to worklist
                stmt_id = frame.stmt_worklist.pop()
                print(f"========= analyzing stmt_id: {stmt_id} ============")
                # stmt = frame.stmt_id_to_stmt[stmt_id]
                if stmt_id < 0:
                    continue

                if frame.stmt_counters[stmt_id] > config.MAX_STMT_TAINT_ANALYSIS_COUNT:
                    continue
                frame.stmt_worklist.add(util.graph_successors(frame.cfg, stmt_id))

                is_changed_flag:bool = self.prepare_in_taint(stmt_id, frame)
                if not is_changed_flag and frame.stmt_counters[stmt_id] > 0:
                    continue

                taint_status = frame.stmt_id_to_taint_status[stmt_id]
                old_out_taint = taint_status.out_taint.copy()
                # 根据语句类型分发不同的propagation_handler
                # 当call的时候，进去分析，暂停当前函数分析
                # todo 遇到call进入函数前，如何把参数的in_taint送进去，出函数后如何把返回值的out_taint送回
                result = taint_propagation.analyze_stmt(stmt_id, taint_status)
                print("in method")
                if isinstance(result, PropagationResult) and result.interruption_flag:
                    return result
                new_out_taint = taint_status.out_taint
                out_changed_flag:bool = self.process_out_taint(stmt_id, frame, old_out_taint, new_out_taint)
                # if out_changed_flag:

                frame.stmt_counters[stmt_id] += 1
                # return is_done_flag
        self.apply_method_summary(frame)
        return is_done_flag

    def analyze_call_graph(self, call_graph):
        if self.lian.options.debug:
            util.debug()
            util.debug(
                "\n\n\t" + "/" * 60 + "\n" +
                "\t////" + " " * 17 + "Taint Analysis p2" + " " * 18 + "////\n"
                "\t" + "/" * 60 + "\n"
            )
        root_nodes = util.find_graph_nodes_with_zero_in_degree(call_graph.graph)
        # 以一条完整函数调用为一次污点分析的分析边界
        for first_node in root_nodes:
            taint_env = TaintEnv()
            method_counter = {}
            frame_stack = ComputeFrameStack()

            first_frame = self.init_taint_frame(first_node, taint_env, frame_stack, call_graph.graph)
            frame_stack.add(first_frame) #  used for collecting the final results

            while frame_stack:

                frame = frame_stack.peek()
                # print(frame.content_to_be_analyzed)
                # print(666666666666666666666666)
                if len(frame_stack) > 1:
                    caller_frame = frame_stack[-2]
                method_id = frame.method_id

                print(f"analyzing method {method_id}")
                if method_id not in method_counter:
                    method_counter[method_id] = 0
                method_counter[method_id] += 1
                print(f"method {method_id} call count: {method_counter[method_id]}")
                if method_counter[method_id] > config.MAX_METHOD_CALL_COUNT:
                    frame_stack.pop()
                    continue

                if frame.content_to_be_analyzed:
                    children_done_flag = True
                    for key in frame.content_to_be_analyzed:
                        value = frame.content_to_be_analyzed[key]
                        if not value:
                            frame.content_to_be_analyzed[key] = True
                            children_done_flag = False
                            #在这里准备好arg_to_param的映射
                            param_list = self.loader.get_parameter_mapping_p2(key)
                            taint_state_manager = TaintStateManager()
                            taint_state_manager.sync_arg_to_param(param_list, frame.taint_state_manager)
                            taint_env.sync_arg_to_param(param_list)
                            callee_frame = self.init_taint_frame(key[2], taint_env, frame_stack, call_graph.graph, taint_state_manager)
                            frame_stack.push(callee_frame)
                            break
                    if not children_done_flag:
                        continue

                # 分析该函数，函数内遇到call时，中断分析，进入该call函数
                result = self.analyze_method(frame)
                # push stack
                if isinstance(result, PropagationResult) and result.interruption_flag:
                    # print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
                    found_callee = False
                    for callee_id in frame.stmt_id_to_callees[result.stmt_id]:
                        key = (method_id, result.stmt_id, callee_id)
                        frame.content_to_be_analyzed[key] = False
                        found_callee = True

                    if found_callee:
                        continue

                if frame.return_tag:
                    if caller_frame.callee_return:
                        caller_frame.callee_return |= frame.return_tag
                    else:
                        caller_frame.callee_return = frame.return_tag
                frame_stack.pop()
# call_path的method的分析顺序是什么？

    def analyze_call_paths(self, call_paths):
        if self.lian.options.debug:
            util.debug()
            util.debug(
                "\n\n\t" + "/" * 60 + "\n" +
                "\t////" + " " * 17 + "Taint Analysis p3" + " " * 18 + "////\n"
                "\t" + "/" * 60 + "\n"
            )
        self.phase = 3
        taint_env = TaintEnv()
        taint_state_manager = TaintStateManager()
        call_paths_list = list(call_paths)
        call_paths_list += call_paths_list

        for each_path in call_paths_list:
            frame_stack = ComputeFrameStack()
            path:tuple = each_path.path
            frame = self.init_taint_frame(path[0], taint_env, current_call_site = path[0:3], previous_call_site = (-1, -1, path[0]), taint_state_manager = taint_state_manager)
            frame.current_call_site = path[0:3]
            frame_stack.add(frame) #  used for collecting the final results
            while frame_stack:
                frame = frame_stack.peek()
                if frame.content_to_be_analyzed:
                    value = frame.content_to_be_analyzed[frame.current_call_site]
                    if  value:
                        frame.content_to_be_analyzed[frame.current_call_site] = False
                        callee_frame = self.init_taint_frame(path[0], taint_env, frame_stack, current_call_site = path[0:3], previous_call_site = value, taint_state_manager = taint_state_manager)
                        # callee_frame.current_call_site = path[0:3]
                        frame_stack.push(callee_frame)
                        continue

                result = self.analyze_method(frame)

                if isinstance(result, PropagationResult) and result.interruption_flag:
                    frame.content_to_be_analyzed[frame.current_call_site] = path[0 : 3]
                    path = path[2:]
                    continue

                frame_stack.pop()

    def run(self):
        #self.lian = Lian().set_options(workspace = config.DEFAULT_WORKSPACE).run()
        self.lian = Lian().run()
        self.loader = self.lian.loader

        if self.lian.options.debug:
            util.debug()
            util.debug(
                "\n\n\t" + "/" * 60 + "\n" +
                "\t////" + " " * 20 + "Taint Analysis" + " " * 18 + "////\n"
                "\t" + "/" * 60 + "\n"
            )

        # 1. load data from loader (phase2, phase3)
        call_graph_p2 = self.loader.get_prelim_call_graph()
        call_paths_p3 = self.loader.get_global_call_path()
        print("call_paths_p2: ", list(call_graph_p2.graph.edges))
        # 2. traverse call_graph
        self.analyze_call_graph(call_graph_p2)

        # 3. traverse call_paths
        self.analyze_call_paths(call_paths_p3)

    def run_as_app(self, lian):
        self.lian = lian
        self.loader = self.lian.loader

        if self.lian.options.debug:
            util.debug()
            util.debug(
                "\n\n\t" + "/" * 60 + "\n" +
                "\t////" + " " * 20 + "Taint Analysis" + " " * 18 + "////\n"
                "\t" + "/" * 60 + "\n"
            )

        # 1. load data from loader (phase2, phase3)
        call_graph_p2 = self.loader.get_prelim_call_graph()
        call_paths_p3 = self.loader.get_global_call_path()
        print("call_paths_p2: ", list(call_graph_p2.graph.edges))
        # 2. traverse call_graph
        # self.analyze_call_graph(call_graph_p2)
        self.analyze_call_paths(call_paths_p3)
def main():
    TaintAnalysis().run()

if __name__ == "__main__":
    main()
