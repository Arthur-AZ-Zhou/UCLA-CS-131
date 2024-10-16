from intbase import InterpreterBase
from intbase import ErrorType
from brewparse import parse_program
from element import Element

class Interpreter(InterpreterBase):
    def __init__(self, console_output = True, inp = None, trace_output = False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.variables = {} #store names and values

    def run(self, program):
        ast = parse_program(program)
        print("ast: ", ast)
        self.var_name_to_val = dict()
        main_func_node = self.get_main_func_node(ast)
        run_func(main_func_node)

    def get_main_func_node(self, tree: Element):
        if tree.elem_type == "program":
            main = tree.get("functions")[0]

            if main.elem_type == "func" and main.get("name") == "main":
                return main
            super().error(
                ErrorType.NAME_ERROR,
                "No main() function was found",
            )
        return None

    def run_func(self, main_node: Element):
        if main_node: #Not none
            pass

test_program = [
    '''func main() {
        var x;
        x = 5 + 6;
        print("The sum is: ", x);
    }'''
]

new_interpreter = Interpreter(console_output = True)
new_interpreter.run(test_program)