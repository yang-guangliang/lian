#!/usr/bin/env python3

import os
import ast
from collections import namedtuple

import networkx as nx
import pprint
import numpy
from bisect import insort

import pandas as pd

from lian.util.data_model import DataModel
from lian.config import schema
from lian.util import util
from lian.config import config
from lian.config.constants import (
    IMPORT_GRAPH_EDGE_KIND,
    SYMBOL_OR_STATE,
    LIAN_SYMBOL_KIND
)
from lian.semantic.semantic_structs import (
    BasicGraph,
    State,
    StateDefNode,
    Symbol,
    ControlFlowGraph,
    SymbolDefNode,
    SymbolGraph,
    StmtStatus,
    SymbolStateSpace,
    BitVectorManager,
    CallGraph,
    UnitSymbolDeclSummary,
    MethodDefUseSummary,
    MethodSummaryTemplate,
    MethodInternalCallee,
    SimplyGroupedMethodTypes,
    ParameterMapping,
    AccessPoint,
    IndexMapInSummary,
    MethodSummaryInstance,
    APath,
    SymbolNodeInImportGraph
)

class ModuleSymbolsLoader:
    def __init__(self, options, path):
        self.options = options
        self.path = path
        self.module_symbol_table = None
        #self.cache = util.LRUCache(capacity = config.TMP_UNIT_INFO_CACHE_CAPABILITY)
        self.init_self()

    def init_self(self):
        self.module_id_to_module_info = {}
        self.unit_id_to_lang = {}
        self.module_name_to_module_ids = {}
        self.module_id_to_children_ids = {}
        self.module_unit_ids = set()
        self.all_module_ids = set()
        self.module_dir_ids = set()
        self.unit_path_to_id = {}
        self.unit_id_to_path = {}

    def save(self, module_symbol_results):
        #print(module_symbol_results)
        self.module_symbol_table = DataModel(module_symbol_results)
        self._do_cache()

    def restore(self):
        self.module_symbol_table = DataModel().load(self.path)
        self._do_cache()

    def _do_cache(self):
        self.init_self()

        for row in self.module_symbol_table:
            module_id = row.module_id

            if row.symbol_type == LIAN_SYMBOL_KIND.UNIT_SYMBOL:
                self.module_unit_ids.add(module_id)

            # cache all module ids
            self.all_module_ids.add(module_id)

            # cache all lines
            self.module_id_to_module_info[module_id] = row

            # cache module_name_to_module_ids
            if row.symbol_name not in self.module_name_to_module_ids:
                self.module_name_to_module_ids[row.symbol_name] = set()
            self.module_name_to_module_ids[row.symbol_name].add(module_id)

            # cache unit_id_to_lang
            if util.is_available(row.lang):
                self.unit_id_to_lang[module_id] = row.lang

            # cache module_id_to_children_ids
            if row.parent_module_id not in self.module_id_to_children_ids:
                self.module_id_to_children_ids[row.parent_module_id] = set()
            self.module_id_to_children_ids[row.parent_module_id].add(module_id)

            # cache unit_path_to_id and unit_id_to_path
            if util.is_available(row.unit_path):
                self.unit_path_to_id[row.unit_path] = module_id
                self.unit_id_to_path[module_id] = row.unit_path

        self.module_dir_ids = self.all_module_ids - self.module_unit_ids

    def export(self):
        if util.is_available(self.module_symbol_table):
            self.module_symbol_table.save(self.path)

    def is_module_id(self, unit_id):
        return unit_id in self.all_module_ids

    def is_unit_id(self, unit_id):
        return unit_id in self.module_unit_ids

    def is_module_dir_id(self, unit_id):
        return unit_id in self.module_dir_ids

    def load_all_module_ids(self):
        return self.all_module_ids

    def load_module_symbol_table(self):
        return self.module_symbol_table

    def load_unit_lang_name(self, unit_id):
        return self.unit_id_to_lang.get(unit_id, "unknown")

    def convert_module_id_to_module_info(self, unit_id):
        return self.module_id_to_module_info.get(unit_id, None)

    def convert_module_id_to_child_ids(self, module_id):
        return self.module_id_to_children_ids.get(module_id, set())

    def load_all_unit_info(self):
        if len(self.module_symbol_table) == 0:
            return []

        all_units = self.module_symbol_table.query(self.module_symbol_table.symbol_type == LIAN_SYMBOL_KIND.UNIT_SYMBOL)
        if len(all_units) == 0:
            return []

        all_units = all_units.query(all_units.unit_ext.isin(self.options.lang_extensions))
        if len(all_units) == 0:
            return []

        return all_units

    def convert_unit_path_to_unit_id(self, unit_path):
        for path in  self.unit_path_to_id:
            if path.endswith(unit_path):
                return self.unit_path_to_id[path]

    def convert_unit_id_to_unit_path(self, unit_id):
        return self.unit_id_to_path.get(unit_id, None)

class GeneralLoader:
    def __init__(self, options, item_schema, bundle_path_summary, item_cache_capacity, bundle_cache_capacity):
        # use this to find the path of the corresponding bundle
        self.options = options
        self.item_schema = item_schema
        self.bundle_path_summary = bundle_path_summary
        self.loader_indexing_path = f"{self.bundle_path_summary}.{config.LOADER_INDEXING_PATH}"

        # caching cfg of method_a/symbol_graph of method_b/
        self.item_cache = util.LRUCache(item_cache_capacity)
        # caching dead cfg_bundle/symbol_graph_bundle...
        self.bundle_cache = util.LRUCache(bundle_cache_capacity)
        # active bundle of item1, item2 ...
        self.active_bundle = {}
        self.active_bundle_length = 0
        self.item_id_to_bundle_id = {}
        self.bundle_count = 0

    def query_flattened_item_when_loading(self, item_id, bundle_data):
        return None

    def unflatten_item_dataframe_when_loading(self, _id, item_df):
        return item_df

    def flatten_item_when_saving(self, _id, item_content):
        return None

    def convert_active_bundle_to_dataframe(self):
        accumulated_rows = []
        for key in sorted(self.active_bundle.keys()):
            value = self.active_bundle[key]
            accumulated_rows.extend(value[1])

        return DataModel(accumulated_rows, columns=self.item_schema)

    def new_bundle_id(self):
        result = self.bundle_count
        self.bundle_count += 1
        return result

    def load(self, _id):
        if self.item_cache.contain(_id):
            return self.item_cache.get(_id)

        bundle_id = self.item_id_to_bundle_id.get(_id, None)
        if bundle_id is None:
            return None

        if bundle_id == -1:
            # the item should be in the active bundle at this moment
            result = self.active_bundle.get(_id, None)
            if result is not None:
                self.item_cache.put(_id, result[0])
                return result[0]
            return None

        # read this item from existing bundles
        bundle_data = None
        if self.bundle_cache.contain(bundle_id):
            bundle_data = self.bundle_cache.get(bundle_id)
        else:
            bundle_path = f"{self.bundle_path_summary}.bundle{bundle_id}"
            bundle_data = DataModel().load(bundle_path)
            self.bundle_cache.put(bundle_id, bundle_data)

        item_df = self.query_flattened_item_when_loading(_id, bundle_data)
        formatted_item = self.unflatten_item_dataframe_when_loading(_id, item_df)
        self.item_cache.put(_id, formatted_item)
        return formatted_item

    def load_all(self):
        all_results = {}
        for item_id in self.item_id_to_bundle_id:
            all_results[item_id] = self.load(item_id)
        return all_results

    def save(self, _id, item_content):
        self.item_cache.put(_id, item_content)
        flattened_item = self.flatten_item_when_saving(_id, item_content)
        self.active_bundle[_id] = (item_content, flattened_item)
        self.item_id_to_bundle_id[_id] = -1
        self.active_bundle_length += len(flattened_item)
        if self.active_bundle_length > config.MAX_ROWS:
            self.export()
        return item_content

    def export(self):
        if self.active_bundle_length > 0:
            new_bundle_id = self.new_bundle_id()
            bundle_df = self.convert_active_bundle_to_dataframe()
            bundle_path = f"{self.bundle_path_summary}.bundle{new_bundle_id}"
            bundle_df.save(bundle_path)

            self.bundle_cache.put(new_bundle_id, bundle_df)
            for item_id, bundle_id in self.item_id_to_bundle_id.items():
                if bundle_id == -1:
                    self.item_id_to_bundle_id[item_id] = new_bundle_id

            self.active_bundle = {}
            self.active_bundle_length = 0

    def export_indexing(self):
        results = []
        for (key, value) in self.item_id_to_bundle_id.items():
            results.append([key, value])

        DataModel(results, columns = schema.loader_indexing_schema).save(self.loader_indexing_path)

    def restore_indexing(self):
        if not os.path.exists(self.loader_indexing_path):
            return

        df = DataModel().load(self.loader_indexing_path)
        for row in df:
            data = row.raw_data()
            # TODO
            #  TEMPORARY FIX, EXPECTED TO BE IMPROVED LATER
            #  This is due to pandas feather format saving tuples but loading numpy.ndarray
            try:
                self.item_id_to_bundle_id[data[0]] = data[1]
            except TypeError:
                key_tuple = tuple(data[0])
                self.item_id_to_bundle_id[key_tuple] = data[1]


class UnitLevelLoader(GeneralLoader):
    def query_flattened_item_when_loading(self, unit_id, bundle_data):
        flattened_item = bundle_data.query(sorted(bundle_data.unit_id.bundle_search(unit_id)))
        return flattened_item

    def convert_content_to_dict_list(self, unit_id, item_content):
        results = []
        #print("@convert_content_to_dict_list", item_content)
        for item in item_content:
            to_dict_result = item.to_dict()
            if not hasattr(to_dict_result, "unit_id"):
                to_dict_result["unit_id"] = unit_id
            #print("to_dict_result", to_dict_result)
            results.append(to_dict_result)
        return results

    def save(self, unit_id, item_content):
        # convert item_content to dataframe
        flattened_item = self.convert_content_to_dict_list(unit_id, item_content)
        item_df = DataModel(flattened_item)
        self.item_cache.put(unit_id, item_df)

        self.active_bundle[unit_id] = (item_df, flattened_item)
        self.item_id_to_bundle_id[unit_id] = -1
        self.active_bundle_length += len(flattened_item)

        if self.active_bundle_length > config.MAX_ROWS:
            self.export()

        return item_df

class UnitGIRLoader(UnitLevelLoader):
    def save(self, unit_id, flattened_item):
        # print("flattened_item", flattened_item)
        # convert item_content to dataframe
        item_df = DataModel(flattened_item)
        self.active_bundle[unit_id] = (item_df, flattened_item)
        self.item_id_to_bundle_id[unit_id] = -1
        self.active_bundle_length += len(flattened_item)

        if self.active_bundle_length > config.MAX_ROWS:
            self.export()

        return item_df

    def export(self):
        if self.active_bundle_length > 0:
            new_bundle_id = self.new_bundle_id()
            bundle_df = self.convert_active_bundle_to_dataframe()
            bundle_path = f"{self.bundle_path_summary}.bundle{new_bundle_id}"
            bundle_df.save(bundle_path)

            for item_id, bundle_id in self.item_id_to_bundle_id.items():
                if bundle_id == -1:
                    self.item_id_to_bundle_id[item_id] = new_bundle_id

            self.active_bundle = {}
            self.active_bundle_length = 0

class ScopeHierarchyLoader(UnitLevelLoader):
    pass

class UnitIDToExportSymbolsLoader(UnitLevelLoader):
    pass

class ClassIDToMethodInfoLoader(UnitLevelLoader):
    pass

