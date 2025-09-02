#!/usr/bin/env python3

from lian.config.constants import LIAN_INTERNAL
from lian.util import util

common_type_table0 = {
    "auto"                          : "",
    "any"                           : "",
    "object"                        : "",

    "NoneType"                      : LIAN_INTERNAL.NULL,
    "bool"                          : LIAN_INTERNAL.BOOL,
    "boolean"                       : LIAN_INTERNAL.BOOL,
    "char"                          : LIAN_INTERNAL.I8,
    "signed char"                   : LIAN_INTERNAL.I8,
    "unsigned char"                 : LIAN_INTERNAL.U8,
    "short"                         : LIAN_INTERNAL.I16,
    "signed short"                  : LIAN_INTERNAL.I16,
    "unsigned short"                : LIAN_INTERNAL.U16,
    "signed int"                    : LIAN_INTERNAL.I32,
    "unsigned int"                  : LIAN_INTERNAL.U32,
    "signed long"                   : LIAN_INTERNAL.I64,
    "unsigned long"                 : LIAN_INTERNAL.U64,
    "long long"                     : LIAN_INTERNAL.I64,
    "unsigned long long"            : LIAN_INTERNAL.U64,
    "float"                         : LIAN_INTERNAL.F32,
    "double"                        : LIAN_INTERNAL.F64,
    "long double"                   : LIAN_INTERNAL.F64,
    "wchar_t"                       : LIAN_INTERNAL.I16,
    "char16_t"                      : LIAN_INTERNAL.I16,
    "char32_t"                      : LIAN_INTERNAL.I32,
    "int8_t"                        : LIAN_INTERNAL.I8,
    "int16_t"                       : LIAN_INTERNAL.I16,
    "int32_t"                       : LIAN_INTERNAL.I32,
    "int_t"                         : LIAN_INTERNAL.I32,
    "int64_t"                       : LIAN_INTERNAL.I64,
    "uint8_t"                       : LIAN_INTERNAL.U8,
    "uint16_t"                      : LIAN_INTERNAL.U16,
    "uint32_t"                      : LIAN_INTERNAL.U32,
    "uint64_t"                      : LIAN_INTERNAL.U16,
    "size_t"                        : LIAN_INTERNAL.I64,
    "ssize_t"                       : LIAN_INTERNAL.I64,
    "isize"                         : LIAN_INTERNAL.POINTER,

    "uintptr_t"                     : LIAN_INTERNAL.POINTER,
    "nullptr_t"                     : LIAN_INTERNAL.POINTER,
    "ptr_t"                         : LIAN_INTERNAL.POINTER,
    "ptr"                           : LIAN_INTERNAL.POINTER,
    "uintptr"                       : LIAN_INTERNAL.POINTER,

    "string"                        : LIAN_INTERNAL.STRING,
    "String"                        : LIAN_INTERNAL.STRING,
    "str"                           : LIAN_INTERNAL.STRING,

    "vector"                        : LIAN_INTERNAL.ARRAY,
    "Vector"                        : LIAN_INTERNAL.ARRAY,
    "list"                          : LIAN_INTERNAL.ARRAY,
    "List"                          : LIAN_INTERNAL.ARRAY,

    "dict"                          : LIAN_INTERNAL.RECORD,
}

common_type_table_for_typed_language = {
    **common_type_table0,
    "int"                           : LIAN_INTERNAL.I32,
    "float"                         : LIAN_INTERNAL.F32,
}

common_type_table_for_untyped_language = {
    **common_type_table0,
    "int"                           : LIAN_INTERNAL.INT,
    "float"                         : LIAN_INTERNAL.FLOAT,
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

    if name == LIAN_INTERNAL.NULL:
        result = LIAN_INTERNAL.NULL

    elif name in [LIAN_INTERNAL.TRUE, LIAN_INTERNAL.FALSE]:
        result = LIAN_INTERNAL.BOOL

    elif "'" in name or '"' in name:
        result = LIAN_INTERNAL.STRING

    else:
        try:
            int(name)
            result = LIAN_INTERNAL.INT
        except ValueError:
            pass

        if result is None:
            try:
                float(name)
                result = LIAN_INTERNAL.FLOAT
            except ValueError:
                pass

        if result is None:
            result = LIAN_INTERNAL.STRING

    return result

def is_builtin_type(data_type):
    return data_type in built_data_types
