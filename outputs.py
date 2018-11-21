#!/usr/bin/env python3

class Output(object):

    def __init__(self, indent=0):
        super().__init__()

        self.indent = indent

    def write(self, text):
        print(text)

class PipeOutput(Output):

    def __init__(self, output, indent=0):
        super().__init__(indent=indent)

        self.output = output

    def write(self, text):
        self.output.write(text)

class FileOutput(Output):

    def __init__(self, file, indent=0):
        super().__init__(indent=indent)

        self.file = file

    def write(self, text):
        self.file.write(text)

class VariablesOutput(Output):

    def __init__(self, variables, indent=0, var_type=False):
        super().__init__(indent=indent)

        self.variables = variables
        self.var_type = var_type

    def write(self, text):
        if not self.var_type:
            if text == "\n":
                self.variables.variables[-1].append("")
            else:
                self.variables.variables[-1][-1] += text
        else:
            self.variables.var_types[-1] += text

class FunctionParametersOutput(Output):

    def __init__(self, function, indent=0, var_type=False):
        super().__init__(indent=indent)

        self.function = function
        self.var_type = var_type

    def write(self, text):
        if self.function.local_variables is not None:
            if not self.var_type:
                if text == "\n":
                    self.function.local_variables[-1].append("")
                else:
                    self.function.local_variables[-1][-1] += text
            else:
                self.function.local_types[-1] += text

        elif self.function.variables is not None:
            if not self.var_type:
                if text == "\n":
                    self.function.variables[-1].append("")
                else:
                    self.function.variables[-1][-1] += text
            else:
                self.function.var_types[-1] += text

class FunctionArgumentOutput(Output):

    def __init__(self, function_call, indent=0):
        super().__init__(indent=indent)

        self.function_call = function_call

    def write(self, text):
        self.function_call.arguments[-1] += text

class AssignmentOutput(Output):

    def __init__(self, assignment, indent=0):
        super().__init__(indent=indent)

        self.assignment = assignment

    def write(self, text):
        self.assignment.rhs += text

class ConditionalOutput(Output):

    def __init__(self, condition, indent=0):
        super().__init__(indent=indent)

        self.condition = condition

    def write(self, text):
        self.condition.condition += text

class ForLoopOutput(Output):

    def __init__(self, for_loop, indent=0):
        super().__init__(indent=indent)

        self.for_loop = for_loop

    def write(self, text):
        if self.for_loop.increment is not None:
            self.for_loop.increment += text
        elif self.for_loop.end_value is not None:
            self.for_loop.end_value += text
        elif self.for_loop.start_value is not None:
            self.for_loop.start_value += text
        elif self.for_loop.variable is not None:
            self.for_loop.variable += text
