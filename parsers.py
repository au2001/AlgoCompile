#!/usr/bin/env python3

import re

import utils
import outputs

class Parser(object):

    def __init__(self, out_c, out_h):
        super().__init__()

        self.out_c = out_c
        self.out_h = out_h

    def starts(text, parent):
        return -1

    def children(self):
        return []

    def ends(self, text):
        return -1

    def parse(self, text):
        return 0

    def write_c(self, text):
        self.out_c.write(text)

    def write_h(self, text):
        self.out_h.write(text)

class FileParser(Parser):

    def __init__(self, out_c, out_h):
        super().__init__(out_c, out_h)

    def starts(text, parent):
        return 0, FileParser(parent.out_c, parent.out_h)

    def children(self):
        return [GlobalVariablesParser, FunctionDefinitionParser, MainFunctionDefinitionParser]

    def ends(self, text):
        return 0 if not text else -1

    def parse(self, text):
        char = text[0]

        if char == "\n" or char == " " or char == "\t":
            return len(char)

        raise Exception("Unexpected character \"%s\" (%d) in file." % (char, ord(char)))

class GlobalVariablesParser(Parser):

    def __init__(self, out_c, out_h):
        super().__init__(out_c, out_h)

        self.variables = [""]
        self.var_type = None

    def starts(text, parent):
        if text[:4].upper() == "VAR:":
            return 4, GlobalVariablesParser(parent.out_c, parent.out_h)
        else:
            return -1, None

    def ends(self, text):
        return 0 if self.variables is None else -1

    def parse(self, text):
        char = text[0]

        if char == ",":
            if self.var_type is None:
                if not self.variables[-1]:
                    raise Exception("Unexpected character \"%s\" (%d) in global variables." % (char, ord(char)))

                self.variables.append("")
            elif self.var_type:
                self.write_h("%s\n" % utils.indent(self.out_h.indent, utils.write_variables(self.variables, self.var_type)))
                self.variables = [""]
                self.var_type = None
            else:
                raise Exception("Unexpected character \"%s\" (%d) in global variables." % (char, ord(char)))

            return len(char)

        if char == ":" and self.var_type is None:
            self.var_type = ""

            return len(char)

        if self.var_type is None and (char == "[" or char == "]" or char in utils.WORD_CHARACTERS):
            self.variables[-1] += char

            return len(char)

        if self.var_type is not None and (char == " " or char in utils.WORD_CHARACTERS):
            self.var_type += char

            return len(char)

        if char == "\n" and self.var_type is not None:
            self.write_h("%s\n" % utils.indent(self.out_h.indent, utils.write_variables(self.variables, self.var_type)))
            self.variables = None
            self.var_type = None
            return 0

        if (char == "\n" or char == " " or char == "\t") and self.var_type is None and not self.variables[-1]:
            return len(char)

        if self.var_type is None and len(self.variables[0]) == 1 and not self.variables[0]:
            offset = 0

            while offset < len(text) and (text[offset] == "\n" or text[offset] == " " or text[offset] == "\t"):
                pass

            if offset > 0:
                return offset

        raise Exception("Unexpected character \"%s\" (%d) in global variables definition." % (char, ord(char)))

class VariablesParser(Parser):

    def __init__(self, out_c, out_h):
        super().__init__(out_c, out_h)

        self.variables = [""]
        self.var_type = None

    def starts(text, parent):
        char = text[0]

        if char in utils.WORD_CHARACTERS:
            if type(parent) is FunctionDefinitionParser:
                out_c = outputs.FunctionParametersOutput(parent)
                out_h = outputs.FunctionParametersOutput(parent, var_type=True)
                return 0, VariablesParser(out_c, out_h)
            else:
                out_c = outputs.VariablesOutput(parent)
                out_h = outputs.VariablesOutput(parent, var_type=True)
                return 0, VariablesParser(out_c, out_h)
        else:
            return -1, None

    def ends(self, text):
        return 0 if self.variables is None else -1

    def parse(self, text):
        char = text[0]

        if self.var_type is None and (char == "[" or char == "]" or char in utils.WORD_CHARACTERS):
            self.variables[-1] += char

            return len(char)

        if char == "," and self.var_type is None:
            self.variables.append("")

            return len(char)

        if char == ":" and self.var_type is None:
            self.var_type = ""

            return len(char)

        if self.var_type is not None and (char == " " or char in utils.WORD_CHARACTERS):
            self.var_type += char

            return len(char)

        if self.var_type is None and not self.variables[-1] and char == "\n" or char == " " or char == "\t":
            return len(char)

        if self.var_type is not None:
            for i, variable in enumerate(self.variables):
                if i > 0:
                    self.write_c("\n")
                self.write_c(variable)
            self.write_h(self.var_type)

            self.variables = None
            self.var_type = None

            return 0

        raise Exception("Unexpected character \"%s\" (%d) in variables definition." % (char, ord(char)))

