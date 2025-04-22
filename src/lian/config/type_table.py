#!/usr/bin/env python3

from lian.config.constants import LianInternal
from lian.util import util

common_type_table0 = {
    "auto"                          : "",
    "any"                           : "",
    "object"                        : "",

    "NoneType"                      : LianInternal.NULL,
    "bool"                          : LianInternal.BOOL,
    "boolean"                       : LianInternal.BOOL,
    "char"                          : LianInternal.I8,
    "signed char"                   : LianInternal.I8,
    "unsigned char"                 : LianInternal.U8,
    "short"                         : LianInternal.I16,
    "signed short"                  : LianInternal.I16,
    "unsigned short"                : LianInternal.U16,
    "signed int"                    : LianInternal.I32,
    "unsigned int"                  : LianInternal.U32,
    "signed long"                   : LianInternal.I64,
    "unsigned long"                 : LianInternal.U64,
    "long long"                     : LianInternal.I64,
    "unsigned long long"            : LianInternal.U64,
    "float"                         : LianInternal.F32,
    "double"                        : LianInternal.F64,
    "long double"                   : LianInternal.F64,
    "wchar_t"                       : LianInternal.I16,
    "char16_t"                      : LianInternal.I16,
    "char32_t"                      : LianInternal.I32,
    "int8_t"                        : LianInternal.I8,
    "int16_t"                       : LianInternal.I16,
    "int32_t"                       : LianInternal.I32,
    "int_t"                         : LianInternal.I32,
    "int64_t"                       : LianInternal.I64,
    "uint8_t"                       : LianInternal.U8,
    "uint16_t"                      : LianInternal.U16,
    "uint32_t"                      : LianInternal.U32,
    "uint64_t"                      : LianInternal.U16,
    "size_t"                        : LianInternal.I64,
    "ssize_t"                       : LianInternal.I64,
    "isize"                         : LianInternal.POINTER,

    "uintptr_t"                     : LianInternal.POINTER,
    "nullptr_t"                     : LianInternal.POINTER,
    "ptr_t"                         : LianInternal.POINTER,
    "ptr"                           : LianInternal.POINTER,
    "uintptr"                       : LianInternal.POINTER,

    "string"                        : LianInternal.STRING,
    "String"                        : LianInternal.STRING,
    "str"                           : LianInternal.STRING,

    "vector"                        : LianInternal.ARRAY,
    "Vector"                        : LianInternal.ARRAY,
    "list"                          : LianInternal.ARRAY,
    "List"                          : LianInternal.ARRAY,

    "dict"                          : LianInternal.RECORD,
}

common_type_table_for_typed_language = {
    **common_type_table0,
    "int"                           : LianInternal.I32,
    "float"                         : LianInternal.F32,
}

common_type_table_for_untyped_language = {
    **common_type_table0,
    "int"                           : LianInternal.INT,
    "float"                         : LianInternal.FLOAT,
}

lang_type_table = {
    "c": common_type_table_for_typed_language,
    "java": common_type_table_for_typed_language,
    "llvm": common_type_table_for_typed_language,
    "mir": common_type_table_for_typed_language,
    "python": common_type_table_for_untyped_language,
    "javascript": common_type_table_for_untyped_language,
    "php": common_type_table_for_untyped_language,
}

built_data_types = set()
for table in [common_type_table0, common_type_table_for_typed_language, common_type_table_for_untyped_language]:
    for value in table.values():
        if value:
            built_data_types.add(value)

def get_lang_type_table(lang):
    return lang_type_table.get(lang, common_type_table0)

def determine_constant_type(name):
    result = None

    if util.isna(name):
        return result

    if name == LianInternal.NULL:
        result = LianInternal.NULL

    elif name in [LianInternal.TRUE, LianInternal.FALSE]:
        result = LianInternal.BOOL

    elif "'" in name or '"' in name:
        result = LianInternal.STRING

    else:
        try:
            int(name)
            result = LianInternal.INT
        except ValueError:
            pass

        if result is None:
            try:
                float(name)
                result = LianInternal.FLOAT
            except ValueError:
                pass

        if result is None:
            result = LianInternal.STRING

    return result

def is_builtin_type(data_type):
    return data_type in built_data_types
