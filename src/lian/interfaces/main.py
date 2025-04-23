#!/usr/bin/env python3
import os
import sys
############################################################
# Initliaze the configuration
############################################################
# Support empty @profile
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
from lian.externs.extern_system import ExternSystem
from lian.config import constants, config
from lian.apps.app_manager import AppManager
from lian.config import config, constants, lang_config
from lian.util import util
from lian.util.loader import Loader
from lian.lang.lang_analysis import LangAnalysis
from lian.semantic.basic_analysis import BasicSemanticAnalysis
from lian.semantic.summary_generation import SemanticSummaryGeneration
from lian.semantic.global_analysis import GlobalAnalysis
from lian.semantic.resolver import Resolver
from lian.semantic.entry_points import EntryPointGenerator
from lian.semantic import semantic_structure

class Lian:
    def __init__(self):
        self.options = None
        self.app_manager = None
        self.loader = None
        self.extern_system = None
        self.resolver = None
        self.lang_table = lang_config.LANG_TABLE
        self.command_handler = {
            "lang":         self.lang_command,
            "semantic":     self.semantic_command,
            "security":     self.security_command,
            "run":          self.run_command,
        }

        self.args_parser = args_parser.ArgsParser()
        self.options = self.args_parser.obtain_default_options()

    def parse_cmds(self):
        self.options = self.args_parser.init().parse_cmds()
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

        # update lang config & options.lang_extensions
        self.update_lang_config()

        # Set up the analysis environment
        self.app_manager = AppManager(self.options)
        self.loader = Loader(self.options, self.app_manager)
        self.resolver = Resolver(self.options, self.app_manager, self.loader)
        self.extern_system = ExternSystem(self.options, self.loader)
        self.app_manager.register_extern_system(self.extern_system)
        # prepare folders and unit info tables
        preparation.run(self.options, self.loader)
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
    def run(self):
        handler = self.command_handler.get(self.options.sub_command)
        if not handler:
            util.error_and_quit(f"Failed to find command \"{self.options.sub_command}\"")
        handler()

    def lang_command(self):
        LangAnalysis(self).run()

    def semantic_command(self):
        if self.options.debug:
            util.debug("\n\t###########  # Semantic Analysis #  ###########")

        BasicSemanticAnalysis(self).run()
        SemanticSummaryGeneration(self).run()
        GlobalAnalysis(self).run()

        self.loader.export()

    def security_command(self):
        SecurityAnalysis(self).run()

    def run_command(self):
        self.lang_command()
        self.semantic_command()
        #self.security_command()

def main():
    Lian().parse_cmds().init_submodules().run()

if __name__ == "__main__":
    main()
