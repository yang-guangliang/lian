#!/usr/bin/env python3
import os
import sys
import dataclasses
from tqdm import tqdm
############################################################
# Initliaze the configuration
############################################################
# Support empty @profile
import builtins

# from lian.safe_compiler.compiler import SafeCompiler

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
from lian.config import config, constants
from lian.util import util
from lian.util.loader import Loader
from lian.lang.gir_parser import GLangParser
from lian.semantic.basic_analysis import BasicSemanticAnalysis
from lian.semantic.summary_generation import SemanticSummaryGeneration
from lian.semantic.global_analysis import GlobalAnalysis
from lian.semantic.resolver import Resolver
from lian.semantic.entry_points import EntryPointGenerator
from lian.semantic import semantic_structure
from lian.incremental.unit_level_checker import UnitLevelChecker

class GeneralAnalysis:
    def __init__(self, options, apps, loader, extern_system = None):
        self.options = options
        self.apps: AppManager = apps
        self.loader: Loader = loader
        self.extern_system: ExternSystem = extern_system

class LangAnalysis(GeneralAnalysis):
    def init_start_stmt_id(self):
        symbol_table = self.loader.load_module_symbol_table()
        result = len(symbol_table)
        remainder = len(symbol_table) % 10
        result += 10 - remainder
        if remainder < 5:
            return result
        return result + 10

    def adjust_node_id(self, node_id):
        # remainder = node_id % 10
        # if remainder != 0:
        #     node_id += (10 - remainder)
        return node_id + config.MIN_ID_INTERVAL

    def run(self):
        if self.options.debug:
            util.debug("\n\t###########  # Language Parsing #  ###########")

        gir_parser = GLangParser(
            self.options,
            self.apps,
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

        unit_level_checker = UnitLevelChecker.unit_level_checker()
        new_units = []
        for unit_info in all_units:

            incremental_lazy_flag = False
            if self.options.incremental:
                current_node_id, previous_results = unit_level_checker.previous_lang_analysis_results(unit_info, current_node_id)#
                if previous_results:
                    # util.debug(current_node_id)
                    # if self.options.debug:
                    #     util.debug("Incremental: Previous result found")
                    gir_parser.add_unit_gir(unit_info, previous_results)
                    current_node_id = self.adjust_node_id(current_node_id)
                    incremental_lazy_flag = True
            if not incremental_lazy_flag:
                # util.debug("main not found:",unit_info.module_id)
                new_units.append(unit_info)
            #util.debug(current_node_id)

        for unit_info in tqdm(new_units):
            current_node_id, gir_ir = gir_parser.deal_with_file_unit(
                current_node_id, unit_info.unit_path
            )
            gir_parser.add_unit_gir(unit_info, gir_ir)
            current_node_id = self.adjust_node_id(current_node_id)
            #util.debug(current_node_id)
            # if self.options.debug:
            #     gir_parser.export()
        util.debug(len(all_units), len(new_units))
        gir_parser.export()
        self.loader.export()

class SemanticAnalysis(GeneralAnalysis):
    def run(self):
        if self.options.debug:
            util.debug("\n\t###########  # Semantic Analysis #  ###########")

        incremental_checker = UnitLevelChecker.unit_level_checker()
        resolver = Resolver(self.options, self.apps, self.loader)
        BasicSemanticAnalysis(self.options, self.apps, self.loader, resolver, incremental_checker, self.extern_system).run()
        SemanticSummaryGeneration(self.options, self.apps, self.loader, resolver).run()
        GlobalAnalysis(self.options, self.apps, self.loader, resolver).run()

        self.loader.export()

class SecurityAnalysis(GeneralAnalysis):
    def run(self):
        # if self.options.debug:
        #     util.debug("###########  # Security Analysis #  ###########")
        pass

class SafeLangCompiler(GeneralAnalysis):
    def run(self):
        if self.options.debug:
            util.debug("\n\t###########  # Safe Language Compiler #  ###########")

        resolver = Resolver(self.options, self.apps, self.loader)
        BasicSemanticAnalysis(self.options, self.apps, self.loader, resolver, self.extern_system).run()
        SafeCompiler(self.options, self.apps, self.loader, resolver).run()

        self.loader.export()

class Lian:
    def __init__(self):
        self.options = None
        self.app_manager = None
        self.loader = None
        self.extern_system = None
        # self.incremental_checker = None
        self.command_handler = {
            "lang":         self.lang_command,
            "semantic":     self.semantic_command,
            "security":     self.security_command,
            "run":          self.run_command,
            "safe":         self.safe_compiler_command,
        }

    def init(self):
        # Analyze options
        self.options = args_parser.ArgParser().parse()
        config.DEBUG_FLAG = self.options.debug
        if self.options.debug:
            util.debug(self.options)

        # Set up the analysis environment
        self.app_manager = AppManager(self.options)
        self.loader = Loader(self.options, self.app_manager)
        self.extern_system = ExternSystem(self.options, self.loader)
        self.app_manager.register_extern_system(self.extern_system)
        preparation.run(self.options, self.loader)

        UnitLevelChecker.init(self.options, self.app_manager, self.loader)
        self.extern_system.init()
        return self

    # app path -> options -> app_manager -> load app from the path (importlib) -> register app
    def run(self):
        handler = self.command_handler.get(self.options.sub_command)
        if not handler:
            util.error_and_quit(f"Failed to find command \"{self.options.sub_command}\"")
        handler()

    def lang_command(self):
        LangAnalysis(options = self.options, apps = self.app_manager, loader = self.loader).run()

    def semantic_command(self):
        SemanticAnalysis(options = self.options, apps = self.app_manager, loader = self.loader, extern_system = self.extern_system).run()

    def security_command(self):
        SecurityAnalysis(options = self.options, apps = self.app_manager, loader = self.loader, extern_system = self.extern_system).run()

    def run_command(self):
        self.lang_command()
        self.semantic_command()
        self.security_command()

    def safe_compiler_command(self):
        SafeLangCompiler(options = self.options, apps = self.app_manager, loader = self.loader, extern_system = self.extern_system).run()


def main():
    Lian().init().run()

if __name__ == "__main__":
    main()