class MainFunctionDefinitionParser(Parser):

    def __init__(self, out_c, out_h):
        super().__init__(out_c, out_h)

    def starts(text, parent):
        if re.match(r"^BEGIN\b", text.upper()):
            child = MainFunctionDefinitionParser(out_c=parent.out_c, out_h=parent.out_h)
            child.write_c("%s\n" % utils.indent(child.out_c.indent, "int main(int argc, char *argv[]) {"))
            child.write_h("%s\n" % utils.indent(child.out_h.indent, "int main(int argc, char *argv[]);"))
            return 5, child
        else:
            return -1, None

    def children(self):
        return [IfConditionParser, WhileLoopParser, DoWhileLoopParser, ForLoopParser, SwitchStatementParser, FunctionCallParser, AssignmentParser]

    def ends(self, text):
        if re.match(r"^END\b", text.upper()):
            self.write_c("%s\n" % utils.indent(self.out_c.indent + 1, "return 0;"))
            self.write_c("%s\n" % utils.indent(self.out_c.indent, "}"))
            return 3
        else:
            return -1

    def parse(self, text):
        char = text[0]

        if char == "\n" or char == " " or char == "\t":
            return len(char)

        raise Exception("Invalid operation starting with character \"%s\" (%d) in main function body." % (char, ord(char)))

