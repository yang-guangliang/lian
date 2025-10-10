from lian.util.loader import Loader
import os
from lian.config import config
from lian.util import util
import copy
from lian.semantic.semantic_structs import Scope


class UnitLevelIncrementalChecker:

    _instance = None

    def __init__(self, options, app_manager, current_loader):
        self.options = copy.deepcopy(options)
        workspace_path = self.options.workspace
        self.current_loader = current_loader
        self.bak_path = os.path.join(workspace_path, config.BACKUP_DIR)
        self.options.workspace = self.bak_path
        self.app_manager = app_manager
        self.bak_loader = Loader(self.options, self.app_manager)

        self.bak_loader.restore()
        self.module_symbol_backup = self.bak_loader.load_module_symbol_table()

        self.max_stmt_id = -1

    # singleton pattern
    @classmethod
    def init(cls, options, app_manager, current_loader):
        cls._instance = UnitLevelIncrementalChecker(options, app_manager, current_loader)
    @classmethod
    def unit_level_incremental_checker(cls):
        if cls._instance is None:
            util.error_and_quit("Accessing a nonexistent incremental checker instance")
        # util.debug("Singleton called")
        return cls._instance


    def revive_data_from_dict(self, data, Classname):
        empty_object = Classname()
        return empty_object.from_dict(data)

    def revive_data_from_dict_list(self, dict_list, Classname):
        result = []
        for item in dict_list:
            result.append(self.revive_data_from_dict(item, Classname))
        return result

    def check_unit_id_analyzed(self, unit_id):
        unit_info = self.current_loader.convert_module_id_to_module_info(unit_id)
        return self.check_unit_analyzed(unit_info)

    def check_unit_analyzed(self, unit_info):
        if not self.module_symbol_backup:
            # util.error_and_quit("backup not loaded")
            return None
        unit_hash = unit_info.hash
        bak_unit_entry = self.module_symbol_backup.query(self.module_symbol_backup.hash == unit_hash)
        # util.debug(unit_hash)
        if len(bak_unit_entry) == 0:
            return None
        previous_uid = bak_unit_entry.access(0, column_name="module_id")
        # util.warn(unit_info.module_id, previous_uid)
        return previous_uid

    def fetch_gir(self, previous_uid, current_node_id):
        unit_gir_df = self.bak_loader.load_unit_gir(previous_uid)
        if not unit_gir_df:
            return current_node_id, None
        if len(unit_gir_df) == 0:
            return current_node_id, None
        unit_gir_df.modify_column("unit_id", None)
        unit_gir_list = unit_gir_df.convert_to_dict_list()
        for stmt in unit_gir_list:
            self.max_stmt_id = max(self.max_stmt_id, stmt["stmt_id"])
        return self.max_stmt_id + 1, unit_gir_list

    def fetch_scope(self, previous_uid):
        scope_pack = {}
        # scope_pack["stmt_ids"] = self.bak_loader.convert_unit_id_to_stmt_ids(previous_uid)
        scope_pack["method_stmt_ids"] = self.bak_loader.convert_unit_id_to_method_ids(previous_uid)
        scope_pack["class_stmt_ids"] = self.bak_loader.convert_unit_id_to_class_ids(previous_uid)
        scope_pack["namespace_stmt_ids"] = self.bak_loader.convert_unit_id_to_namespace_ids(previous_uid)
        scope_pack["variable_ids"] = self.bak_loader.find_variable_ids_by_unit_id(previous_uid)
        scope_pack["import_stmt_ids"] = self.bak_loader.convert_unit_id_to_import_stmt_ids(previous_uid)

        method_id_to_method_name = {}
        method_id_to_parameter_ids = {}
        method_stmt_ids = scope_pack["method_stmt_ids"]
        for stmt_id in method_stmt_ids:
            method_id_to_method_name[stmt_id] = self.bak_loader.convert_method_id_to_method_name(stmt_id)
            method_id_to_parameter_ids[stmt_id] = self.bak_loader.convert_method_id_to_parameter_ids(stmt_id)

        class_id_to_class_name = {}
        class_id_to_class_method_ids = {}
        class_id_to_class_field_ids = {}
        class_stmt_ids = scope_pack["class_stmt_ids"]
        for stmt_id in class_stmt_ids:
            class_id_to_class_name[stmt_id] = self.bak_loader.convert_class_id_to_class_name(stmt_id)
            class_id_to_class_method_ids[stmt_id] = self.bak_loader.convert_class_id_to_method_ids(stmt_id)
            class_id_to_class_field_ids[stmt_id] = self.bak_loader.convert_class_id_to_field_ids(stmt_id)

        scope_pack["method_id_to_method_name"] = method_id_to_method_name
        scope_pack["method_id_to_parameter_ids"] = method_id_to_parameter_ids
        scope_pack["class_id_to_class_name"] = class_id_to_class_name
        scope_pack["class_id_to_class_method_ids"] = class_id_to_class_method_ids
        scope_pack["class_id_to_class_field_ids"] = class_id_to_class_field_ids

        scope_space_df = self.bak_loader.load_unit_scope_hierarchy(previous_uid)
        scope_space_list = scope_space_df.convert_to_dict_list()
        scope_pack["scope_space"] = self.revive_data_from_dict_list(scope_space_list, Scope)

        scope_pack["unit_symbol_decl_summary"] = self.bak_loader.load_unit_symbol_decl_summary(previous_uid)
        return scope_pack

    def fetch_cfg(self, method_id):
        return self.bak_loader.load_method_cfg(method_id)

    def previous_lang_analysis_results(self, unit_info, current_node_id):
        # util.debug("inc:", unit_info.module_id)
        previous_uid = self.check_unit_analyzed(unit_info)
        if not previous_uid:
            return current_node_id, None
        else:
            return self.fetch_gir(previous_uid, current_node_id)

    def previous_scope_hierarchy_analysis_results(self, unit_info):
        previous_uid = self.check_unit_analyzed(unit_info)
        if not previous_uid:
            return None
        else:
            return self.fetch_scope(previous_uid)
