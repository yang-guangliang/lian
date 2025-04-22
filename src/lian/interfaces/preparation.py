#!/usr/bin/env python3

import os
import re
import shutil
import tempfile
import subprocess
from lian.util import util
from lian.config import constants, config, lang_config
import lian.util.data_model as dm

SymbolKind = constants.SymbolKind
LANG_EXTENSIONS = lang_config.LANG_EXTENSIONS
EXTENSIONS_LANG = lang_config.EXTENSIONS_LANG

class WorkspaceBuilder:
    def __init__(self, options):
        self.dst_file_to_src_file = {}
        self.options = options
        #self.clang_installed = shutil.which('clang') is not None and shutil.which('clang++') is not None
        self.clang_installed = False
        self.c_like_extensions = LANG_EXTENSIONS.get('c', []) + LANG_EXTENSIONS.get('cpp', [])
        self.required_subdirs = [
            config.SOURCE_CODE_DIR, config.EXTERNS_DIR, config.GIR_DIR,
            config.SEMANTIC_DIR_P1, config.SEMANTIC_DIR_P2, config.SEMANTIC_DIR_P3
        ]
        self.header_keywords = [
            "stdio.h", "stdlib.h", "string.h", "math.h", "ctype.h", "time.h",
            "assert.h", "errno.h", "limits.h", "locale.h", "setjmp.h", "signal.h",
            "stdarg.h", "stddef.h", "stdint.h", "stdio_ext.h", "float.h", "iso646.h",
            "wchar.h", "wctype.h", "fenv.h", "inttypes.h", "complex.h", "tgmath.h",
            "stdalign.h", "stdatomic.h", "stdnoreturn.h", "threads.h", "uchar.h",
            "iostream", "iomanip", "fstream", "sstream", "cmath", "cstdlib", "cstdio",
            "cstring", "cctype", "cwchar", "climits", "cfloat", "cstdarg", "cstdbool",
            "csignal", "cerrno", "ciso646", "cwctype", "csetjmp", "ctime", "cassert",
            "cfenv", "cstdalign", "cstdint", "cinttypes", "clocale", "ccomplex",
            "cuchar", "stdexcept", "string", "vector", "deque", "list", "set", "map",
            "unordered_map", "unordered_set", "stack", "queue", "algorithm", "iterator",
            "numeric", "utility", "memory", "functional", "bitset", "locale", "stdexcept",
            "cassert", "mutex", "thread", "future", "condition_variable", "chrono",
            "random", "ratio", "complex", "tuple", "array", "new", "type_traits",
            "typeinfo", "initializer_list", "scoped_allocator", "system_error", "iosfwd",
            "ios", "istream", "ostream", "limits", "exception", "functional", "locale",
            "codecvt", "cstddef", "cstdint", "compare", "coroutine", "iterator",
            "memory_resource", "version", "concepts", "ranges", "span", "stop_token",
            "syncstream", "any", "optional", "variant"
        ]

    def manage_directory(self):
        path = self.options.workspace
        if not os.path.exists(path):
            os.makedirs(path)
            if config.DEBUG_FLAG:
                util.debug(f"Directory created at: {path}")
            return

        if not self.options.force:
            util.error_and_quit(f"The target directory already exists: {path}. Use --force/-f to overwrite.")
        if config.DEBUG_FLAG:
            util.warn(f"With the force mode flag, the workspace is being rewritten: {path}")

        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                util.error_and_quit(f"Failed to delete {file_path}. Reason: {e}")

    def obtain_file_extension(self, file_path):
        return os.path.splitext(file_path)[1].lower()

    def preprocess_c_like_file(self, file_path):
        # check if the file exists
        if not os.path.isfile(file_path):
            util.error(f"Error: The file does not exist or the path is invalid: {file_path}")
            return

        extension = self.obtain_file_extension(file_path)
        if extension not in self.c_like_extensions:
            return

        file_path_name = os.path.splitext(file_path)[0]
        new_file_path = f"{file_path_name}_processed{extension}"

        # Create a new file to store the modified content
        with open(new_file_path, 'w') as new_file:
            with open(file_path, 'r') as f:
                for line in f:
                    # skip the #include <
                    if re.match(r'^\s*#include\s*<', line):
                        continue
                    # skip the keywords
                    if any(re.search(fr'\b{keyword}\b', line) for keyword in self.header_keywords):
                        continue

                    new_file.write(line)

        # Prepare the include headers if provided
        include_flags = []
        if self.options.include_headers:
            include_flags.append('-I')
            include_flags.append(self.options.include_headers)

        # Depending on the language type, choose the right Clang command
        try:
            if extension in LANG_EXTENSIONS.get('c', []) :
                preprocessed_file = f"{file_path_name}.i"
                subprocess.run(['clang', '-P', '-E', new_file_path, '-o', preprocessed_file] + include_flags, check=True)
            elif extension in LANG_EXTENSIONS.get('cpp', []):
                preprocessed_file = f"{file_path_name}.ii"
                subprocess.run(['clang++', '-P', '-E', new_file_path, '-o', preprocessed_file] + include_flags, check=True)
        except subprocess.CalledProcessError:
            return

    def rescan_c_like_files(self, target_path):
        if os.path.isdir(target_path):
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.isdir(file_path):
                        self.rescan_c_like_files(file_path)
                    elif os.path.isfile(file_path):
                        self.preprocess_c_like_file(file_path)

        elif os.path.isfile(target_path):
            self.preprocess_c_like_file(target_path)

    def change_c_like_files(self, src_dir_path):
        if "c" in self.options.lang or "cpp" in self.options.lang:
            if self.clang_installed:
                self.rescan_c_like_files(src_dir_path)

                LANG_EXTENSIONS["c"] = [".i"]
                LANG_EXTENSIONS["cpp"] = [".ii"]

    def copytree_with_extension(self, src, dst_path):
        if os.path.islink(src):
            return

        # Check if the source is a directory
        if os.path.isdir(src):
            # Walk through the source directory
            for root, dirs, files in os.walk(src):
                # Construct the destination path, maintaining the folder structure
                rel_path = os.path.relpath(root, src)
                new_dst_path = os.path.join(dst_path, rel_path)

                # Create directories in the destination path
                os.makedirs(new_dst_path, exist_ok=True)

                # Recursively call the function for each file with the specified extension
                for file in files:
                    src_file = os.path.join(root, file)
                    self.copytree_with_extension(src_file, new_dst_path)

        # If the source is a file
        elif os.path.isfile(src):
            ext = os.path.splitext(src)[1].lower()
            if ext in self.options.lang_extensions:
                dst_file = os.path.realpath(os.path.join(dst_path, os.path.basename(src)))
                src_file = os.path.realpath(src)
                shutil.copy2(src_file, dst_file)
                self.dst_file_to_src_file[dst_file] = src_file

    def run(self):
        workspace_path = self.options.workspace
        self.manage_directory()
        #build the sub-directories
        for subdir in self.required_subdirs:
            subdir_path = os.path.join(workspace_path, subdir)
            os.makedirs(subdir_path, exist_ok=True)

        src_dir_path = os.path.join(workspace_path, config.SOURCE_CODE_DIR)
        for path in self.options.in_path:
            if self.options.workspace in path:
                continue
            if os.path.isdir(path):
                path_name = os.path.basename(path)
                self.copytree_with_extension(path, os.path.join(src_dir_path, path_name))
            else:
                self.copytree_with_extension(path, src_dir_path)
            #self.copytree_with_extension(path, src_dir_path)

        self.change_c_like_files(src_dir_path)

        externs_dir_path = os.path.join(workspace_path, config.EXTERNS_DIR)
        self.copytree_with_extension(config.EXTERNS_MOCK_CODE_DIR, externs_dir_path)

        return self.dst_file_to_src_file