class FunctionDefinitionParser(Parser):

    def __init__(self, out_c, out_h):
        super().__init__(out_c, out_h)

        self.func_name = ""
        self.variables = None
        self.var_types = None
        self.return_type = None
        self.done_return = False
        self.changed_parameters = None
        self.copied_parameters = None
        self.local_variables = None
        self.local_types = None
        self.current_parameters = None

    def starts(text, parent):
        if re.match(r"^\w+\s*\(", text.lower()) and not re.match(r"^(while|for|do|if)\s*\(", text.lower()):
            return 0, FunctionDefinitionParser(out_c=parent.out_c, out_h=parent.out_h)
        else:
            return -1, None

    def children(self):
        if self.func_name is None:
            return [IfConditionParser, WhileLoopParser, DoWhileLoopParser, ForLoopParser, SwitchStatementParser, FunctionCallParser, AssignmentParser]
        elif (self.variables is not None and self.return_type is None) or (self.local_variables is not None and self.local_variables == [[""]]):
            return [VariablesParser]
        else:
            return []

    def ends(self, text):
        if self.func_name is None and re.match(r"^END\b", text.upper()):
            self.write_c("%s\n" % utils.indent(self.out_c.indent, "}"))
            return 3
        else:
            return -1

    def parse(self, text):
        char = text[0]

        if self.func_name is not None:
            if self.variables is None and char in utils.WORD_CHARACTERS:
                self.func_name += char

                return len(char)

            if char == "(" and self.variables is None:
                self.variables = [[""]]
                self.var_types = [""]

                return len(char)

            if char == "," and self.variables is not None and self.return_type is None:
                self.variables.append([""])
                self.var_types.append("")

                return len(char)

            if char == ")" and self.variables is not None and self.return_type is None:
                self.return_type = ""

                result = re.match(r"^(\)\s*:)", text.lower())
                if result:
                    return result.end(1)
                else:
                    self.done_return = True

                    return len(char)

            if self.return_type is not None and not self.done_return:
                if char == " " or char in utils.WORD_CHARACTERS:
                    self.return_type += char

                    return len(char)
                else:
                    self.done_return = True

            if self.return_type is not None and self.done_return and self.current_parameters is None:
                if self.changed_parameters is None:
                    result = re.match(r"^(changed\s+parameters\s*:)", text.lower())
                    if result:
                        self.changed_parameters = [""]
                        self.current_parameters = "changed"

                        return result.end(1)

                elif self.copied_parameters is None:
                    result = re.match(r"^(copied\s+parameters\s*:)", text.lower())
                    if result:
                        self.copied_parameters = [""]
                        self.current_parameters = "copied"

                        return result.end(1)

                elif self.local_variables is None:
                    result = re.match(r"^(local\s+variables\s*:)", text.lower())
                    if result:
                        self.local_variables = [[""]]
                        self.local_types = [""]

                        self.current_parameters = None

                        return result.end(1)

            if self.current_parameters == "changed":
                if char == ",":
                    self.changed_parameters.append("")

                    return len(char)
                elif char in utils.WORD_CHARACTERS:
                    self.changed_parameters[-1] += char

                    return len(char)
                elif (char == "\n" and not self.changed_parameters[-1]) or char == " " or char == "\t":
                    return len(char)
                else:
                    self.current_parameters = None

            if self.current_parameters == "copied":
                if char == ",":
                    self.copied_parameters.append("")

                    return len(char)
                elif char in utils.WORD_CHARACTERS:
                    self.copied_parameters[-1] += char

                    return len(char)
                elif (char == "\n" and not self.copied_parameters[-1]) or char == " " or char == "\t":
                    return len(char)
                else:
                    self.current_parameters = None

            if self.current_parameters is None and (char == "\n" or char == " " or char == "\t"):
                return len(char)

            if re.match(r"^BEGIN\b", text.upper()):
                return_type = utils.translate_type(self.return_type)

                self.write_c("%s\n" % utils.indent(self.out_c.indent, "%s %s(%s) {" % (return_type, self.func_name, utils.write_parameters(self.variables, self.var_types, self.changed_parameters, self.copied_parameters))))
                self.write_h("%s\n" % utils.indent(self.out_h.indent, "%s %s(%s);" % (return_type, self.func_name, utils.write_parameters(self.variables, self.var_types, self.changed_parameters, self.copied_parameters))))

                for i, variables in enumerate(self.local_variables):
                    var_type = utils.translate_type(self.local_types[i])
                    self.write_c("%s\n" % utils.indent(self.out_c.indent + 1, utils.write_variables(variables, var_type)))

                self.func_name = None
                self.variables = None
                self.var_types = None
                self.return_type = None
                self.changed_parameters = None
                self.copied_parameters = None
                self.local_variables = None
                self.local_types = None
                self.current_parameters = None

                return 5
        elif char == "\n" or char == " " or char == "\t":
            return len(char)

        raise Exception("Unexpected character \"%s\" (%d) in function definition." % (char, ord(char)))

class FunctionCallParser(Parser):

    def __init__(self, out_c, out_h):
        super().__init__(out_c, out_h)

        self.func_name = ""
        self.arguments = None

    def starts(text, parent):
        if re.match(r"^\w+\s*\(", text.lower()) and not re.match(r"^(while|for|do|if)\s*\(", text.lower()):
            if type(parent) is FormulaParser:
                out_c = outputs.PipeOutput(parent.out_c, indent=-1)
                return 0, FunctionCallParser(out_c, parent.out_h)
            else:
                out_c = outputs.PipeOutput(parent.out_c, indent=parent.out_c.indent + 1)
                return 0, FunctionCallParser(out_c, parent.out_h)
        else:
            return -1, None

    def children(self):
        if self.arguments is not None and not self.arguments[-1]:
            return [FormulaParser]
        else:
            return []

    def ends(self, text):
        return 0 if self.func_name is None else -1

    def parse(self, text):
        char = text[0]

        if char == "\n" or char == " " or char == "\t":
            return len(char)

        if char == "," and self.arguments is not None:
            if not self.arguments[-1]:
                raise Exception("Unexpected character \"%s\" (%d) in function call." % (char, ord(char)))

            self.arguments.append("")

            return len(char)

        if char == "(" and self.arguments is None:
            self.arguments = [""]

            return len(char)

        if self.arguments is None and char in utils.WORD_CHARACTERS:
            self.func_name += char

            return len(char)

        if char == ")" and self.arguments is not None:
            if self.out_c.indent >= 0:
                self.write_c("%s\n" % utils.indent(self.out_c.indent, utils.write_function(self.func_name, self.arguments)))
            else:
                self.write_c(utils.write_function(self.func_name, self.arguments))

            self.func_name = None
            self.arguments = None

            return len(char)

        raise Exception("Unexpected character \"%s\" (%d) in function call." % (char, ord(char)))

