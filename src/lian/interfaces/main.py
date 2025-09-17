#!/usr/bin/env python3
import os
import sys
############################################################
# Initliaze the configuration
############################################################
# Support empty  
import builtins

try:
    builtins.profile
except AttributeError:
    def profile(func):
        return func
    builtins.profile = profile
# Disable copy
import pandas as pd
pd.options.mode.copy_on_write = False

# Init path
sys.path.append(os.path.realpath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))))

############################################################
# Essential content
############################################################
from lian.interfaces import (
    preparation,
    args_parser
)

from lian.config import constants, config
from lian.apps.app_manager import AppManager
from lian.config import config, constants, lang_config
from lian.util import util
from lian.util.loader import Loader
from lian.lang.lang_analysis import LangAnalysis
from lian.semantic.basic_analysis.basic_analysis import BasicSemanticAnalysis
from lian.semantic.summary_analysis.summary_generation import SemanticSummaryGeneration
from lian.semantic.global_analysis.global_analysis import GlobalAnalysis
from lian.semantic.resolver import Resolver

class Lian:
    def __init__(self):
        self.options = None
        self.app_manager = None
        self.loader = None
        self.extern_system = None
        self.resolver = None
        self.lang_table = lang_config.LANG_TABLE
        self.command_handler = {
            "lang":         self.lang_analysis,
            "semantic":     self.semantic_analysis,
            "security":     self.security_analysis,
            "run":          self.run_all,
        }

        self.set_workspace_dir_flag = False

        self.args_parser = args_parser.ArgsParser()
        self.options = self.args_parser.obtain_default_options()

    def parse_cmds(self, **custom_options):
        self.options = self.args_parser.init().parse_cmds()

        if util.is_available(custom_options):
            if isinstance(self.options, dict):
                for key, value in custom_options.items():
                    if key in self.options:
                        self.options[key] = value
            else:
                for key, value in custom_options.items():
                    if hasattr(self.options, key):
                        setattr(self.options, key, value)

        return self

    def set_workspace_dir(self, default_workspace_dir = config.DEFAULT_WORKSPACE):
        self.set_workspace_dir_flag = True
        if default_workspace_dir not in self.options.workspace:
            self.options.workspace = os.path.join(self.options.workspace, default_workspace_dir)
        self.options.default_workspace_dir = default_workspace_dir
        return self

    def update_lang_config(self):
        lang_config.update_lang_extensions(self.lang_table, self.options.lang)

        file_extensions = []
        for lang in self.options.lang:
            file_extensions.extend(lang_config.LANG_EXTENSIONS.get(lang, []))
        self.options.lang_extensions = file_extensions

    def init_submodules(self, other_init = None):
        # Analyze options
        config.DEBUG_FLAG = self.options.debug
        if self.options.debug:
            util.debug(self.options)

        if not self.set_workspace_dir_flag:
            self.set_workspace_dir()

        # update lang config & options.lang_extensions
        self.update_lang_config()

        # Set up the analysis environment
        if hasattr(self.options, "extern_path") and self.options.extern_path:
            sys.path.append(self.options.extern_path)  # 添加绝对路径
            from externs.extern_system import ExternSystem
        else:
            from lian.externs.extern_system import ExternSystem
        self.app_manager = AppManager(self.options)
        self.loader = Loader(self.options, self.app_manager)
        self.resolver = Resolver(self.options, self.app_manager, self.loader)
        self.extern_system = ExternSystem(self.options, self.loader, self.resolver)
        self.app_manager.register_extern_system(self.extern_system)
        # prepare folders and unit info tables
        preparation.run(self.options, self.loader)
        if not self.options.noextern:
            self.extern_system.init()

        if util.is_available(other_init):
            other_init(self)

        return self

    def add_lang(self,lang, extension, so_path, parser):
        self.lang_table.append(
            lang_config.LangConfig(
                name = lang, extension = extension, so_path = so_path, parser = parser
            )
        )

    # app path -> options -> app_manager -> load app from the path (importlib) -> register app
    def dispatch_command(self):
        handler = self.command_handler.get(self.options.sub_command)
        if not handler:
            util.error_and_quit(f"Failed to find command \"{self.options.sub_command}\"")
        return handler()

    def lang_analysis(self):
        LangAnalysis(self).run()
        self.loader.export()
        return self

    def semantic_analysis(self):
        if self.options.debug:
            util.debug("\n\t###########  # Semantic Analysis #  ###########")

        BasicSemanticAnalysis(self).run()
        summary_generation = SemanticSummaryGeneration(self)
        summary_generation.run()
        print(summary_generation.analyzed_method_list)
        GlobalAnalysis(self, summary_generation.analyzed_method_list).run()
        self.loader.export()
        return self

    def security_analysis(self):
        pass

    def run_all(self):
        self.lang_analysis()
        self.semantic_analysis()
        return self

    def run(self):
        self.parse_cmds().init_submodules().dispatch_command()

        return self

def main():
    Lian().run()

if __name__ == "__main__":
    main()