class ModuleSymbolsBuilder:
    def __init__(self, options, loader, dst_file_to_src_file = {}):
        self.global_module_id = config.START_INDEX
        self.module_symbol_results = []
        self.options = options
        self.loader = loader
        self.file_counter = 0
        self.dst_file_to_src_file = dst_file_to_src_file

    def generate_module_id(self):
        result = self.global_module_id
        self.global_module_id += 1
        return result

    def scan_modules(self, module_path, parent_module_id = 0, is_extern = False):
        if module_path is None:
            return

        # Only scan current directory, _not_ recursively
        for entry in os.scandir(module_path):
            # scan all folders and build the module-level symbols
            if entry.is_dir():
                module_id = self.generate_module_id()
                self.module_symbol_results.append({
                    "module_id": module_id,
                    "symbol_name": entry.name,
                    "unit_path": entry.path,
                    "parent_module_id": parent_module_id,
                    "symbol_type": SymbolKind.MODULE_SYMBOL,
                    "is_extern": is_extern
                })
                self.scan_modules(entry.path, module_id, is_extern)

            # scan each .gl file, and extract the unit-level symbols
            elif entry.is_file():
                self.file_counter += 1
                unit_id = self.generate_module_id()
                unit_name, unit_ext = os.path.splitext(entry.name)
                self.module_symbol_results.append({
                    "module_id": unit_id,
                    "symbol_name": unit_name,
                    "unit_ext": unit_ext,
                    "lang": EXTENSIONS_LANG.get(unit_ext, "unknown"),
                    "parent_module_id": parent_module_id,
                    "symbol_type": SymbolKind.UNIT_SYMBOL,
                    "unit_path": entry.path,
                    "original_path": self.dst_file_to_src_file.get(entry.path, ""),
                    "is_extern": is_extern
                })

    def run(self):
        self.scan_modules(module_path = os.path.join(self.options.workspace, config.SOURCE_CODE_DIR))
        if len(self.module_symbol_results) == 0:
            util.error_and_quit("No target file found.")
        self.scan_modules(module_path = os.path.join(self.options.workspace, config.EXTERNS_DIR), is_extern = True)
        self.loader.save_module_symbols(self.module_symbol_results)

def run(options, loader):
    dst_file_to_src_file = WorkspaceBuilder(options).run()
    #print("dst_file_to_src_file", dst_file_to_src_file)
    ModuleSymbolsBuilder(options, loader, dst_file_to_src_file).run()
    loader.export()