class FormulaParser(Parser):

    def __init__(self, out_c, out_h):
        super().__init__(out_c, out_h)

        self.string = None
        self.escaped = False
        self.parenthesis = False

        self.current = False
        self.operator = False
        self.empty = True
        self.ended = False

    def starts(text, parent):
        char = text[0]

        if char in ["(", "\"", "\'", "+", "-"] or char in utils.WORD_CHARACTERS:
            if type(parent) is FunctionCallParser:
                return 0, FormulaParser(outputs.FunctionArgumentOutput(parent), parent.out_h)
            elif type(parent) is AssignmentParser:
                return 0, FormulaParser(outputs.AssignmentOutput(parent), parent.out_h)
            elif type(parent) in [IfConditionParser, WhileLoopParser, DoWhileLoopParser, SwitchStatementParser]:
                return 0, FormulaParser(outputs.ConditionalOutput(parent), parent.out_h)
            elif type(parent) is ForLoopParser:
                return 0, FormulaParser(outputs.ForLoopOutput(parent), parent.out_h)
            else:
                return 0, FormulaParser(parent.out_c, parent.out_h)
        else:
            return -1, None

    def children(self):
        if self.string is None and (not self.current or self.operator or self.empty) and not self.ended:
            if self.parenthesis:
                return [FunctionCallParser, FormulaParser]
            else:
                return [FunctionCallParser]
        else:
            return []

    def ends(self, text):
        return 0 if self.ended else -1

    def parse(self, text):
        char = text[0]

        if self.string is not None:
            if self.escaped:
                self.escaped = False

                if char == "\n":
                    return len(char)
                else:
                    self.write_c("\\")
            elif char == "\\":
                self.escaped = True

                return len(char)
            elif char == self.string:
                self.string = None
            elif char == "\n":
                self.write_c("\\n")

                return len(char)

            self.write_c(char)

            return len(char)

        if self.parenthesis:
            if char == ")":
                self.parenthesis = False

                self.write_c(char)

                return len(char)
            else:
                raise Exception("Expected closing parenthesis but got character \"%s\" (%d) in formula." % (char, ord(char)))

        if char == "\"" or char == "'":
            self.string = char
            self.operator = False
            self.empty = False

            self.write_c(char)

            return len(char)

        if (self.current or self.operator or self.empty) and char in utils.WORD_CHARACTERS:
            self.current = True
            self.operator = False
            self.empty = False

            self.write_c(char)

            return len(char)

        if self.current and char == ".":
            self.write_c(char)

            return len(char)

        if not self.current and not self.operator and (char == "+" or char == "-"):
            self.current = True

            self.write_c(char)

            return len(char)

        if not self.operator and not self.empty:
            result = re.match(r"^\s*(\+|-|\*|/|%|={1,3}|≠|!=|<|>|>=|≥|<=|≤|\|{1,2}|&{1,2}|\^|\band\b|\bor\b)", text.lower())
            if result:
                self.current = False
                self.operator = True

                self.write_c(" %s " % utils.translate_operator(result.group(1)))

                return result.end(1)

        if (self.operator or self.empty) and char == "(":
            self.parenthesis = True
            self.current = False
            self.operator = False
            self.empty = False

            self.write_c(char)

            return len(char)

        if (self.operator or self.empty) and (char == "\n" or char == " " or char == "\t"):
            self.current = False

            return len(char)

        if not self.string and not self.parenthesis:
            self.current = False
            self.ended = True
            return 0

        raise Exception("Unexpected character \"%s\" (%d) in formula." % (char, ord(char)))

