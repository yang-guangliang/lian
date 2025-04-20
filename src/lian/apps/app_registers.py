#!/usr/bin/env python3

from lian.apps.default_apps import (
    basic,
    js_handlers,
    init_new_file_and_object
)
from lian.apps.app_template import (
    AppSummary,
    EventHandler
)
from lian.config.constants import (
    EventKind,
    LianInternal,
)
from lian.config import config

class DefaultApp(AppSummary):
    def enable(self):
        self.app_manager.register_list([
            EventHandler(
                event = EventKind.MOCK_SOURCE_CODE_READY,
                handler = basic.replace_percent_symbol_in_mock,
                langs = [config.ANY_LANG]
            ),

            EventHandler(
                event = EventKind.ORIGINAL_SOURCE_CODE_READY,
                handler = basic.preprocess_llvm_float_value,
                langs = ["llvm"]
            ),

            EventHandler(
                event = EventKind.ORIGINAL_SOURCE_CODE_READY,
                handler = basic.preprocess_python_import_statements,
                langs = ["python"]
            ),

            EventHandler(
                event = EventKind.ORIGINAL_SOURCE_CODE_READY,
                handler = basic.remove_php_comments,
                langs = ["php"]
            ),

            EventHandler(
                event = EventKind.ORIGINAL_SOURCE_CODE_READY,
                handler = basic.preprocess_php_namespace,
                langs = ["php"]
            ),

            EventHandler(
                event = EventKind.ORIGINAL_SOURCE_CODE_READY,
                handler = basic.preprocess_php_namespace_2,
                langs = ["php"]
            ),
            EventHandler(
                event = EventKind.ORIGINAL_SOURCE_CODE_READY,
                handler = basic.preprocess_abc_loop,
                langs = ["abc"]
            ),
            EventHandler(
                event = EventKind.UNFLATTENED_GIR_LIST_GENERATED,
                handler = basic.unify_this,
                langs = [
                    "javascript",
                    "php",
                    "java"
                    # "llvm"
                ]
            ),

            EventHandler(
                event = EventKind.UNFLATTENED_GIR_LIST_GENERATED,
                handler = basic.unify_python_self,
                langs = ["python"]
            ),

            EventHandler(
                event = EventKind.UNFLATTENED_GIR_LIST_GENERATED,
                handler = basic.adjust_variable_decls,
                langs = [
                    "python",
                    "javascript",
                    "php",
                    "abc",
                    "yian"
                    # "llvm"
                ]
            ),

            EventHandler(
                event = EventKind.GIR_LIST_GENERATED,
                handler = basic.remove_unnecessary_tmp_variables,
                langs = [config.ANY_LANG]
            ),

            EventHandler(
                event = EventKind.GIR_LIST_GENERATED,
                handler = basic.add_main_func,
                langs = [
                    "python",
                    "javascript",
                    "c",
                    "php",
                    "typescript",
                    "arkts",
                    "yian"
                ]
            ),

            # EventHandler(
            #     event = EventKind.GIR_LIST_GENERATED,
            #     handler = basic.unify_data_type,
            #     langs = [config.ANY_LANG]
            # ),

            EventHandler(
                event = EventKind.P2STATE_FIELD_READ_BEFORE,
                handler = js_handlers.field_read_prototype,
                langs = ["javascript"]
            ),

            # EventHandler(
            #     event = EventKind.P2STATE_FIELD_READ_AFTER,
            #     handler = js_handlers.field_read_prototype,
            #     langs = ["javascript"]
            # ),

            EventHandler(
                event = EventKind.P2STATE_GENERATE_EXTERNAL_STATES,
                handler = js_handlers.method_decl_prototype,
                langs = ["javascript"]
            ),

            EventHandler(
                event = EventKind.P2STATE_NEW_OBJECT_BEFORE,
                handler = init_new_file_and_object.init_new_object,
                langs = [config.ANY_LANG]
            ),

            EventHandler(
                event = EventKind.P2STATE_NEW_OBJECT_BEFORE,
                handler = js_handlers.new_object_proto,
                langs = ["javascript"]
            ),

            EventHandler(
                event = EventKind.P2STATE_NEW_OBJECT_AFTER,
                handler = init_new_file_and_object.apply_constructor_summary,
                langs = [config.ANY_LANG]
            ),
        ])