class ClassIDToMembersLoader(UnitLevelLoader):
    def save_all(self, class_id_to_members:dict):
        for class_id in class_id_to_members:
            self.save(class_id, class_id_to_members[class_id])

    def save(self, class_id, class_members_dict:dict):
        class_members_series = pd.Series(class_members_dict, dtype = object)
        class_members_df = DataModel(class_members_series, columns=["members"])
        self.item_cache.put(class_id, class_members_df)

        self.active_bundle[class_id] = (class_members_df, class_members_dict)
        self.item_id_to_bundle_id[class_id] = -1
        self.active_bundle_length += len(class_members_dict)

        if self.active_bundle_length > config.MAX_ROWS:
            self.export()

        return class_members_df


class SymbolNameToScopeIDsLoader(GeneralLoader):
    def query_flattened_item_when_loading(self, unit_id, bundle_data):
        flattened_item = bundle_data.query(bundle_data.unit_id.bundle_search(unit_id))
        return flattened_item

    def flatten_item_when_saving(self, unit_id, symbol_name_to_scope_ids):
        results = []
        for symbol_name in symbol_name_to_scope_ids:
            results.append({
                "unit_id": unit_id,
                "symbol_name": symbol_name,
                "scope_ids": list(symbol_name_to_scope_ids[symbol_name])
            })
        return results

    def unflatten_item_dataframe_when_loading(self, _id, item_df):
        symbol_name_to_scope_ids = {}
        for row in item_df:
            symbol_name_to_scope_ids[row.symbol_name] = set(row.scope_ids)
        return symbol_name_to_scope_ids

class ScopeIDToSymbolInfoLoader(GeneralLoader):
    def query_flattened_item_when_loading(self, unit_id, bundle_data):
        flattened_item = bundle_data.query(bundle_data.unit_id.bundle_search(unit_id))
        return flattened_item

    def flatten_item_when_saving(self, unit_id, scope_id_to_symbol_info):
        results = []
        for scope_id in scope_id_to_symbol_info:
            symbol_names = []
            symbol_stmt_ids = []
            value = scope_id_to_symbol_info[scope_id]
            for name in sorted(value.keys()):
                symbol_names.append(name)
                symbol_stmt_ids.append(value[name])

            results.append({
                "unit_id": unit_id,
                "scope_id": scope_id,
                "symbol_names": symbol_names,
                "symbol_stmt_ids": symbol_stmt_ids
            })

        return results

    def unflatten_item_dataframe_when_loading(self, _id, item_df):
        scope_id_to_symbol_info = {}
        for row in item_df:
            results = {}
            for index, name in enumerate(row.symbol_names):
                results[name] = row.symbol_stmt_ids[index]
            scope_id_to_symbol_info[row.scope_id] = results
        return scope_id_to_symbol_info

class ScopeIDToAvailableScopeIDsLoader(GeneralLoader):
    def query_flattened_item_when_loading(self, unit_id, bundle_data):
        flattened_item = bundle_data.query(bundle_data.unit_id.bundle_search(unit_id))
        return flattened_item

    def flatten_item_when_saving(self, unit_id, scope_id_to_available_scope_ids):
        results = []
        for scope_id in scope_id_to_available_scope_ids:
            results.append({
                "unit_id": unit_id,
                "scope_id": scope_id,
                "available_scope_ids": list(scope_id_to_available_scope_ids[scope_id])
            })
        return results

    def unflatten_item_dataframe_when_loading(self, _id, item_df):
        scope_id_to_available_scope_ids = {}
        for row in item_df:
            scope_id_to_available_scope_ids[row.scope_id] = set(row.available_scope_ids)
        return scope_id_to_available_scope_ids

class UnitSymbolDeclSummaryLoader:
    def __init__(self, symbol_name_to_scope_ids_loader, scope_id_to_symbol_info_loader, scope_id_to_available_scope_ids_loader):
        self.symbol_name_to_scope_ids_loader = symbol_name_to_scope_ids_loader
        self.scope_id_to_symbol_info_loader = scope_id_to_symbol_info_loader
        self.scope_id_to_available_scope_ids_loader = scope_id_to_available_scope_ids_loader

    def load(self, unit_id):
        return UnitSymbolDeclSummary(
            unit_id,
            self.symbol_name_to_scope_ids_loader.load(unit_id),
            self.scope_id_to_symbol_info_loader.load(unit_id),
            self.scope_id_to_available_scope_ids_loader.load(unit_id)
        )

    def save(self, unit_id, summary: UnitSymbolDeclSummary):
        self.symbol_name_to_scope_ids_loader.save(unit_id, summary.symbol_name_to_scope_ids)
        self.scope_id_to_symbol_info_loader.save(unit_id, summary.scope_id_to_symbol_info)
        self.scope_id_to_available_scope_ids_loader.save(unit_id, summary.scope_id_to_available_scope_ids)

    def export(self):
        self.symbol_name_to_scope_ids_loader.export()
        self.scope_id_to_symbol_info_loader.export()
        self.scope_id_to_available_scope_ids_loader.export()

class CallStmtIDToCallFormatInfoLoader:
    def __init__(self, path):
        self.call_stmt_id_to_call_format_info = {}
        self.path = path

    def load_all_call_stmt_id_to_call_format_info(self):
        return self.call_stmt_id_to_call_format_info

    def save(self, call_stmt_id, call_format_info):
        self.call_stmt_id_to_call_format_info[call_stmt_id] = call_format_info

    def load(self, call_stmt_id):
        return self.call_stmt_id_to_call_format_info.get(call_stmt_id, None)

    def export(self):
        if len(self.call_stmt_id_to_call_format_info) == 0:
            return

        results = []
        for (stmt_id, call_format_info) in self.call_stmt_id_to_call_format_info.items():
            results.append(call_format_info)
        DataModel(results).save(self.path)

    def restore(self):
        df = DataModel().load(self.path)
        for row in df:
            self.call_stmt_id_to_call_format_info[row.stmt_id] = row

class MethodIDToMethodDeclFormat:
    def __init__(self, path):
        self.method_id_to_method_decl_format = {}
        self.path = path

    def save(self, method_id, method_decl_format):
        self.method_id_to_method_decl_format[method_id] = method_decl_format

    def load(self, method_id):
        return self.method_id_to_method_decl_format.get(method_id, None)

    def export(self):
        if len(self.method_id_to_method_decl_format) == 0:
            return

        results = []
        for (method_id, method_decl_format) in self.method_id_to_method_decl_format.items():
            results.append(method_decl_format)
        DataModel(results).save(self.path)

    def restore(self):
        df = DataModel().load(self.path)
        for row in df:
            self.method_id_to_method_decl_format[row.method_id] = row

class UnitIDToStmtIDLoader:
    def __init__(self, path):
        self.unit_id_to_stmt_ids = {}
        self.stmt_id_to_unit_id = {}
        self.path = path

    def save(self, unit_id, all_ids):
        if len(all_ids) == 0:
            return

        self.unit_id_to_stmt_ids[unit_id] = all_ids
        for stmt_id in all_ids:
            self.stmt_id_to_unit_id[stmt_id] = unit_id

    def load(self, stmt_id):
        return self.stmt_id_to_unit_id.get(stmt_id, -1)

    def load_one_to_many(self, unit_id):
        return self.unit_id_to_stmt_ids.get(unit_id, [])

    def load_all_stmt_ids(self):
        return self.stmt_id_to_unit_id.keys()

    def load_all_unit_ids(self):
        return self.unit_id_to_stmt_ids.keys()

    def export(self):
        if len(self.unit_id_to_stmt_ids) == 0:
            return

        results = []
        for (unit_id, stmt_ids) in self.unit_id_to_stmt_ids.items():
            results.append([unit_id, min(stmt_ids), max(stmt_ids)])
        DataModel(results, columns = schema.unit_id_to_stmt_id_schema).save(self.path)

    def restore(self):
        df = DataModel().load(self.path)
        for row in df:
            unit_id = row.unit_id
            min_stmt_id = row.min_stmt_id
            max_stmt_id = row.max_stmt_id
            stmt_ids = range(min_stmt_id, max_stmt_id + 1)
            self.unit_id_to_stmt_ids[unit_id] = stmt_ids
            for stmt_id in stmt_ids:
                self.stmt_id_to_unit_id[stmt_id] = unit_id

class UnitIDToMethodIDLoader:
    def __init__(self, path):
        self.unit_id_to_stmt_ids = {}
        self.stmt_id_to_unit_id = {}
        self.path = path

    def save(self, unit_id, stmt_ids):
        if len(stmt_ids) == 0:
            return
        if isinstance(stmt_ids, set):
            stmt_ids = list(stmt_ids)
        self.unit_id_to_stmt_ids[unit_id] = stmt_ids

        if isinstance(stmt_ids, (int, float, str)):
            self.stmt_id_to_unit_id[stmt_ids] = unit_id
        else:
            for each_id in stmt_ids:
                self.stmt_id_to_unit_id[each_id] = unit_id

    def load_value_to_key(self, stmt_id):
        return self.stmt_id_to_unit_id.get(stmt_id, -1)

    def load_key_to_values(self, unit_id):
        return self.unit_id_to_stmt_ids.get(unit_id, [])

    def load_all_values(self):
        return self.stmt_id_to_unit_id.keys()

    def load_all_unit_ids(self):
        return self.unit_id_to_stmt_ids.keys()

    def is_method_decl(self, stmt_id):
        return stmt_id in self.stmt_id_to_unit_id

    def export(self):
        if len(self.unit_id_to_stmt_ids) == 0:
            return

        results = []
        for (unit_id, stmt_ids) in self.unit_id_to_stmt_ids.items():
            results.append([unit_id, stmt_ids])
        DataModel(results, columns = schema.unit_id_to_method_id_schema).save(self.path)

    def restore(self):
        df = DataModel().load(self.path)
        for row in df:
            unit_id, stmt_ids = row.raw_data()
            self.unit_id_to_stmt_ids[unit_id] = stmt_ids
            for stmt_id in stmt_ids:
                self.stmt_id_to_unit_id[stmt_id] = unit_id

class ClassIdToNameLoader(UnitIDToMethodIDLoader):
    def export(self):
        if len(self.unit_id_to_stmt_ids) == 0:
            return

        results = []
        for (unit_id, stmt_ids) in self.unit_id_to_stmt_ids.items():
            results.append([unit_id, stmt_ids])
        DataModel(results, columns = schema.class_id_to_name_schema).save(self.path)

class UnitIDToClassIDLoader(UnitIDToMethodIDLoader):
    def is_class_decl(self, stmt_id):
        return stmt_id in self.stmt_id_to_unit_id

class UnitIDToNamespaceIDLoader(UnitIDToMethodIDLoader):
    def is_namespace_decl(self, stmt_id):
        return stmt_id in self.stmt_id_to_unit_id

class UnitIDToVariableIDLoader(UnitIDToMethodIDLoader):
    def is_variable_decl(self, stmt_id):
        return stmt_id in self.stmt_id_to_unit_id

class UnitIDToImportStmtIDLoader(UnitIDToMethodIDLoader):
    def is_import_stmt(self, stmt_id):
        return stmt_id in self.stmt_id_to_unit_id

class MethodIDToParameterIDLoader(UnitIDToMethodIDLoader):
    def is_parameter_decl(self, stmt_id):
        return stmt_id in self.stmt_id_to_unit_id

    def is_parameter_decl_of_method(self, stmt_id, method_id):
        parameters = self.unit_id_to_stmt_ids.get(method_id, set())
        return stmt_id in parameters

class MethodsInClassLoader(UnitIDToMethodIDLoader):
    def is_method_decl_of_class(self, stmt_id, class_id):
        methods = self.unit_id_to_stmt_ids.get(class_id, set())
        return stmt_id in methods

    def export(self):
        if len(self.unit_id_to_stmt_ids) == 0:
            return

        results = []
        for (unit_id, class_ids) in self.unit_id_to_stmt_ids.items():

            for method in class_ids:
                results.append([method.unit_id, method.class_id, method.name, method.stmt_id])
        DataModel(results, columns = schema.class_id_to_method_id_schema).save(self.path)

