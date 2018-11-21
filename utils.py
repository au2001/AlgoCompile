#!/usr/bin/env python3

import re

INDENT_UNIT = "    " # "\t"

WORD_CHARACTERS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")

TYPE_MAP = {
    "integer": "int",
    "": "void"
}

FUNC_MAP = {
    "read": lambda x: "std::cin >> %s;" % " >> ".join(x),
    "write": lambda x: "std::cout << %s;" % " << ".join(x)
}

OP_MAP = {
    "=": "==",
    "≠": "!=",
    "≥": ">=",
    "≤": "<=",
    "and": "&&",
    "or": "||"
}

def strip_comments(text):
    offset = 0

    stripped_text = ""
    string = None

    while offset < len(text):
        char = text[offset]

        if char == "\"" or char == "'":
            if string is None:
                string = char
            elif char == string:
                string = None

        if string is None:
            result = re.match(r"^(#.*)\n", text[offset:])
            if char == "#":
                offset += result.end(1)
                continue

        stripped_text += char
        offset += len(char)

    return stripped_text

def indent(count, text=""):
    return "\n".join(map(lambda x: INDENT_UNIT * count + x, text.split("\n")))

def translate_type(var_type):
    var_type = var_type.strip().lower()

    result = re.match(r"^(array\s+of\s+)", var_type)
    if result:
        var_type = var_type[result.end(1):]

    var_type = re.sub(r"\W+", r"", var_type)

    if var_type in TYPE_MAP:
        var_type = TYPE_MAP[var_type]

    return var_type

def write_variables(variables, var_type):
    var_type = translate_type(var_type)
    if var_type in TYPE_MAP:
        var_type = TYPE_MAP[var_type]

    var_names = ", ".join(map(lambda x: re.sub(r"\W+", r"", x), variables))

    return "%s %s;" % (var_type, var_names)

def write_parameters(variables, var_types, changed, copied):
    result = ""

    for i, var_list in enumerate(variables):
        var_type = translate_type(var_types[i])

        for variable in var_list:
            if result:
                result += ", "

            if variable in changed:
                result += "%s *%s" % (var_type, variable)
            else:
                result += "%s %s" % (var_type, variable)

    return result

def write_function(func_name, arguments):
    func_name = re.sub(r"\W+", r"", func_name).lower()

    if func_name in FUNC_MAP:
        return FUNC_MAP[func_name](arguments)

    arg_name = ", ".join(arguments)

    return "%s(%s);" % (func_name, arg_name)

def translate_operator(operator):
    if operator in OP_MAP:
        return OP_MAP[operator]

    return operator