class AssignmentParser(Parser):

    def __init__(self, out_c, out_h):
        super().__init__(out_c, out_h)

        self.lhs = ""
        self.rhs = None

    def starts(text, parent):
        if re.match(r"^\w+\s*<-", text.lower()):
            out_c = outputs.PipeOutput(parent.out_c, indent=parent.out_c.indent + 1)
            return 0, AssignmentParser(out_c, parent.out_h)
        else:
            return -1, None

    def children(self):
        if self.rhs is not None and not self.rhs:
            return [FormulaParser]
        else:
            return []

    def ends(self, text):
        return 0 if self.lhs is None else -1

    def parse(self, text):
        char = text[0]

        if self.rhs is not None and self.rhs:
            self.write_c("%s\n" % utils.indent(self.out_c.indent, "%s = %s;" % (self.lhs, self.rhs)))
            self.lhs = None
            self.rhs = None

            return 0

        if self.rhs is None:
            result = re.match(r"^\s*(<-)", text.lower())
            if result:
                self.rhs = ""

                return result.end(1)

            if char in utils.WORD_CHARACTERS or char == " ":
                self.lhs += char

                return len(char)

        if char == "\n" or char == " " or char == "\t":
            return len(char)

        raise Exception("Unexpected character \"%s\" (%d) in assignment." % (char, ord(char)))

class IfConditionParser(Parser):

    def __init__(self, out_c, out_h):
        super().__init__(out_c, out_h)

        self.condition = ""
        self.else_block = False

    def starts(text, parent):
        if re.match(r"^if\b", text.lower()):
            out_c = outputs.PipeOutput(parent.out_c, indent=parent.out_c.indent + 1)
            return 2, IfConditionParser(out_c=out_c, out_h=parent.out_h)
        else:
            return -1, None

    def children(self):
        if self.condition is None:
            return [IfConditionParser, WhileLoopParser, DoWhileLoopParser, ForLoopParser, SwitchStatementParser, FunctionCallParser, AssignmentParser]
        elif not self.condition:
            return [FormulaParser]
        else:
            return []

    def ends(self, text):
        if self.condition is None:
            result = re.match(r"^(end\s+if)\b", text.lower())
            if result:
                self.write_c("%s\n" % utils.indent(self.out_c.indent, "}"))
                return result.end(1)
            else:
                return -1
        else:
            return -1

    def parse(self, text):
        char = text[0]

        if char == "\n" or char == " " or char == "\t":
            return len(char)

        if self.condition is not None:
            result = re.match(r"^(then)\b", text.lower())
            if result:
                if not self.else_block:
                    self.write_c("%s\n" % utils.indent(self.out_c.indent, "if (%s) {" % self.condition))
                else:
                    self.write_c("%s\n" % utils.indent(self.out_c.indent, "} else if (%s) {" % self.condition))
                    self.else_block = False

                self.condition = None

                return result.end(1)
            else:
                raise Exception("Unexpected character \"%s\" (%d) in if condition." % (char, ord(char)))

        result = re.match(r"^(else\s+if)\b", text.lower())
        if result:
            self.condition = ""
            self.else_block = True

            return result.end(1)

        if not self.else_block:
            result = re.match(r"^(else)\b", text.lower())
            if result:
                self.write_c("%s\n" % utils.indent(self.out_c.indent, "} else {"))

                self.condition = None

                return result.end(1)
            else:
                raise Exception("Unexpected character \"%s\" (%d) in if condition." % (char, ord(char)))

        raise Exception("Unexpected character \"%s\" (%d) in if body." % (char, ord(char)))