class ExternalSymbolIDCollectionLoader:
    def __init__(self, path):
        self.path = path
        self.method_id_to_external_symbol_id_collection = {}

    def save_external_symbol_id_collection(self, method_id, external_symbol_id_collection):
        results = set()
        if isinstance(external_symbol_id_collection, dict):
            for symbol_name, symbol_id in external_symbol_id_collection.items():
                results.add(symbol_id)
        elif isinstance(external_symbol_id_collection, list):
            results = set(external_symbol_id_collection)
        else:
            results = external_symbol_id_collection
        self.method_id_to_external_symbol_id_collection[method_id] = results

    def load_external_symbol_id_collection(self, method_id):
        return self.method_id_to_external_symbol_id_collection.get(method_id, {})

    def export(self):
        if len(self.method_id_to_external_symbol_id_collection) == 0:
            return
        results = []
        for (method_id, external_symbol_id_collection) in self.method_id_to_external_symbol_id_collection.items():
            results.append({
                'method_id': method_id,
                'external_symbol_id_collection': external_symbol_id_collection
            })
        DataModel(results).save(self.path)

    def restore(self):
        df = DataModel().load(self.path)
        for row in df:
            self.method_id_to_external_symbol_id_collection[row.method_id] = row.external_symbol_id_collection


class EntryPointsLoader:
    def __init__(self, path):
        self.path = path
        self.entry_points = set()

    def save(self, entry_points):
        self.entry_points |= set(entry_points)

    def load_entry_points(self):
        return self.entry_points

    def export(self):
        if len(self.entry_points) == 0:
            return
        DataModel([{
            'entry_points': list(self.entry_points)
        }]).save(self.path)

    def restore(self):
        df = DataModel().load(self.path)
        row = df.access(0)
        data = row.raw_data()
        self.entry_points = set(data[0])

class CFGLoader(GeneralLoader):
    def query_flattened_item_when_loading(self, method_id, bundle_data):
        flattened_item = bundle_data.query(bundle_data.method_id.bundle_search(method_id))
        return flattened_item

    def unflatten_item_dataframe_when_loading(self, method_id, item_df):
        cfg = ControlFlowGraph(method_id)
        for row in item_df:
            cfg.add_edge(row.src_stmt_id, row.dst_stmt_id, row.control_flow_type)
        return cfg.graph

    def flatten_item_when_saving(self, method_id, cfg: nx.DiGraph):
        edges = []
        old_edges = cfg.edges(data='weight', default = 0)
        for e in old_edges:
            edges.append((
                method_id,
                e[0],
                e[1],
                0 if util.is_empty(e[2]) else e[2]
            ))
        return edges

##############################################################
# The following is to deal with the results of basice analysis
##############################################################
class MethodLevelAnalysisResultLoader(GeneralLoader):
    def query_flattened_item_when_loading(self, _id, bundle_data):
        if type(_id) == tuple:
            flattened_item = bundle_data.query(bundle_data.hash_id.bundle_search(hash(_id)))
        else:
            flattened_item = bundle_data.query(bundle_data.method_id.bundle_search(_id))
        return flattened_item

class BitVectorManagerLoader(MethodLevelAnalysisResultLoader):
    def unflatten_item_dataframe_when_loading(self, _id, flattened_item):
        manager = BitVectorManager()
        counter = 0
        id_to_bit_pos = {}
        bit_pos_to_id = {}
        for row in flattened_item:
            counter += 1
            bit_id = None
            if row.state_id:
                bit_id = StateDefNode(index = int(row.index), state_id = int(row.state_id), stmt_id = int(row.stmt_id))
            elif row.symbol_id:
                bit_id = SymbolDefNode(index = int(row.index), symbol_id = int(row.symbol_id), stmt_id = int(row.stmt_id))
            if not bit_id:
                continue
            bit_pos_to_id[int(row.bit_pos)] = bit_id
            id_to_bit_pos[bit_id] = int(row.bit_pos)
        manager.counter = counter
        manager.id_to_bit_pos = id_to_bit_pos
        manager.bit_pos_to_id = bit_pos_to_id
        return manager

    def flatten_item_when_saving(self, method_id, bit_vector_manager: BitVectorManager):
        return bit_vector_manager.to_dict(method_id)

class StmtStatusLoader(MethodLevelAnalysisResultLoader):
    def unflatten_item_dataframe_when_loading(self, method_id, flattened_item):
        stmt_to_status = {}
        for row in flattened_item:
            stmt_to_status[row.stmt_id] = \
                StmtStatus(
                    stmt_id = int(row.stmt_id),
                    defined_symbol = int(row.defined_symbol),
                    used_symbols = [int(item) for item in ast.literal_eval(row.used_symbols)],
                    implicitly_defined_symbols = [int(item) for item in ast.literal_eval(row.implicitly_defined_symbols)],
                    implicitly_used_symbols = [int(item) for item in ast.literal_eval(row.implicitly_used_symbols)],
                    in_symbol_bits = int(row.in_symbol_bits),
                    out_symbol_bits = int(row.out_symbol_bits),
                    defined_states = set(row.defined_states),
                    in_state_bits = util.bytes_to_int(row.in_state_bits),
                    out_state_bits = util.bytes_to_int(row.out_state_bits),
                    field_name = row.field,
                )
        return stmt_to_status

    def flatten_item_when_saving(self, method_id, stmt_to_status: dict[int, StmtStatus]):
        all_status = []
        for _, status in stmt_to_status.items():
            record = status.to_dict(method_id)
            all_status.append(record)
        return all_status

class SymbolStateSpaceLoader(MethodLevelAnalysisResultLoader):
    def unflatten_item_dataframe_when_loading(self, _id, flattened_item):
        symbol_state_space = SymbolStateSpace()
        for row in flattened_item:
            if row.symbol_or_state == SYMBOL_OR_STATE.SYMBOL:
                item = Symbol(
                    stmt_id = row.stmt_id,
                    symbol_id = row.symbol_id,
                    source_unit_id = row.source_unit_id,
                    name = row.name,
                    default_data_type = row.default_data_type,
                    states = set(row.states),
                    symbol_or_state = row.symbol_or_state
                )
            else:
                access_path = []
                access_path_str_list = row.access_path
                for access_path_point_str in access_path_str_list:
                    access_path_point = ast.literal_eval(access_path_point_str)
                    access_path.append(
                        AccessPoint(
                            kind = access_path_point['kind'],
                            key = access_path_point['key'],
                            state_id = access_path_point['state_id']
                        )
                    )
                item = State(
                    stmt_id = row.stmt_id,
                    data_type = row.data_type,
                    state_type = row.state_type,
                    state_id = row.state_id,
                    value = row.value,
                    fields = ast.literal_eval(row.fields),
                    array = ast.literal_eval(row.array),
                    tangping_flag = row.tangping_flag,
                    tangping_elements = ast.literal_eval(row.tangping_elements),
                    access_path = access_path,
                    symbol_or_state = row.symbol_or_state
                )
            symbol_state_space.add(item)

        return symbol_state_space

    def flatten_item_when_saving(self, _id, symbol_state_space: SymbolStateSpace):
        return symbol_state_space.to_dict(_id)

# TODO: convert to memory
class CalleeParameterMapping(MethodLevelAnalysisResultLoader):
    def unflatten_item_dataframe_when_loading(self, _id, flattened_item):
        parameter_mapping_list = []
        for row in flattened_item:
            arg_access_path = []
            access_path_str_list = row.arg_access_path
            for access_path_point_str in access_path_str_list:
                access_path_point = ast.literal_eval(access_path_point_str)
                arg_access_path.append(
                    AccessPoint(
                        kind = access_path_point['kind'],
                        key = access_path_point['key'],
                        state_id = access_path_point['state_id']
                    )
                )

            parameter_access_point_str = row.parameter_access_path
            parameter_access_point = ast.literal_eval(parameter_access_point_str)
            parameter_access_path = AccessPoint(
                kind = parameter_access_point['kind'],
                key = parameter_access_point['key'],
                state_id = parameter_access_point['state_id']
            )

            parameter_mapping_list.append(
                ParameterMapping(
                    arg_index_in_space = row.arg_index_in_space,
                    arg_state_id = row.arg_state_id,
                    arg_source_symbol_id = row.arg_source_symbol_id,
                    parameter_symbol_id = row.parameter_symbol_id,
                    arg_access_path = arg_access_path,
                    parameter_type = row.parameter_type,
                    parameter_access_path = parameter_access_path,
                    is_default_value = row.is_default_value,
                )
            )
        return parameter_mapping_list

    def flatten_item_when_saving(self, _id, parameter_mapping_list: list[ParameterMapping]):
        all_parameter_mapping = []
        for parameter_mapping in parameter_mapping_list:
            record = parameter_mapping.to_dict(_id)
            all_parameter_mapping.append(record)
        return all_parameter_mapping

class MethodDefUseSummaryLoader:
    def __init__(self, path):
        self.method_summary_records = {}
        self.path = path

    def load(self, method_id):
        return self.method_summary_records.get(method_id)

    def save(self, method_id, basic_method_summary: MethodDefUseSummary):
        self.method_summary_records[method_id] = basic_method_summary

    def restore(self):
        # read file and convert to self.all_method_def_use
        df = DataModel().load(self.path)
        for row in df:
            self.method_summary_records[row.method_id] = MethodDefUseSummary(
                row.method_id,
                row.parameter_symbol_ids,
                row.local_symbol_ids,
                row.defined_external_symbol_ids,
                row.used_external_symbol_ids,
                row.return_symbol_ids,
                row.defined_this_symbol_id,
                row.used_this_symbol_id
            )

    def export(self):
        if len(self.method_summary_records) == 0:
            return

        results = []
        for method_id in sorted(self.method_summary_records.keys()):
            summary = self.method_summary_records[method_id]
            results.append(summary.to_dict())
        DataModel(results).save(self.path)

class MethodSummaryLoader:
    def __init__(self, path):
        self.method_summary_records = {}
        self.path = path

    def load(self, _id):
        return self.method_summary_records.get(_id)

    def save(self, _id, method_summary):
        self.method_summary_records[_id] = method_summary

    def convert_list_to_dict(self, l):
        if l is None:
            return {}
        if len(l) == 0:
            return {}

        results = {}
        for item in l:
            key = item[0]
            raw_index = item[1]
            new_index = item[2]
            if len(item) > 3:
                default_value_symbol_id = item[3]
            else:
                default_value_symbol_id = -1

            if key not in results:
                results[key] = set()
            results[key].add(
                IndexMapInSummary(raw_index = raw_index, new_index = new_index, default_value_symbol_id = default_value_symbol_id))

        return results

    def restore(self):
        # read file and convert to self.all_method_def_use
        df = DataModel().load(self.path)
        for row in df:
            if row.caller_id:
                self.method_summary_records[(row.caller_id, row.call_stmt_id, row.method_id)] = MethodSummaryInstance(
                    method_id = (row.caller_id, row.call_stmt_id, row.method_id),
                    parameter_symbols = self.convert_list_to_dict(row.parameter_symbols),
                    defined_external_symbols = self.convert_list_to_dict(row.defined_external_symbols),
                    used_external_symbols = self.convert_list_to_dict(row.used_external_symbol_ids),
                    return_symbols = self.convert_list_to_dict(row.return_symbols),
                    key_dynamic_content = self.convert_list_to_dict(row.key_dynamic_content),
                    dynamic_call_stmt = row.dynamic_call_stmt,
                    this_symbols = self.convert_list_to_dict(row.this_symbols)
                )
            else:
                self.method_summary_records[row.method_id] = MethodSummaryTemplate(
                    method_id = row.method_id,
                    parameter_symbols = self.convert_list_to_dict(row.parameter_symbols),
                    defined_external_symbols = self.convert_list_to_dict(row.defined_external_symbols),
                    used_external_symbols = self.convert_list_to_dict(row.used_external_symbol_ids),
                    return_symbols = self.convert_list_to_dict(row.return_symbols),
                    key_dynamic_content = self.convert_list_to_dict(row.key_dynamic_content),
                    dynamic_call_stmt = row.dynamic_call_stmt,
                    this_symbols = self.convert_list_to_dict(row.this_symbols)
                )

    def export(self):
        if len(self.method_summary_records) == 0:
            return

        results = []
        for method_id in sorted(self.method_summary_records.keys()):
            summary = self.method_summary_records[method_id]
            results.append(summary.to_dict())
        DataModel(results).save(self.path)

