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
        self.variable_val_dict = dict()
        main_func_node = self.get_main_func_node(ast)
        self.run_func(main_func_node)
        # self.lines = program
        # self.interpret_program()

    # def interpret_program(self): #looks for main function
    #     main_func = None
    #     for l in self.lines:
    #         if l.startswith("func main"):
    #             main_func = l
    #             break

    #     if main_func == None:
    #         super().error(ErrorType.NAME_ERROR, "main() wasn't found")
    #     else:
    #         self.interpret_main(main_func)

    # def interpret_main(self, body):
    #     body = body.replace('func main() {', '').replace('}', '').strip()
    #     lines = [l.strip() for l in body.split(';') if l.strip()]

    #     for l in lines:
    #         self.interpret_line(l)

    # def interpret_line(self, line):
        pass

    def get_main_func_node(self, tree: Element):
        if tree.elem_type == "program":
            main = tree.get("functions")[0]

            if main.elem_type == "func" and main.get("name") == "main":
                print("SUCCESSFULLY FOUND MAIN")
                return main
            super().error(
                ErrorType.NAME_ERROR,
                "No main() function was found",
            )
        return None

    def run_func(self, main_node: Element):
        if main_node: #Not none
            for statement in main_node.get("statements"):
                self.run_statement(statement)

    def run_statement(self, node):
        print("ElemType: ", node.elem_type)

test_program = """func main() {
    var x;
    x = 5 + 6;
    print("The sum is: ", x);
}"""

new_interpreter = Interpreter(console_output = True, inp = None, trace_output = True)
new_interpreter.run(test_program)