#!/usr/bin/env python3
import os,sys

import config.config as config
sys.path.extend([config.LIAN_DIR, config.ANALYZER_DIR])
print(sys.path)
 
from lian.interfaces.main import Lian
from lian.interfaces.args_parser import ArgsParser
# from lian.lang.lang_analysis  import LangAnalysis
from lian.semantic.basic_analysis import BasicSemanticAnalysis
from lian.semantic.scope_hierarchy import ImportGraphTranslatorToUnitLevel
from lian.config.constants import SymbolOrState
from frontend.abc_parser import ABCParser

class AnalyzerArgsParser(ArgsParser):
    def init(self):
        # Create the top-level parser
        subparsers = self.main_parser.add_subparsers(dest='sub_command')
        # Create the parser for the "lang" command
        parser_compile = subparsers.add_parser('Analyzer', help="run Analyzer")

        parser_run = subparsers.add_parser('run', help='Run the Analyzer')

        for parser in [parser_compile, parser_run]:
            parser.add_argument('in_path', nargs='+', type=str, help='the input')
            parser.add_argument('-w', "--workspace", default=config.DEFAULT_WORKSPACE, type=str, help='the workspace directory (default:lian_workspace)')
            parser.add_argument("-f", "--force", action="store_true", help="Enable the FORCE mode for rewritting the workspace directory")
            parser.add_argument("-d", "--debug", action="store_true", help="Enable the DEBUG mode")
            parser.add_argument("-c", "--cores", default=1, help="Configure the available CPU cores")

        return self

    def set_analyzer_default_options(self):
        self.options.lang       = config.LANG_NAME
        self.options.workspace  = config.DEFAULT_WORKSPACE,
        return self



class Analyzer:
    def __init__(self):
        self.lian = Lian()
        self.unit_id_to_unit_info = {}
        self.analyzer_loader = None

    def init_analyzer(self):
        analyzer_out_path = os.path.join(self.lian.options.workspace, config.OUT_DIR)
        self.lian.options.compiler_out_path = analyzer_out_path
        os.makedirs(analyzer_out_path, exist_ok=True)

        unit_headers = os.path.join(analyzer_out_path, config.UNIT_HEADERS)
        self.lian.options.unit_headers = unit_headers
        os.makedirs(unit_headers, exist_ok=True)

        generics_results = os.path.join(analyzer_out_path, config.GENERICS_RESULTS)
        self.lian.options.generics_results = generics_results
        os.makedirs(generics_results, exist_ok=True)

        bin_dir = os.path.join(analyzer_out_path, config.BIN_DIR)
        self.lian.options.bin_dir = bin_dir
        os.makedirs(bin_dir, exist_ok=True)

        # self.analyzer_loader = AnalyzerLoader(self.lian)




    def lang_analysis(self):
        self.lian = Lian()
        self.lian.add_lang(config.LANG_NAME, config.LANG_EXTENSION, config.LANG_SO_PATH, ABCParser)
        self.lian.options = AnalyzerArgsParser().init().set_analyzer_default_options().parse_cmds()
        self.lian.init_submodules()
        # self.init_analyzer()
        self.lian.run()

    def run(self):
        self.lang_analysis()

def main():
    Analyzer().run()

if __name__ == "__main__":
    main()