class MethodInternalCalleesLoader:
    def __init__(self, path):
        self.path = path
        self.method_internal_callees_records = {}

    def load(self, method_id):
        return self.method_internal_callees_records.get(method_id)

    def save(self, method_id, method_internal_callees):
        self.method_internal_callees_records[method_id] = method_internal_callees

    def restore(self):
        # read file and convert to self.all_method_def_use
        df = DataModel().load(self.path)
        for row in df:
            callee = MethodInternalCallee(
                row.method_id,
                row.callee_type,
                row.stmt_id,
                row.callee_symbol_id,
                row.callee_symbol_index
            )
            if callee.method_id not in self.method_internal_callees_records:
                self.method_internal_callees_records[callee.method_id] = set()
            self.method_internal_callees_records[callee.method_id].add(callee)

    def export(self):
        if len(self.method_internal_callees_records) == 0:
            return

        results = []
        for callee_set in self.method_internal_callees_records.values():
            for callee in callee_set:
                results.append(callee.to_dict())
        DataModel(results).save(self.path)


class CallGraphP1Loader:
    def __init__(self, path):
        self.path = path
        self.call_graph = None

    def save(self, basic_call_graph: CallGraph):
        self.call_graph = basic_call_graph

    def load(self):
        return self.call_graph

    def restore(self):
        df = DataModel().load(self.path)
        self.call_graph = CallGraph()
        for row in df:
            self.call_graph.add_edge(row.source_method_id, row.target_method_id, row.stmt_id)

    def export(self):
        if util.is_empty(self.call_graph):
            return

        results = []
        for edge in self.call_graph.graph.edges(data='weight'):
            results.append({
                "source_method_id": edge[0],
                "target_method_id": edge[1],
                "stmt_id": edge[2]
            })
        DataModel(results).save(self.path)

class CallPathLoader:
    def __init__(self, file_path):
        self.path = file_path
        self.all_APaths = []

    def save(self, all_APaths: set):
        self.all_APaths = all_APaths

    def load(self):
        # 防止该文件不存在第三阶段call_path从而读取报错
        if not os.path.exists(self.path):
            return {}
        dm = DataModel().load(self.path)

        return self.all_APaths

    def export(self):
        if len(self.all_APaths) == 0:
            return
        all_pathTuples = [(index, ap.path) for index, ap in enumerate(self.all_APaths)]
        DataModel(all_pathTuples,columns=schema.call_path_schema).save(self.path)

class UniqueSymbolIDAssignerLoader:
    def __init__(self, path):
        self.path = path
        self.negative_symbol_id = config.BUILTIN_SYMBOL_START_ID
        self.max_gir_id = config.DEFAULT_MAX_GIR_ID
        self.positive_symbol_id = self.max_gir_id + config.POSITIVE_GIR_INTERVAL

    def save_max_gir_id(self, max_gir_id):
        self.max_gir_id = max_gir_id
        # 计算基础值（原逻辑）
        base_value = self.max_gir_id + config.POSITIVE_GIR_INTERVAL
        # 向上取整到 POSITIVE_GIR_INTERVAL 的整数倍（抹掉后面几位）
        self.positive_symbol_id = (base_value + config.POSITIVE_GIR_INTERVAL - 1) // config.POSITIVE_GIR_INTERVAL * config.POSITIVE_GIR_INTERVAL

    def load_max_gir_id(self):
        return self.max_gir_id

    def is_greater_than_max_gir_id(self, symbol_id):
        return symbol_id > self.max_gir_id

    def assign_new_unique_negative_id(self):
        self.negative_symbol_id -= 1
        return self.negative_symbol_id

    def assign_new_unique_positive_id(self):
        self.positive_symbol_id += 1
        return self.positive_symbol_id

    def restore(self):
        df = DataModel().load(self.path)
        for row in df:
            self.negative_symbol_id = row.negative_symbol_id
            self.positive_symbol_id = row.positive_symbol_id
            self.max_gir_id = row.max_gir_id
            break

    def export(self):
        results = [{
            "negative_symbol_id": self.negative_symbol_id,
            "positive_symbol_id": self.positive_symbol_id,
            "max_gir_id": self.max_gir_id
        }]
        DataModel(results).save(self.path)

class ImportGraphLoader:
    def __init__(self, path):
        self.path = path
        self.import_graph = None
        self.import_graph_nodes = []
        self.import_deps = None
        self.symbol_id_to_import_node = {}

        self.import_graph_nodes_save_path = self.path + "_nodes"

        dir_path = os.path.dirname(self.path)
        new_save_path = os.path.join(dir_path, "import_deps")
        self.import_deps_save_path = new_save_path

    def save(self, import_graph):
        self.import_graph = import_graph

    def load(self):
        return self.import_graph

    def save_nodes(self, symbol_id_to_symbol_node):
        # 定义排序键函数，根据节点的 unit_id 和 symbol_id 进行排序
        def sort_key(node_key):
            node = symbol_id_to_symbol_node[node_key]
            return node.unit_id, node.symbol_id

        result = []
        for node_key in sorted(symbol_id_to_symbol_node, key=sort_key):
            result.append(symbol_id_to_symbol_node[node_key])

        # 对图节点的键按照排序规则进行排序
        self.import_graph_nodes = result
        self.symbol_id_to_import_node = symbol_id_to_symbol_node

    def load_nodes(self):
        return self.import_graph_nodes

    def save_deps(self, import_deps):
        self.import_deps = import_deps

    def load_deps(self):
        return self.import_deps

    def get_successor_nodes_from_ids(self, successor_ids):
        result = []
        if isinstance(successor_ids, int):
            successor_ids = [successor_ids]
        for each_succ in successor_ids:
            import_node = self.symbol_id_to_import_node.get(each_succ)
            if import_node:
                result.append(import_node)
        return result

    def get_internal_successor_nodes(self, node_id):
        successor_ids = util.graph_successors_with_weight(
            self.import_graph, node_id, IMPORT_GRAPH_EDGE_KIND.INTERNAL_SYMBOL
        )
        return self.get_successor_nodes_from_ids(successor_ids)

    def get_external_successor_nodes(self, node_id):
        successor_ids = util.graph_successors_with_weight(
            self.import_graph, node_id, IMPORT_GRAPH_EDGE_KIND.EXTERNAL_SYMBOL
        )
        return self.get_successor_nodes_from_ids(successor_ids)

    def get_edges_and_nodes_with_edge_attrs(self, node_id, attr_dict: dict):
        EdgeNodePair = namedtuple("EdgeNodePair", ["edge", "node"])
        edge_node_list = util.graph_successors_with_edge_attrs(self.import_graph, node_id, attr_dict)
        return [EdgeNodePair(edge, self.get_successor_nodes_from_ids(node_index)) for edge, node_index in edge_node_list]

    def restore(self):
        df = DataModel().load(self.path)
        self.import_graph = nx.DiGraph()
        for row in df:
            self.import_graph.add_edge(row.parent_node, row.child_node, weight=row.edge_type)

        self.import_graph_nodes = DataModel().load(self.import_graph_nodes_save_path)
        for each_node in self.import_graph_nodes:
            self.symbol_id_to_import_node[each_node.symbol_id] = each_node

        df = DataModel().load(self.import_deps_save_path)
        self.import_deps = nx.DiGraph()
        for row in df:
            self.import_deps.add_edge(row.unit_id, row.imported_unit_id)

    def export(self):
        if util.is_empty(self.import_graph):
            return

        # 初始化一个空列表，用于存储图中边的信息
        results = []
        # 遍历图中的每一条边
        for edge in self.import_graph.edges(data=True):
            # 为每条边创建一个字典，记录边的起始节点和结束节点
            edge_info = {
                "parent_node": edge[0],
                "child_node": edge[1],
                "edge_type": edge[2].get('weight', None)
            }
            # 将边的信息添加到结果列表中
            results.append(edge_info)

        DataModel(results).save(self.path)

        # 初始化一个列表，用于存储图中节点的信息
        node_info_list = []

        # 遍历排序后的节点键，将节点信息转换为字典并添加到列表中
        for each_node in self.import_graph_nodes:
            node_info_list.append(each_node.to_dict())

        # 使用 DataModel 保存节点信息到文件
        DataModel(node_info_list).save(self.import_graph_nodes_save_path)

        # 初始化一个空列表，用于存储图中边的信息
        results = []
        # 遍历图中的每一条边
        for edge in self.import_deps.edges:
            # 为每条边创建一个字典，记录边的起始节点和结束节点
            edge_info = {
                "unit_id": edge[0],
                "imported_unit_id": edge[1]
            }
            # 将边的信息添加到结果列表中
            results.append(edge_info)

        # 使用 DataModel 保存边信息到文件
        DataModel(results).save(self.import_deps_save_path)

class TypeGraphLoader:
    def __init__(self, path):
        self.path = path
        self.type_graph = None

    def save(self, type_graph):
        self.type_graph = type_graph

    def load(self):
        return self.type_graph

    def restore(self):
        df = DataModel().load(self.path)
        self.type_graph = BasicGraph()
        for row in df:
            self.type_graph.add_edge(row.type_id, row.parent_type_id, row.inheritance)

    def export(self):
        if util.is_empty(self.type_graph):
            return

        results = []
        for edge in self.type_graph.graph.edges(data='weight'):
            results.append({
                "type_id": edge[0],
                "parent_type_id": edge[1],
                "name": edge[2].name,
                "parent_pos": edge[2].parent_pos,
                "parent_name": edge[2].parent_name
            })
        DataModel(results).save(self.path)

class MethodSymbolToDefinedLoader(MethodLevelAnalysisResultLoader):
    def unflatten_item_dataframe_when_loading(self, method_id, flattened_item):
        symbol_to_define = {}
        for row in flattened_item:
            if row.symbol_id not in symbol_to_define:
                symbol_to_define[row.symbol_id] = set()

            defined = row.defined
            for each_defined in defined:
                if isinstance(each_defined, (tuple, numpy.ndarray)):
                    symbol_to_define[row.symbol_id].add(
                        SymbolDefNode(index = int(each_defined[0]), symbol_id = int(row.symbol_id), stmt_id = int(each_defined[1])))

                else:
                    symbol_to_define[row.symbol_id].add(each_defined)

        return symbol_to_define

    def flatten_item_when_saving(self, method_id, symbol_to_define):
        all_defined = []
        for symbol_id, defined_set in symbol_to_define.items():
            defined = []
            for each_defined in defined_set:
                if isinstance(each_defined, SymbolDefNode):
                    defined.append((each_defined.index, each_defined.stmt_id))

                else:
                    defined.append(each_defined)

            all_defined.append({
                "method_id": method_id,
                "symbol_id": symbol_id,
                "defined": defined
            })
        return all_defined

class MethodStateToDefinedLoader(MethodLevelAnalysisResultLoader):
    def unflatten_item_dataframe_when_loading(self, method_id, flattened_item):
        state_to_define = {}
        for row in flattened_item:
            if row.state_id not in state_to_define:
                state_to_define[row.state_id] = set()

            for each_defined in row.defined:
                if isinstance(each_defined, tuple):
                    state_to_define[row.state_id].add(
                        StateDefNode(index = int(each_defined[0]), state_id = int(row.state_id), stmt_id = int(each_defined[1])))
        return state_to_define

    def flatten_item_when_saving(self, method_id, state_to_define):
        all_defined = []
        for state_id, defined_set in state_to_define.items():
            defined = []
            for each_defined in defined_set:
                if isinstance(each_defined, StateDefNode):
                    defined.append((each_defined.index, each_defined.stmt_id))

                else:
                    defined.append(each_defined)

            all_defined.append({
                "method_id": method_id,
                "state_id": state_id,
                "defined": defined
            })
        return all_defined