class WhileLoopParser(Parser):

    def __init__(self, out_c, out_h):
        super().__init__(out_c, out_h)

        self.condition = ""

    def starts(text, parent):
        if re.match(r"^while\b", text.lower()):
            out_c = outputs.PipeOutput(parent.out_c, indent=parent.out_c.indent + 1)
            return 5, WhileLoopParser(out_c=out_c, out_h=parent.out_h)
        else:
            return -1, None

    def children(self):
        if self.condition is None:
            return [IfConditionParser, WhileLoopParser, DoWhileLoopParser, ForLoopParser, SwitchStatementParser, FunctionCallParser, AssignmentParser]
        elif not self.condition:
            return [FormulaParser]
        else:
            return []

    def ends(self, text):
        if self.condition is None:
            result = re.match(r"^(end\s+while)\b", text.lower())
            if result:
                self.write_c("%s\n" % utils.indent(self.out_c.indent, "}"))
                return result.end(1)
            else:
                return -1
        else:
            return -1

    def parse(self, text):
        char = text[0]

        if char == "\n" or char == " " or char == "\t":
            return len(char)

        if self.condition is not None:
            self.write_c("%s\n" % utils.indent(self.out_c.indent, "while (%s) {" % self.condition))

            self.condition = None

            return 0

        raise Exception("Unexpected character \"%s\" (%d) in while loop body." % (char, ord(char)))

class DoWhileLoopParser(Parser):

    def __init__(self, out_c, out_h):
        super().__init__(out_c, out_h)

        self.condition = None

    def starts(text, parent):
        if re.match(r"^do\b", text.lower()):
            out_c = outputs.PipeOutput(parent.out_c, indent=parent.out_c.indent + 1)
            child = DoWhileLoopParser(out_c=out_c, out_h=parent.out_h)
            child.write_c("%s\n" % utils.indent(child.out_c.indent, "do {"))
            return 2, child
        else:
            return -1, None

    def children(self):
        if self.condition is None:
            # Disabled while loops directly inside do-whiles, otherwise there is no way to differentiate the do-while's end and a while's beginning
            return [IfConditionParser, DoWhileLoopParser, ForLoopParser, SwitchStatementParser, FunctionCallParser, AssignmentParser]
        elif not self.condition:
            return [FormulaParser]
        else:
            return []

    def ends(self, text):
        if self.condition is not None and self.condition:
            self.write_c("%s\n" % utils.indent(self.out_c.indent, "} while (%s);" % self.condition))
            return 0
        else:
            return -1

    def parse(self, text):
        char = text[0]

        if char == "\n" or char == " " or char == "\t":
            return len(char)

        if self.condition is None:
            result = re.match(r"^(while)\b", text.lower())
            if result:
                self.condition = ""

                return result.end(1)

        raise Exception("Unexpected character \"%s\" (%d) in for loop body." % (char, ord(char)))

class ForLoopParser(Parser):

    def __init__(self, out_c, out_h):
        super().__init__(out_c, out_h)

        self.variable = ""
        self.start_value = None
        self.end_value = None
        self.increment = None

    def starts(text, parent):
        if re.match(r"^for\b", text.lower()):
            out_c = outputs.PipeOutput(parent.out_c, indent=parent.out_c.indent + 1)
            return 3, ForLoopParser(out_c=out_c, out_h=parent.out_h)
        else:
            return -1, None

    def children(self):
        if self.variable is None:
            return [IfConditionParser, WhileLoopParser, DoWhileLoopParser, ForLoopParser, SwitchStatementParser, FunctionCallParser, AssignmentParser]
        elif (self.start_value is not None and not self.start_value) or (self.end_value is not None and not self.end_value) or (self.increment is not None and not self.increment):
            return [FormulaParser]
        else:
            return []

    def ends(self, text):
        if self.variable is None:
            result = re.match(r"^(end\s+for)\b", text.lower())
            if result:
                self.write_c("%s\n" % utils.indent(self.out_c.indent, "}"))

                return result.end(1)
            else:
                return -1
        else:
            return -1

    def parse(self, text):
        char = text[0]

        if char == "\n" or char == " " or char == "\t":
            return len(char)

        if self.variable is not None and self.start_value is None:
            if char in utils.WORD_CHARACTERS:
                self.variable += char

                return len(char)
            else:
                result = re.match(r"^(<-)", text.lower())
                if result:
                    self.start_value = ""

                    return result.end(1)
                else:
                    raise Exception("Unexpected character \"%s\" (%d) in for loop variable definition." % (char, ord(char)))

        if self.start_value is not None and self.end_value is None:
            result = re.match(r"^(to)\b", text.lower())
            if result:
                self.end_value = ""

                return result.end(1)
            else:
                raise Exception("Unexpected character \"%s\" (%d) in for loop initial value definition." % (char, ord(char)))

        if self.end_value is not None and self.increment is None:
            if char == "[":
                self.increment = ""

                return len(char)
            else:
                result = re.match(r"^(do)\b", text.lower())
                if result:
                    self.write_c("%s\n" % utils.indent(self.out_c.indent, "for (%s = %s; %s <= %s; ++%s) {" % (self.variable, self.start_value, self.variable, self.end_value, self.variable)))

                    self.variable = None
                    self.start_value = None
                    self.end_value = None
                    self.increment = None

                    return result.end(1)
                else:
                    raise Exception("Unexpected character \"%s\" (%d) in for loop end value definition." % (char, ord(char)))

        if self.increment is not None:
            result = re.match(r"^(\]\s+do)\b", text.lower())
            if result:
                if self.increment.strip() != "1":
                    self.write_c("%s\n" % utils.indent(self.out_c.indent, "for (%s = %s; %s <= %s; %s += %s) {" % (self.variable, self.start_value, self.variable, self.end_value, self.variable, self.increment)))
                else:
                    self.write_c("%s\n" % utils.indent(self.out_c.indent, "for (%s = %s; %s <= %s; ++%s) {" % (self.variable, self.start_value, self.variable, self.end_value, self.variable)))

                self.variable = None
                self.start_value = None
                self.end_value = None
                self.increment = None

                return result.end(1)
            else:
                raise Exception("Unexpected character \"%s\" (%d) in for loop increment definition." % (char, ord(char)))

        raise Exception("Unexpected character \"%s\" (%d) in for loop body." % (char, ord(char)))

