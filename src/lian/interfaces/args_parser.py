#!/usr/bin/env python3

import sys
import argparse
import types
from lian.config import constants, config
LANG_EXTENSIONS = constants.LANG_EXTENSIONS

class ArgParser:
    def __init__(self):
        self.main_parser = None
        self.options = None
        self.init()

    def init(self):
        # Create the top-level parser
        self.main_parser = argparse.ArgumentParser()
        subparsers = self.main_parser.add_subparsers(dest='sub_command')
        # Create the parser for the "lang" command
        parser_lang = subparsers.add_parser('lang', help="Parse code to General IR")
        parser_semantic = subparsers.add_parser('semantic', help='Perform semantic analysis')
        parser_security = subparsers.add_parser('security', help='Conduct security analysis')
        parser_run = subparsers.add_parser('run', help='Run end-to-end analysis')
        parser_safe = subparsers.add_parser('safe', help='Compile safe-lang files')

        # Add the arguments to the main parser
        for parser in [parser_lang, parser_semantic, parser_security, parser_run]:
            parser.add_argument("-b", "--benchmark", action="store_true")
            # parser.add_argument("-r", "--recursive", action="store_true",
            #                    help="Recursively search the input directory")
            parser.add_argument('in_path', nargs='+', type=str, help='the input')
            parser.add_argument('-w', "--workspace", default=config.DEFAULT_WORKSPACE, type=str, help='the workspace directory (default:lian_workspace)')
            parser.add_argument("-f", "--force", action="store_true", help="Enable the FORCE mode for rewritting the workspace directory")
            parser.add_argument("-d", "--debug", action="store_true", help="Enable the DEBUG mode")
            parser.add_argument("-i", "--include_headers", type=str, help="Specifying C-like Headers")
            parser.add_argument("-p", "--print_stmts", action="store_true", help="Print statements")
            parser.add_argument("-c", "--cores", default=1, help="Configure the available CPU cores")
            parser.add_argument("--android", action="store_true", help="Enable the Android analysis mode")
            parser.add_argument("-a", "--apps", default=[], action='append', help="Config the <plugin> dir")
            parser.add_argument('-l', "--lang", default="", type=str, help='programming lang', required=True)
            parser.add_argument("--incremental", action="store_true", help="Reuse previous analysis results")


    def print_help(self):
        self.main_parser.print_help()

    def validate(self):
        correctness = True
        if not self.options.sub_command:
            correctness = False
        else:
            if not self.options.lang or not self.options.in_path:
                correctness = False

        if not correctness:
            self.main_parser.print_help()
            sys.exit(1)

    def adjust(self):
        self.options.lang = self.options.lang.split(",")
        if len(self.options.lang) == 0:
            util.error_and_quit("The target lang should be specified.")

        lang_list = []
        for lang_option in self.options.lang:
            lang_option = lang_option.strip()
            if lang_option:
                lang_list.append(lang_option)
        self.options.lang = lang_list

        constants.update_lang_extensions(lang_list)

        file_extensions = []
        for lang_option in self.options.lang:
            file_extensions.extend(LANG_EXTENSIONS.get(lang_option, []))
        self.options.lang_extensions = file_extensions

    def parse(self):
        args = self.main_parser.parse_args()
        self.options = types.SimpleNamespace(**vars(args))
        self.validate()
        self.adjust()
        return self.options