class MethodSymbolToUsedLoader(MethodLevelAnalysisResultLoader):
    def unflatten_item_dataframe_when_loading(self, method_id, flattened_item):
        stmt_to_use = {}
        for row in flattened_item:
            stmt_to_use[row.symbol_id] = set(row.used)
        return stmt_to_use

    def flatten_item_when_saving(self, method_id, symbol_to_use):
        all_used = []
        for symbol_id, used in symbol_to_use.items():
            all_used.append({
                "method_id": method_id,
                "symbol_id": symbol_id,
                "used": list(used)
            })
        return all_used

class GroupedMethodsLoader:
    def __init__(self, path):
        self.path = path
        self.grouped_methods = None

    def save(self, grouped_methods):
        self.grouped_methods = grouped_methods

    def load(self):
        return self.grouped_methods

    def export(self):
        if util.is_empty(self.grouped_methods):
            return
        DataModel([self.grouped_methods.to_dict()]).save(self.path)

    def restore(self):
        df = DataModel().load(self.path)
        if len(df) == 0:
            return
        data = df.access(0)
        self.grouped_methods = SimplyGroupedMethodTypes(
            data.no_callees,
            data.only_direct_callees,
            data.mixed_direct_callees,
            data.only_dynamic_callees,
            data.containing_dynamic_callees,
            data.containing_error_callees
        )

class SymbolGraphLoader(MethodLevelAnalysisResultLoader):
    def unflatten_item_dataframe_when_loading(self, _id, item_df):
        # print("@SymbolGraphLoader@item_df", item_df)
        method_id = _id
        symbol_graph = SymbolGraph(method_id)
        for row in item_df:
            if not util.isna(row.defined):
                defined_tuple = row.defined
                key = SymbolDefNode(defined_tuple[0], defined_tuple[1], defined_tuple[2])
                symbol_graph.add_edge(row.stmt_id, key, row.edge_type)
            else:
                used_tuple = row.used
                key = SymbolDefNode(used_tuple[0], used_tuple[1], used_tuple[2])
                symbol_graph.add_edge(key, row.stmt_id, row.edge_type)
        return symbol_graph.graph

    def flatten_item_when_saving(self, _id, symbol_graph: nx.DiGraph):
        method_id = _id
        edges = []
        old_edges = symbol_graph.edges(data='weight', default = 0)
        for e in old_edges:
            src_node = e[0]
            dst_node = e[1]
            edge_type = 0 if util.is_empty(e[2]) else e[2]
            if isinstance(src_node, (int, numpy.int64)):
                edges.append({
                    "method_id": method_id,
                    "stmt_id": int(src_node),
                    "defined": dst_node.to_tuple(),
                    "edge_type": edge_type
                })
            else:
                edges.append({
                    "method_id": method_id,
                    "used": src_node.to_tuple(),
                    "stmt_id": int(dst_node),
                    "edge_type": edge_type
                })
        # print(edges)
        return edges


############################################################