class SwitchStatementParser(Parser):

    def __init__(self, out_c, out_h):
        super().__init__(out_c, out_h)

        self.condition = ""
        self.switch = True
        self.first_case = True

    def starts(text, parent):
        if re.match(r"^switch\b", text.lower()):
            out_c = outputs.PipeOutput(parent.out_c, indent=parent.out_c.indent + 1)
            return 6, SwitchStatementParser(out_c=out_c, out_h=parent.out_h)
        else:
            return -1, None

    def children(self):
        if self.condition is None:
            return [IfConditionParser, WhileLoopParser, DoWhileLoopParser, ForLoopParser, SwitchStatementParser, FunctionCallParser, AssignmentParser]
        elif not self.condition:
            return [FormulaParser]
        else:
            return []

    def ends(self, text):
        if self.condition is None:
            result = re.match(r"^(end\s+switch)\b", text.lower())
            if result:
                self.write_c("%s\n" % utils.indent(self.out_c.indent, "}"))

                return result.end(1)
            else:
                return -1
        else:
            return -1

    def parse(self, text):
        char = text[0]

        if char == "\n" or char == " " or char == "\t":
            return len(char)

        if self.condition is not None and self.condition:
            if self.switch:
                self.write_c("%s\n" % utils.indent(self.out_c.indent, "switch (%s) {" % self.condition))

                self.condition = None
                self.switch = False

                return 0
            elif char == ":":
                self.write_c("%s\n" % utils.indent(self.out_c.indent, "case %s:" % self.condition))

                self.condition = None

                return len(char)
            else:
                raise Exception("Unexpected character \"%s\" (%d) in switch case." % (char, ord(char)))

        if self.condition is None:
            result = re.match(r"^(case)\b", text.lower())
            if result:
                self.condition = ""

                if not self.first_case:
                    self.write_c("%s\n" % utils.indent(self.out_c.indent + 1, "break;"))
                else:
                    self.first_case = False

                return result.end(1)
            else:
                result = re.match(r"^(default\s*:)", text.lower())
                if result:
                    if not self.first_case:
                        self.write_c("%s\n" % utils.indent(self.out_c.indent + 1, "break;"))
                    else:
                        self.first_case = False

                    self.write_c("%s\n" % utils.indent(self.out_c.indent, "default:"))

                    return result.end(1)

        raise Exception("Unexpected character \"%s\" (%d) in switch body." % (char, ord(char)))
