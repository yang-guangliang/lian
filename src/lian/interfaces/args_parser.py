#!/usr/bin/env python3

import sys
import argparse
import types
from lian.config import config

class ArgsParser:
    def __init__(self):
        self.main_parser = argparse.ArgumentParser()
        self.options = self.obtain_default_options()

    def init(self):
        # Create the top-level parser
        subparsers = self.main_parser.add_subparsers(dest='sub_command')
        # Create the parser for the "lang" command
        parser_lang = subparsers.add_parser('lang', help="Parse code to General IR")
        parser_semantic = subparsers.add_parser('semantic', help='Perform semantic analysis')
        parser_security = subparsers.add_parser('security', help='Conduct security analysis')
        parser_run = subparsers.add_parser('run', help='Run end-to-end analysis')
        # Add the arguments to the main parser

        for parser in [parser_lang, parser_semantic, parser_security, parser_run]:
            parser.add_argument("-b", "--benchmark", action="store_true")
            # parser.add_argument("-r", "--recursive", action="store_true",
            #                    help="Recursively search the input directory")
            parser.add_argument('in_path', nargs='+', type=str, help='the input')
            parser.add_argument('-w', "--workspace", default=config.DEFAULT_WORKSPACE, type=str, help='the workspace directory (default:lian_workspace)')
            parser.add_argument("-f", "--force", action="store_true", help="Enable the FORCE mode for rewritting the workspace directory")
            parser.add_argument("-d", "--debug", action="store_true", help="Enable the DEBUG mode")
            parser.add_argument("-i", "--included_headers", type=str, help="Specifying C-like Headers")
            parser.add_argument("-I", "--process_headers", action="store_true", help="Deal with C-like Headers")
            parser.add_argument("-p", "--print_stmts", action="store_true", help="Print statements")
            parser.add_argument("-c", "--cores", default=1, help="Configure the available CPU cores")
            parser.add_argument("--android", action="store_true", help="Enable the Android analysis mode")
            parser.add_argument("-a", "--apps", default=[], action='append', help="Config the <plugin> dir")
            parser.add_argument('-l', "--lang", default="", type=str, help='programming lang', required=True)

            parser.add_argument("-noextern", action="store_true", help="Disable the external processing module")

        return self

    def merge_options(self, parsed_args):
        for key, value in vars(parsed_args).items():
            setattr(self.options, key, value)

    def obtain_default_options(self):
        return types.SimpleNamespace(
            apps = [],
            lang = "",
            benchmark = False,
            android = False,
            cores = 1,
            print_stmts = False,
            included_headers = "",
            process_headers = False,
            debug = False,
            force = False,
            recursive = True,
            workspace = config.DEFAULT_WORKSPACE,
            sub_command = "",
            in_path = "",
        )

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
            self.print_help()
            sys.exit(1)

    def adjust_lang(self):
        self.options.lang = self.options.lang.split(",")
        if len(self.options.lang) == 0:
            util.error_and_quit("The target lang should be specified.")

        lang_list = []
        for lang_option in self.options.lang:
            lang_option = lang_option.strip()
            if lang_option:
                lang_list.append(lang_option)
        self.options.lang = lang_list

    def parse_cmds(self):
        args = self.main_parser.parse_args()
        self.merge_options(args)
        self.adjust_lang()
        self.validate()
        return self.options