class Loader:
    # This is our file system manager
    def __init__(self, options, apps):
        self.options = options
        self.basic_path = os.path.join(options.workspace, config.BASIC_DIR)
        self.semantic_path_p1 = os.path.join(options.workspace, config.SEMANTIC_DIR_P1)
        self.semantic_path_p2 = os.path.join(options.workspace, config.SEMANTIC_DIR_P2)
        self.semantic_path_p3 = os.path.join(options.workspace, config.SEMANTIC_DIR_P3)
        self.apps = apps

        self._module_symbols_loader: ModuleSymbolsLoader = ModuleSymbolsLoader(
            options,
            os.path.join(self.semantic_path_p1, config.MODULE_SYMBOLS_PATH),
        )

        self._gir_loader = UnitGIRLoader(
            options,
            # schema.gir_schema,
            [],
            os.path.join(self.basic_path, config.GIR_BUNDLE_PATH),
            config.GIR_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._unique_symbol_id_assigner_loader = UniqueSymbolIDAssignerLoader(
            os.path.join(self.basic_path, config.UNIQUE_SYMBOL_IDS_PATH),
        )

        self._external_symbol_id_collection_loader = ExternalSymbolIDCollectionLoader(
            os.path.join(self.basic_path, config.EXTERNAL_SYMBOL_ID_COLLECTION_PATH)
        )

        self._cfg_loader: CFGLoader = CFGLoader(
            options,
            schema.control_flow_graph_schema,
            os.path.join(self.basic_path, config.CFG_BUNDLE_PATH),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._scope_hierarchy_loader = ScopeHierarchyLoader(
            options,
            [],
            os.path.join(self.semantic_path_p1, config.SCOPE_HIERARCHY_BUNDLE_PATH),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._unit_id_to_export_symbols_loader = UnitIDToExportSymbolsLoader(
            options,
            [],
            os.path.join(self.semantic_path_p1, config.UNIT_EXPORT_PATH),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._class_id_to_methods_loader = MethodsInClassLoader(
            os.path.join(self.semantic_path_p1, config.CLASS_METHODS_PATH),
        )

        self._call_stmt_id_to_call_format_info_loader = CallStmtIDToCallFormatInfoLoader(
            os.path.join(self.semantic_path_p1, config.CALL_STMT_ID_TO_CALL_FORMAT_INFO_PATH)
        )

        self._method_id_to_method_decl_format_loader = MethodIDToMethodDeclFormat(
            os.path.join(self.semantic_path_p1, config.METHOD_ID_TO_METHOD_DECL_FORMAT_PATH)
        )

        self._unit_id_to_stmt_id_loader: UnitIDToStmtIDLoader = UnitIDToStmtIDLoader(
            os.path.join(self.basic_path, config.UNIT_ID_TO_STMT_ID_PATH)
        )

        self._unit_id_to_method_id_loader: UnitIDToMethodIDLoader = UnitIDToMethodIDLoader(
            os.path.join(self.semantic_path_p1, config.UNIT_ID_TO_METHOD_ID_PATH)
        )

        self._unit_id_to_class_id_loader: UnitIDToClassIDLoader = UnitIDToClassIDLoader(
            os.path.join(self.semantic_path_p1, config.UNIT_ID_TO_CLASS_ID_PATH)
        )

        self._unit_id_to_namespace_id_loader: UnitIDToNamespaceIDLoader = UnitIDToNamespaceIDLoader(
            os.path.join(self.semantic_path_p1, config.UNIT_ID_TO_NAMESPACE_ID_PATH)
        )

        self._unit_id_to_variable_id_loader: UnitIDToVariableIDLoader = UnitIDToVariableIDLoader(
            os.path.join(self.semantic_path_p1, config.UNIT_ID_TO_VARIABLE_ID_PATH)
        )

        self._unit_id_to_import_stmt_id_loader = UnitIDToImportStmtIDLoader(
            os.path.join(self.semantic_path_p1, config.UNIT_ID_TO_IMPORT_STMT_ID_PATH)
        )

        self._method_id_to_parameter_id_loader: MethodIDToParameterIDLoader = MethodIDToParameterIDLoader(
            os.path.join(self.semantic_path_p1, config.METHOD_ID_TO_PARAMETER_ID_PATH)
        )

        self._class_id_to_method_id_loader = MethodIDToParameterIDLoader(
            os.path.join(self.semantic_path_p1, config.CLASS_ID_TO_METHOD_ID_PATH)
        )

        self._class_id_to_field_id_loader = MethodIDToParameterIDLoader(
            os.path.join(self.semantic_path_p1, config.CLASS_ID_TO_FIELD_ID_PATH)
        )

        self._class_id_to_class_name_loader = ClassIdToNameLoader(
            os.path.join(self.semantic_path_p1, config.CLASS_ID_TO_CLASS_NAME_PATH)
        )

        self._method_id_to_method_name_loader = UnitIDToMethodIDLoader(
            os.path.join(self.semantic_path_p1, config.METHOD_ID_TO_METHOD_NAME_PATH)
        )

        self._symbol_name_to_scope_ids_loader: SymbolNameToScopeIDsLoader = SymbolNameToScopeIDsLoader(
            options,
            [],
            os.path.join(self.semantic_path_p1, config.SYMBOL_NAME_TO_SCOPE_IDS_PATH),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._scope_id_to_symbol_info_loader: ScopeIDToSymbolInfoLoader = ScopeIDToSymbolInfoLoader(
            options,
            [],
            os.path.join(self.semantic_path_p1, config.SCOPE_ID_TO_SYMBOL_INFO_PATH),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._scope_id_to_available_scope_ids_loader: ScopeIDToAvailableScopeIDsLoader = ScopeIDToAvailableScopeIDsLoader(
            options,
            [],
            os.path.join(self.semantic_path_p1, config.SCOPE_ID_TO_AVAILABLE_SCOPE_IDS_PATH),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        # self._call_stmt_id_to_info = ScopeIDToAvailableScopeIDsLoader(
        #     options,
        #     [],
        #     os.path.join(self.semantic_path_p1, config.CALL_STMT_ID_TO_INFO_PATH),
        #     config.LRU_CACHE_CAPACITY,
        #     config.BUNDLE_CACHE_CAPACITY
        # )

        self._unit_symbol_decl_summary_loader: UnitSymbolDeclSummaryLoader = UnitSymbolDeclSummaryLoader(
            self._symbol_name_to_scope_ids_loader,
            self._scope_id_to_symbol_info_loader,
            self._scope_id_to_available_scope_ids_loader
        )

        self._entry_points_loader: EntryPointsLoader = EntryPointsLoader(
            os.path.join(self.semantic_path_p1, config.ENTRY_POINTS_PATH)
        )

        self._import_graph_loader = ImportGraphLoader(
            os.path.join(self.semantic_path_p1, config.IMPORT_GRAPH_PATH),
        )

        self._type_graph_loader = TypeGraphLoader(
            os.path.join(self.semantic_path_p1, config.TYPE_GRAPH_PATH),
        )

        self._symbol_bit_vector_manager_p1_loader = BitVectorManagerLoader(
            options,
            # schema.bit_vector_manager_schema,
            [],
            os.path.join(self.semantic_path_p1, config.SYMBOL_BIT_VECTOR_MANAGER_BUNDLE_PATH_P1),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._symbol_bit_vector_manager_p2_loader = BitVectorManagerLoader(
            options,
            # schema.bit_vector_manager_schema,
            [],
            os.path.join(self.semantic_path_p2, config.SYMBOL_BIT_VECTOR_MANAGER_BUNDLE_PATH_P2),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._class_id_to_members_loader = ClassIDToMembersLoader(
            options,
            [],
            os.path.join(self.semantic_path_p2, config.CLASS_ID_TO_MEMBERS_PATH),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._symbol_bit_vector_manager_p3_loader = BitVectorManagerLoader(
            options,
            # schema.bit_vector_manager_schema,
            [],
            os.path.join(self.semantic_path_p3, config.SYMBOL_BIT_VECTOR_MANAGER_BUNDLE_PATH_P3),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._state_bit_vector_manager_p2_loader = BitVectorManagerLoader(
            options,
            # schema.bit_vector_manager_schema,
            [],
            os.path.join(self.semantic_path_p2, config.STATE_BIT_VECTOR_MANAGER_BUNDLE_PATH_P2),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._state_bit_vector_manager_p3_loader = BitVectorManagerLoader(
            options,
            # schema.bit_vector_manager_schema,
            [],
            os.path.join(self.semantic_path_p3, config.STATE_BIT_VECTOR_MANAGER_BUNDLE_PATH_P3),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._stmt_status_p1_loader = StmtStatusLoader(
            options,
            # schema.stmt_status_schema,
            [],
            os.path.join(self.semantic_path_p1, config.STMT_STATUS_BUNDLE_PATH_P1),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._stmt_status_p2_loader = StmtStatusLoader(
            options,
            # schema.stmt_status_schema,
            [],
            os.path.join(self.semantic_path_p2, config.STMT_STATUS_BUNDLE_PATH_P2),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._stmt_status_p3_loader = StmtStatusLoader(
            options,
            # schema.stmt_status_schema,
            [],
            os.path.join(self.semantic_path_p3, config.STMT_STATUS_BUNDLE_PATH_P3),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._symbol_state_space_p1_loader = SymbolStateSpaceLoader(
            options,
            # schema.symbol_state_space_schema,
            [],
            os.path.join(self.semantic_path_p1, config.SYMBOL_STATE_SPACE_BUNDLE_PATH_P1),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._symbol_state_space_p2_loader = SymbolStateSpaceLoader(
            options,
            # schema.symbol_state_space_schema,
            [],
            os.path.join(self.semantic_path_p2, config.SYMBOL_STATE_SPACE_BUNDLE_PATH_P2),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._symbol_state_space_summary_p2_loader = SymbolStateSpaceLoader(
            options,
            # schema.symbol_state_space_schema,
            [],
            os.path.join(self.semantic_path_p2, config.SYMBOL_STATE_SPACE_SUMMARY_BUNDLE_PATH_P2),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._symbol_state_space_p3_loader = SymbolStateSpaceLoader(
            options,
            # schema.symbol_state_space_schema,
            [],
            os.path.join(self.semantic_path_p3, config.SYMBOL_STATE_SPACE_BUNDLE_PATH_P3),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._symbol_state_space_summary_p3_loader = SymbolStateSpaceLoader(
            options,
            # schema.symbol_state_space_schema,
            [],
            os.path.join(self.semantic_path_p3, config.SYMBOL_STATE_SPACE_SUMMARY_BUNDLE_PATH_P3),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._method_internal_callees_loader = MethodInternalCalleesLoader(
            os.path.join(self.semantic_path_p1, config.METHOD_INTERNAL_CALLEES_PATH),
        )

        self._method_def_use_summary_loader = MethodDefUseSummaryLoader(
            os.path.join(self.semantic_path_p1, config.METHOD_DEF_USE_SUMMARY_PATH),
        )

        self._method_summary_template_loader = MethodSummaryLoader(
            os.path.join(self.semantic_path_p2, config.METHOD_SUMMARY_TEMPLATE_PATH),
        )

        self._method_summary_template_instance = MethodSummaryLoader(
            os.path.join(self.semantic_path_p3, config.METHOD_SUMMARY_INSTANCE_PATH),
        )

        self._call_graph_p1_loader = CallGraphP1Loader(
            os.path.join(self.semantic_path_p1, config.CALL_GRAPH_BUNDLE_PATH_P1),
        )

        self._call_graph_p2_loader = CallGraphP1Loader(
            os.path.join(self.semantic_path_p2, config.CALL_GRAPH_BUNDLE_PATH_P2),
        )

        self._call_path_p3_loader = CallPathLoader(
            os.path.join(self.semantic_path_p3, config.CALL_PATH_BUNDLE_PATH_P3),
        )

        self._symbol_to_define_loader = MethodSymbolToDefinedLoader(
            options,
            [],
            os.path.join(self.semantic_path_p1, config.SYMBOL_TO_DEFINE_PATH),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._symbol_to_define_p2_loader = MethodSymbolToDefinedLoader(
            options,
            [],
            os.path.join(self.semantic_path_p2, config.SYMBOL_TO_DEFINE_PATH_P2),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._symbol_to_define_p3_loader = MethodSymbolToDefinedLoader(
            options,
            [],
            os.path.join(self.semantic_path_p3, config.SYMBOL_TO_DEFINE_PATH_P3),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._state_to_define_p1_loader = MethodStateToDefinedLoader(
            options,
            [],
            os.path.join(self.semantic_path_p1, config.STATE_TO_DEFINE_PATH_P1),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._state_to_define_p2_loader = MethodStateToDefinedLoader(
            options,
            [],
            os.path.join(self.semantic_path_p2, config.STATE_TO_DEFINE_PATH_P2),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._symbol_to_use_loader = MethodSymbolToUsedLoader(
            options,
            [],
            os.path.join(self.semantic_path_p1, config.SYMBOL_TO_USE_PATH),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._grouped_methods_loader: GroupedMethodsLoader = GroupedMethodsLoader(
            os.path.join(self.semantic_path_p1, config.GROUPED_METHODS_PATH)
        )

        self._symbol_graph_p2_loader: SymbolGraphLoader = SymbolGraphLoader(
            options,
            schema.symbol_graph_schema_p2,
            os.path.join(self.semantic_path_p2, config.SYMBOL_GRAPH_BUNDLE_PATH),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._symbol_graph_p3_loader: SymbolGraphLoader = SymbolGraphLoader(
            options,
            schema.symbol_graph_schema_p2,
            os.path.join(self.semantic_path_p2, config.SYMBOL_GRAPH_BUNDLE_PATH_P3),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._callee_parameter_mapping_p2_loader: CalleeParameterMapping = CalleeParameterMapping(
            options,
            [],
            os.path.join(self.semantic_path_p2, config.CALLEE_PARAMETER_MAPPING_BUNDLE_PATH_P2),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self._callee_parameter_mapping_p3_loader: CalleeParameterMapping = CalleeParameterMapping(
            options,
            [],
            os.path.join(self.semantic_path_p2, config.CALLEE_PARAMETER_MAPPING_BUNDLE_PATH_P3),
            config.LRU_CACHE_CAPACITY,
            config.BUNDLE_CACHE_CAPACITY
        )

        self.method_header_cache = util.LRUCache(config.METHOD_HEADER_CACHE_CAPABILITY)
        self.method_body_cache = util.LRUCache(config.METHOD_BODY_CACHE_CAPABILITY)
        self.stmt_scope_cache = util.LRUCache(config.STMT_SCOPE_CACHE_CAPABILITY)

        self._all_loaders = self.init_loading()

    def init_loading(self):
        results = []
        loader_list = list(self.__dict__.keys())
        avoidings = ["_all_loaders"]
        for loader in loader_list:
            if loader not in avoidings:
                if loader.startswith("_") and loader.endswith("_loader"):
                    results.append(getattr(self, loader))
        return results

    def load_method_header(self, method_id):
        if method_id <= 0:
            return (None, None)

        if self.method_header_cache.contain(method_id):
            return self.method_header_cache.get(method_id)

        unit_id = self._unit_id_to_method_id_loader.load_value_to_key(method_id)
        unit_gir = self._gir_loader.load(unit_id)
        if util.is_empty(unit_gir):
            return (None, None)
        method_decl_stmt = unit_gir.query_first(unit_gir.stmt_id.eq(method_id))
        method_parameters = unit_gir.read_block(method_decl_stmt.parameters)
        result = (method_decl_stmt, method_parameters)
        self.method_header_cache.put(method_id, result)
        return result

    def load_method_body(self, method_id):
        method_decl_stmt, _ = self.load_method_header(method_id)
        return self._load_method_body_by_header(method_id, method_decl_stmt)

    def _load_method_body_by_header(self, method_id, method_decl_stmt):
        if util.is_empty(method_decl_stmt):
            return None

        if self.method_body_cache.contain(method_id):
            self.method_body_cache.get(method_id)

        unit_id = self._unit_id_to_method_id_loader.load_value_to_key(method_id)
        unit_gir = self._gir_loader.load(unit_id)
        method_body = unit_gir.read_block(method_decl_stmt.body)
        self.method_body_cache.put(method_id, method_body)
        return method_body

    def load_method_gir(self, method_id):
        method_decl_stmt, method_parameters = self.load_method_header(method_id)
        method_body = self._load_method_body_by_header(method_id, method_decl_stmt)
        return (method_decl_stmt, method_parameters, method_body)
 
    def load_stmt_gir(self, stmt_id):
        if stmt_id <= 0:
            return None
        unit_id = self.convert_stmt_id_to_unit_id(stmt_id)
        unit_gir = self._gir_loader.load(unit_id)
        stmt_gir = unit_gir.query_first(unit_gir.stmt_id.eq(stmt_id))
        return stmt_gir
    
    def load_stmt_scope(self, stmt_id):
        if stmt_id <= 0:
            return None
        if self.stmt_scope_cache.contain(stmt_id):
            return self.stmt_scope_cache.get(stmt_id)
        unit_id = self.convert_stmt_id_to_unit_id(stmt_id)
        scope_data = self.load_unit_scope_hierarchy(unit_id)
        stmt_scope = scope_data.query_first(scope_data.stmt_id == stmt_id)
        self.stmt_scope_cache.put(stmt_id, stmt_scope)
        return stmt_scope

    def export(self):
        for loader in self._all_loaders:
            # print("loader export", loader)
            loader.export()
            if hasattr(loader, 'export_indexing'):
                loader.export_indexing()

    def restore(self):
        for loader in self._all_loaders:
            if hasattr(loader, 'restore_indexing'):
                #util.debug(loader.__class__.__name__ + " is restoring index")
                try:
                    loader.restore_indexing()
                except FileNotFoundError:
                    pass
                # except TypeError as e:
                    # util.warn(e)
            if hasattr(loader, 'restore'):
                #util.debug(loader.__class__.__name__ + " is restoring")
                try:
                    loader.restore()
                except FileNotFoundError:
                    pass

    ############################################################
    # The following is used to forwarding calls; This may be better for autocomplete in editor
    # For save_xxx(), its parameters is usually <_id, content> at the most cases
    # For load_xxx(), its parameter is usually <_id>
    # For export_xxx(), it does not have a parameter
    ############################################################
    def load_module_symbol_table(self, *args):
        return self._module_symbols_loader.load_module_symbol_table(*args)
    def save_module_symbols(self, *args):
        return self._module_symbols_loader.save(*args)
    def load_all_module_ids(self):
        return self._module_symbols_loader.load_all_module_ids()
    def load_all_unit_info(self):
        return self._module_symbols_loader.load_all_unit_info()
    def convert_module_id_to_module_info(self, *args):
        return self._module_symbols_loader.convert_module_id_to_module_info(*args)
    def convert_unit_id_to_info(self, *args):
        return self._module_symbols_loader.convert_module_id_to_module_info(*args)
    def convert_unit_id_to_unit_path(self, *args):
        return self._module_symbols_loader.convert_unit_id_to_unit_path(*args)
    def convert_unit_path_to_unit_id(self, *args):
        return self._module_symbols_loader.convert_unit_path_to_unit_id(*args)

    def is_module_id(self, *args):
        return self._module_symbols_loader.is_module_id(*args)
    def is_unit_id(self, *args):
        return self._module_symbols_loader.is_unit_id(*args)
    def is_module_dir_id(self, *args):
        return self._module_symbols_loader.is_module_dir_id(*args)
    def convert_unit_id_to_lang_name(self, *args):
        return self._module_symbols_loader.load_unit_lang_name(*args)
    def convert_module_id_to_child_ids(self, *args):
        return self._module_symbols_loader.convert_module_id_to_child_ids(*args)

    def load_unit_gir(self, *args):
        return self._gir_loader.load(*args)
    def save_unit_gir(self, *args):
        return self._gir_loader.save(*args)
    def export_gir(self):
        return self._gir_loader.export()

    def load_unit_scope_hierarchy(self, *args):
        return self._scope_hierarchy_loader.load(*args)
    def save_unit_scope_hierarchy(self, *args):
        return self._scope_hierarchy_loader.save(*args)
    def load_all_scope_hierarchy(self, *args):
        return self._scope_hierarchy_loader.load_all(*args)
    def export_scope_hierarchy(self):
        return self._scope_hierarchy_loader.export()

    def load_unit_export_symbols(self, *args):
        return self._unit_id_to_export_symbols_loader.load(*args)
    def save_unit_export_symbols(self, *args):
        return self._unit_id_to_export_symbols_loader.save(*args)

    def load_methods_in_class(self, *args):
        return self._class_id_to_methods_loader.load_key_to_values(*args)
    def save_methods_in_class(self, *args):
        return self._class_id_to_methods_loader.save(*args)

    def convert_stmt_id_to_call_stmt_format(self, stmt_id):
        return self._call_stmt_id_to_call_format_info_loader.load(stmt_id)
    def save_stmt_id_to_call_stmt_format(self, stmt_id, call_format_info):
        return self._call_stmt_id_to_call_format_info_loader.save(stmt_id, call_format_info)
    def load_all_call_stmt_id_to_call_format_info(self):
        return self._call_stmt_id_to_call_format_info_loader.load_all_call_stmt_id_to_call_format_info()

    def convert_method_id_to_method_decl_format(self, method_id):
        return self._method_id_to_method_decl_format_loader.load(method_id)
    def save_method_id_to_method_decl_format(self, method_id, method_decl_format):
        return self._method_id_to_method_decl_format_loader.save(method_id, method_decl_format)

    def convert_unit_id_to_stmt_ids(self, *args):
        return self._unit_id_to_stmt_id_loader.load_one_to_many(*args)
    def save_unit_id_to_stmt_ids(self, *args):
        return self._unit_id_to_stmt_id_loader.save(*args)
    def convert_stmt_id_to_unit_id(self, *args):
        return self._unit_id_to_stmt_id_loader.load(*args)
    def load_all_stmt_ids(self, *args):
        return self._unit_id_to_stmt_id_loader.load_all_stmt_ids(*args)
    def load_all_unit_ids(self, *args):
        return self._unit_id_to_stmt_id_loader.load_all_unit_ids(*args)

    def save_method_external_symbol_id_collection(self, *args):
        self._external_symbol_id_collection_loader.save_external_symbol_id_collection(*args)
    def load_method_external_symbol_id_collection(self, *args):
        return self._external_symbol_id_collection_loader.load_external_symbol_id_collection(*args)

    def convert_unit_id_to_variable_ids(self, *args):
        return self._unit_id_to_variable_id_loader.load_key_to_values(*args)
    def save_unit_id_to_variable_ids(self, *args):
        return self._unit_id_to_variable_id_loader.save(*args)
    def convert_variable_id_to_unit_id(self, *args):
        return self._unit_id_to_variable_id_loader.load_value_to_key(*args)
    def load_all_variable_ids(self, *args):
        return self._unit_id_to_variable_id_loader.load_all_values(*args)
    def is_variable_decl(self, *args):
        return self._unit_id_to_variable_id_loader.is_variable_decl(*args)

    def convert_unit_id_to_import_stmt_ids(self, *args):
        return self._unit_id_to_import_stmt_id_loader.load_key_to_values(*args)
    def save_unit_id_to_import_stmt_ids(self, *args):
        return self._unit_id_to_import_stmt_id_loader.save(*args)
    def convert_import_stmt_id_to_unit_id(self, *args):
        return self._unit_id_to_import_stmt_id_loader.load_value_to_key(*args)
    def load_all_import_stmt_ids(self, *args):
        return self._unit_id_to_import_stmt_id_loader.load_all_values(*args)
    def is_import_stmt(self, *args):
        return self._unit_id_to_import_stmt_id_loader.is_import_stmt(*args)

    def convert_method_id_to_parameter_ids(self, *args):
        return self._method_id_to_parameter_id_loader.load_key_to_values(*args)
    def convert_parameter_id_to_method_id(self, *args):
        return self._method_id_to_parameter_id_loader.load_value_to_key(*args)
    def save_method_id_to_parameter_ids(self, *args):
        return self._method_id_to_parameter_id_loader.save(*args)
    def is_parameter_decl(self, *args):
        return self._method_id_to_parameter_id_loader.is_parameter_decl(*args)
    def is_parameter_decl_of_method(self, *args):
        return self._method_id_to_parameter_id_loader.is_parameter_decl_of_method(*args)

    def convert_class_id_to_method_ids(self, *args):
        return self._class_id_to_method_id_loader.load_key_to_values(*args)
    def save_class_id_to_method_ids(self, *args):
        return self._class_id_to_method_id_loader.save(*args)
    def convert_method_id_to_class_id(self, *args):
        return self._class_id_to_method_id_loader.load_value_to_key(*args)
    def is_method_decl_of_class(self, *args):
        return self._class_id_to_method_id_loader.is_parameter_decl_of_method(*args)

    def save_class_id_to_members(self, class_id, class_members):
        return self._class_id_to_members_loader.save(class_id, class_members)
    def save_all_class_id_to_members(self, class_id_to_members):
        return self._class_id_to_members_loader.save_all(class_id_to_members)
    def load_class_id_to_members(self, class_id, create_if_not_exists = False):
        class_members_dm: DataModel = self._class_id_to_members_loader.load(class_id)
        if class_members_dm is None and create_if_not_exists:
            nil_members = {}
            self.save_class_id_to_members(class_id, nil_members)
            return nil_members
        if not util.is_empty(class_members_dm):
            class_members_df = class_members_dm.get_data()
            if not class_members_df.empty and hasattr(class_members_df, "members"):
                return class_members_df["members"].to_dict()        
        return {}
    def load_all_class_id_to_members(self):
        return self._class_id_to_members_loader.load_all()

    def convert_class_id_to_field_ids(self, *args):
        return self._class_id_to_field_id_loader.load_key_to_values(*args)
    def save_class_id_to_field_ids(self, *args):
        return self._class_id_to_field_id_loader.save(*args)
    def convert_field_id_to_class_id(self, *args):
        return self._class_id_to_field_id_loader.load_value_to_key(*args)
    def is_field_decl_of_class(self, *args):
        return self._class_id_to_field_id_loader.is_parameter_decl_of_method(*args)

    def convert_unit_id_to_method_ids(self, *args):
        return self._unit_id_to_method_id_loader.load_key_to_values(*args)
    def save_unit_id_to_method_ids(self, *args):
        return self._unit_id_to_method_id_loader.save(*args)
    def convert_method_id_to_unit_id(self, *args):
        return self._unit_id_to_method_id_loader.load_value_to_key(*args)
    def load_all_method_ids(self, *args):
        return self._unit_id_to_method_id_loader.load_all_values(*args)
    def is_method_decl(self, *args):
        return self._unit_id_to_method_id_loader.is_method_decl(*args)

    def convert_unit_id_to_class_ids(self, *args):
        return self._unit_id_to_class_id_loader.load_key_to_values(*args)
    def save_unit_id_to_class_ids(self, *args):
        return self._unit_id_to_class_id_loader.save(*args)
    def convert_class_id_to_unit_id(self, *args):
        return self._unit_id_to_class_id_loader.load_value_to_key(*args)
    def load_all_class_ids(self, *args):
        return self._unit_id_to_class_id_loader.load_all_values(*args)
    def is_class_decl(self, *args):
        return self._unit_id_to_class_id_loader.is_class_decl(*args)

    def convert_unit_id_to_namespace_ids(self, *args):
        return self._unit_id_to_namespace_id_loader.load_key_to_values(*args)
    def save_unit_id_to_namespace_ids(self, *args):
        return self._unit_id_to_namespace_id_loader.save(*args)
    def convert_namespace_id_to_unit_id(self, *args):
        return self._unit_id_to_namespace_id_loader.load_value_to_key(*args)
    def load_all_namespace_ids(self, *args):
        return self._unit_id_to_namespace_id_loader.load_all_values(*args)
    def is_namespace_decl(self, *args):
        return self._unit_id_to_namespace_id_loader.is_namespace_decl(*args)

    def convert_class_id_to_class_name(self, *args):
        return self._class_id_to_class_name_loader.load_key_to_values(*args)
    def convert_class_name_to_class_ids(self, *args):
        return self._class_id_to_class_name_loader.load_value_to_key(*args)
    def save_class_id_to_class_name(self, *args):
        return self._class_id_to_class_name_loader.save(*args)

    def convert_method_id_to_method_name(self, *args):
        return self._method_id_to_method_name_loader.load_key_to_values(*args)
    def convert_method_name_to_method_ids(self, *args):
        return self._method_id_to_method_name_loader.load_value_to_key(*args)
    def save_method_id_to_method_name(self, *args):
        return self._method_id_to_method_name_loader.save(*args)

    def save_unit_symbol_decl_summary(self, unit_id, summary):
        return self._unit_symbol_decl_summary_loader.save(unit_id, summary)
    def load_unit_symbol_decl_summary(self, unit_id):
        return self._unit_symbol_decl_summary_loader.load(unit_id)

    def save_max_gir_id(self, max_gir_id):
        return self._unique_symbol_id_assigner_loader.save_max_gir_id(max_gir_id)
    def load_max_gir_id(self):
        return self._unique_symbol_id_assigner_loader.load_max_gir_id()
    def is_greater_than_max_gir_id(self, symbol_id):
        return self._unique_symbol_id_assigner_loader.is_greater_than_max_gir_id(symbol_id)
    def assign_new_unique_positive_id(self):
        return self._unique_symbol_id_assigner_loader.assign_new_unique_positive_id()
    def assign_new_unique_negative_id(self):
        return self._unique_symbol_id_assigner_loader.assign_new_unique_negative_id()

    # def save_symbol_name_to_scope_ids(self, *args):
    #     return self._symbol_name_to_scope_ids_loader.save(*args)
    # def load_symbol_name_to_scope_ids(self, *args):
    #     return self._symbol_name_to_scope_ids_loader.load(*args)
    #
    # def save_scope_id_to_symbol_info(self, *args):
    #     return self._scope_id_to_symbol_info_loader.save(*args)
    # def load_scope_id_to_symbol_info(self, *args):
    #     return self._scope_id_to_symbol_info_loader.load(*args)
    #
    # def save_scope_id_to_available_scope_ids(self, *args):
    #     return self._scope_id_to_available_scope_ids_loader.save(*args)
    # def load_scope_id_to_available_scope_ids(self, *args):
    #     return self._scope_id_to_available_scope_ids_loader.load(*args)

    def save_entry_points(self, *args):
        return self._entry_points_loader.save(*args)
    def load_entry_points(self, *args):
        return self._entry_points_loader.load_entry_points(*args)
    def export_entry_points(self):
        return self._entry_points_loader.export()

    def load_method_cfg(self, *args):
        return self._cfg_loader.load(*args)
    def save_method_cfg(self, *args):
        return self._cfg_loader.save(*args)

    def save_symbol_bit_vector_p1(self, *args):
        return self._symbol_bit_vector_manager_p1_loader.save(*args)
    def load_symbol_bit_vector_p1(self, *args):
        return self._symbol_bit_vector_manager_p1_loader.load(*args)

    def save_symbol_bit_vector_p2(self, *args):
        return self._symbol_bit_vector_manager_p2_loader.save(*args)
    def load_symbol_bit_vector_p2(self, *args):
        return self._symbol_bit_vector_manager_p2_loader.load(*args)

    def save_symbol_bit_vector_p3(self, *args):
        return self._symbol_bit_vector_manager_p3_loader.save(*args)
    def load_symbol_bit_vector_p3(self, *args):
        return self._symbol_bit_vector_manager_p3_loader.load(*args)

    def save_state_bit_vector_p2(self, *args):
        return self._state_bit_vector_manager_p2_loader.save(*args)
    def load_state_bit_vector_p2(self, *args):
        return self._state_bit_vector_manager_p2_loader.load(*args)

    def save_state_bit_vector_p3(self, *args):
        return self._state_bit_vector_manager_p2_loader.save(*args)
    def load_state_bit_vector_p3(self, *args):
        return self._state_bit_vector_manager_p2_loader.load(*args)

    def save_stmt_status_p1(self, *args):
        return self._stmt_status_p1_loader.save(*args)
    def load_stmt_status_p1(self, *args):
        return self._stmt_status_p1_loader.load(*args)

    def save_stmt_status_p2(self, *args):
        return self._stmt_status_p2_loader.save(*args)
    def load_stmt_status_p2(self, *args):
        return self._stmt_status_p2_loader.load(*args)

    def save_stmt_status_p3(self, *args):
        return self._stmt_status_p3_loader.save(*args)
    def load_stmt_status_p3(self, *args):
        return self._stmt_status_p3_loader.load(*args)

    def save_symbol_state_space_p1(self, *args):
        return self._symbol_state_space_p1_loader.save(*args)
    def load_symbol_state_space_p1(self, *args):
        return self._symbol_state_space_p1_loader.load(*args)

    def save_symbol_state_space_p2(self, *args):
        return self._symbol_state_space_p2_loader.save(*args)
    def load_symbol_state_space_p2(self, *args):
        return self._symbol_state_space_p2_loader.load(*args)

    def save_symbol_state_space_summary_p2(self, *args):
        return self._symbol_state_space_summary_p2_loader.save(*args)
    def load_symbol_state_space_summary_p2(self, *args):
        return self._symbol_state_space_summary_p2_loader.load(*args)

    def save_symbol_state_space_p3(self, *args):
        return self._symbol_state_space_p3_loader.save(*args)
    def load_symbol_state_space_p3(self, *args):
        return self._symbol_state_space_p3_loader.load(*args)

    def save_symbol_state_space_summary_p3(self, *args):
        return self._symbol_state_space_summary_p3_loader.save(*args)
    def load_symbol_state_space_summary_p3(self, *args):
        return self._symbol_state_space_summary_p3_loader.load(*args)

    def save_method_internal_callees(self, *args):
        return self._method_internal_callees_loader.save(*args)
    def load_method_internal_callees(self, *args):
        return self._method_internal_callees_loader.load(*args)

    def save_grouped_methods(self, *args):
        return self._grouped_methods_loader.save(*args)
    def load_grouped_methods(self, *args):
        return self._grouped_methods_loader.load(*args)

    def save_import_graph(self, *args):
        return self._import_graph_loader.save(*args)
    def load_import_graph(self, *args):
        return self._import_graph_loader.load(*args)
    def save_import_graph_nodes(self, *args):
        return self._import_graph_loader.save_nodes(*args)
    def load_import_graph_nodes(self, *args):
        return self._import_graph_loader.load_nodes(*args)
    def save_import_deps(self, *args):
        return self._import_graph_loader.save_deps(*args)
    def load_import_deps(self, *args):
        return self._import_graph_loader.load_deps(*args)
    def get_internal_successor_nodes_in_import_graph(self, node_id):
        return self._import_graph_loader.get_internal_successor_nodes(node_id)
    def get_external_successor_nodes_in_import_graph(self, node_id):
        return self._import_graph_loader.get_external_successor_nodes(node_id)
    def get_edges_and_nodes_with_edge_attrs_in_import_graph(self, node_id, attr_dict):
        return self._import_graph_loader.get_edges_and_nodes_with_edge_attrs(node_id, attr_dict)

    def save_type_graph(self, *args):
        return self._type_graph_loader.save(*args)
    def load_type_graph(self, *args):
        return self._type_graph_loader.load(*args)

    def save_call_graph_p1(self, *args):
        return self._call_graph_p1_loader.save(*args)
    def load_call_graph_p1(self, *args):
        return self._call_graph_p1_loader.load(*args)

    def save_call_graph_p2(self, *args):
        return self._call_graph_p2_loader.save(*args)
    def load_call_graph_p2(self, *args):
        return self._call_graph_p2_loader.load(*args)

    def save_call_paths_p3(self, *args):
        return self._call_path_p3_loader.save(*args)
    def load_call_paths_p3(self, *args):
        return self._call_path_p3_loader.load(*args)

    def load_method_symbol_to_define(self, *args):
        return self._symbol_to_define_loader.load(*args)
    def save_method_symbol_to_define(self, *args):
        return self._symbol_to_define_loader.save(*args)

    def load_method_symbol_to_define_p2(self, *args):
        return self._symbol_to_define_p2_loader.load(*args)
    def save_method_symbol_to_define_p2(self, *args):
        return self._symbol_to_define_p2_loader.save(*args)

    def load_method_symbol_to_define_p3(self, *args):
        return self._symbol_to_define_p3_loader.load(*args)
    def save_method_symbol_to_define_p3(self, *args):
        return self._symbol_to_define_p3_loader.save(*args)

    def load_method_state_to_define_p1(self, *args):
        return self._state_to_define_p1_loader.load(*args)
    def save_method_state_to_define_p1(self, *args):
        return self._state_to_define_p1_loader.save(*args)

    def load_method_state_to_define_p2(self, *args):
        return self._state_to_define_p2_loader.load(*args)
    def save_method_state_to_define_p2(self, *args):
        return self._state_to_define_p2_loader.save(*args)

    def load_method_symbol_to_use(self, *args):
        return self._symbol_to_use_loader.load(*args)
    def save_method_symbol_to_use(self, *args):
        return self._symbol_to_use_loader.save(*args)

    def load_method_symbol_graph_p2(self, *args):
        return self._symbol_graph_p2_loader.load(*args)
    def save_method_symbol_graph_p2(self, *args):
        return self._symbol_graph_p2_loader.save(*args)
    def save_method_symbol_graph_p3(self, *args):
        return self._symbol_graph_p3_loader.save(*args)

    def load_method_def_use_summary(self, *args):
        return self._method_def_use_summary_loader.load(*args)
    def save_method_def_use_summary(self, *args):
        return self._method_def_use_summary_loader.save(*args)

    def load_method_summary_template(self, *args):
        return self._method_summary_template_loader.load(*args)
    def save_method_summary_template(self, *args):
        return self._method_summary_template_loader.save(*args)

    def load_method_summary_instance(self, *args):
        return self._method_summary_template_instance.load(*args)
    def save_method_summary_instance(self, *args):
        return self._method_summary_template_instance.save(*args)

    def load_parameter_mapping_p2(self, *args):
        return self._callee_parameter_mapping_p2_loader.load(*args)
    def save_parameter_mapping_p2(self, *args):
        return self._callee_parameter_mapping_p2_loader.save(*args)

    def load_parameter_mapping_p3(self, *args):
        return self._callee_parameter_mapping_p3_loader.load(*args)
    def save_parameter_mapping_p3(self, *args):
        return self._callee_parameter_mapping_p3_loader.save(*args)

    def convert_stmt_id_to_method_id(self, stmt_id):
        unit_id = self.convert_stmt_id_to_unit_id(stmt_id)
        unit_gir = self.load_unit_gir(unit_id)
        stmt_id_to_stmt = {}
        for row in unit_gir:
            stmt_id_to_stmt[row.stmt_id] = row

        current_stmt = stmt_id_to_stmt.get(stmt_id)
        while current_stmt and current_stmt.operation != 'method_decl':
            parent_stmt_id = current_stmt.parent_stmt_id
            current_stmt = stmt_id_to_stmt.get(parent_stmt_id)

        return current_stmt.stmt_id

    def get_method_name_by_method_id(self, stmt_id):
        method_name = self.convert_method_id_to_method_name(stmt_id)
        class_id = self.convert_method_id_to_class_id(stmt_id)
        class_name = self.convert_class_id_to_class_name(class_id)
        if class_name:
            return f"{class_name}.{method_name}"
        else:
            return method_name

    def get_stmt_source_code(self, lines, stmt):
        """极速版获取stmt的source_code"""
        stmt_start_line = 0
        stmt_end_line = -1
        stmt_start_line = int(stmt.start_row)
        stmt_end_line = int(stmt.end_row) + 1

        stmt_source_code = []
        if stmt_end_line > 0 and stmt_end_line < len(lines):
            stmt_source_code = lines[stmt_start_line: stmt_end_line]
        else:
            stmt_source_code = lines[stmt_start_line:]
        return stmt_source_code
    
    def get_stmt_source_code_with_comment(self, stmt_id):
        """获取stmt的source_code，并添加注释"""
        unit_id = self.convert_stmt_id_to_unit_id(stmt_id)
        unit_info = self.convert_module_id_to_module_info(unit_id)
        unit_path = unit_info.original_path
        with open(unit_path, 'r') as f:
            lines = f.readlines()
        lines = [line.rstrip() for line in lines]
        stmt = self.convert_stmt_id_to_stmt(stmt_id)
        return self.get_stmt_source_code(lines, stmt)
    
    def convert_stmt_id_to_stmt(self, stmt_id):
        unit_id = self.convert_stmt_id_to_unit_id(stmt_id)
        unit_gir = self.load_unit_gir(unit_id)
        stmt_id_to_stmt = {}
        for row in unit_gir:
            stmt_id_to_stmt[row.stmt_id] = row
        return stmt_id_to_stmt.get(stmt_id)
        
        

    def get_stmt_parent_method_source_code(self, stmt_id):
        # python文件行号从一开始，tree-sitter从0开始
        unit_id = self.convert_stmt_id_to_unit_id(stmt_id)
        unit_gir = self.load_unit_gir(unit_id)
        stmt_id_to_stmt = {}
        for row in unit_gir:
            stmt_id_to_stmt[row.stmt_id] = row

        current_stmt = stmt_id_to_stmt.get(stmt_id)
        while current_stmt and current_stmt.operation != 'method_decl':
            parent_stmt_id = current_stmt.parent_stmt_id
            current_stmt = stmt_id_to_stmt.get(parent_stmt_id)

        unit_info = self.convert_module_id_to_module_info(unit_id)
        lang_name = unit_info.lang
        unit_path = unit_info.original_path

        with open(unit_path, 'r') as f:
            lines = f.readlines()
        lines = [line.rstrip() for line in lines]

        if current_stmt.name == "%unit_init" or current_stmt.name == "%class_sinit":
            block_start_stmt_id = current_stmt.stmt_id + 1
            stmts = []
            for id, stmt in stmt_id_to_stmt.items():
                if stmt.parent_stmt_id == block_start_stmt_id:
                    stmts.append(stmt)
            code_with_comment = []
            for stmt in stmts:
                code_with_comment.extend(self.get_stmt_source_code(lines, stmt))
            return code_with_comment

        method_start_line = 0
        method_end_line = -1
        if current_stmt:
            print(current_stmt)
            method_start_line = int(current_stmt.start_row)
            method_end_line = int(current_stmt.end_row) + 1
        method_start_line = method_start_line - 1
        if method_start_line > 0:
            method_start_line = util.determine_comment_line(lang_name, method_start_line, lines)
        else:
            method_start_line = 0

        code_with_comment = []
        if method_end_line > 0 and method_end_line < len(lines):
            code_with_comment = lines[method_start_line: method_end_line]
        else:
            code_with_comment = lines[method_start_line:]
        return code_with_comment

    def print_context_info_for_debug(self, stmt_id, method_id):
        unit_id = self.convert_stmt_id_to_unit_id(stmt_id)
        unit_path = self.convert_unit_id_to_unit_path(unit_id)
        method_name = self.convert_method_id_to_method_name(method_id)
        class_id = self.convert_method_id_to_class_id(method_id)
        class_name = self.convert_class_id_to_class_name(class_id)
        if util.is_empty(class_name):
            class_name = "None"
        gir_stmt = self.load_stmt_gir(stmt_id)

        context = {
            'unit_path': unit_path,
            'class_name': class_name,
            'method_name': method_name,
        }
        pprint.pprint(context, indent=2, width=80)








