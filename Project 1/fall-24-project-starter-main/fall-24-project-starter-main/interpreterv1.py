from intbase import InterpreterBase
from intbase import ErrorType
from brewparse import parse_program
from element import Element

class Interpreter(InterpreterBase):
    def __init__(self, console_output = True, inp = None, trace_output = False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output # it's whatever if I have this
        self.name_to_item = dict()

    def run(self, program):
        ast = parse_program(program)
        print("ast: ", ast)
        main_func_node = self.get_main_func(ast)
        self.run_func_def_node(main_func_node)

    def get_main_func(self, tree): # SEARCHES THRU PROGRAM NODE
        if tree.elem_type == "program": #We are guaranteed this too but this is just in case for future projects
            main = tree.get("functions")[0] #this SHOULD ALWAYS WORK

            if main.elem_type == "func" and main.get("name") == "main":
                print("SUCCESSFULLY FOUND MAIN")
                return main
            else:
                super().error(ErrorType.NAME_ERROR, "No main() function was found",)
        return None

    def run_func_def_node(self, main_node): # RUN EACH STATEMENT IN FUNCTION DEFINITION NODE
        if main_node: #Not none
            for statement in main_node.get("statements"):
                self.run_each_statement(statement)
            print(self.name_to_item)

    def run_each_statement(self, node): # ANALYZE STATEMENT AND DO RESPECTIVE ACTION
        print("\nElemType: ", node.elem_type)
        print("Statement: ", node)
        statement_type = node.elem_type
        variable_name = node.get("name")

        if statement_type == "vardef":
            if variable_name in self.name_to_item:
                super().error(ErrorType.NAME_ERROR, f"Variable {variable_name} defined more than once",)
            self.name_to_item[variable_name] = None

        elif statement_type == "=": 
            if variable_name not in self.name_to_item:
                super().error(ErrorType.NAME_ERROR, f"Variable {variable_name} has not been defined",)

            expression_result = self.run_expression(node.get("expression"))
            self.name_to_item[variable_name] = expression_result

        elif statement_type == "fcall": # TO DO WTF IS THIS?!?!?!?!?
            if variable_name != "print" and variable_name != "inputi":
                super().error(ErrorType.NAME_ERROR, f"Function {variable_name} has not been defined",)
            else:
                pass
                # arguments = node.get("args")
                # print(arguments)
                # print(self.run_expression(node.get("args")))
            
        else: #error if it's not a valid statement
            super().error(ErrorType.NAME_ERROR, "Not a valid statement!",)

        print(self.name_to_item)

    def run_expression(self, node): #PROCESS EACH EXPRESSION
        expression_type = node.elem_type
        print("EXPRESSION TYPE: ", expression_type, "---------------------------------------")

        if expression_type == "+" or expression_type == "-":
            op1 = self.run_expression(node.get("op1"))
            op2 = self.run_expression(node.get("op2"))

            if isinstance(op1, int) and isinstance(op2, int):            
                if expression_type == "+":
                    return op1 + op2
                elif expression_type == "-":
                    return op1 - op2
            else:
                super().error(ErrorType.TYPE_ERROR, "Incompatible types for arithmetic operation",)
                return None
            
        elif expression_type == "fcall": # this should only refer to inputi
            pass
            
        elif expression_type == "int":
            return int(node.get("val"))
        
        elif expression_type == "var":
            variable_name = node.get("name")
            return self.name_to_item[variable_name]
        
        elif expression_type == "string":
            return node.get("val")
        
        else: 
            super().error(ErrorType.NAME_ERROR, "Unknown expression type",)

test_program = """func main() {
    var x;
    var y;
    var z;
    var a;
    var b;
    var a_str;
    var magic_num;
    var magic_num_no_prompt;

    x = 5 + 6;
    y = 10;
    z = (x + (1 - 3)) - y;
    a_str = "this is a string";

    print(10);
    print("hello world!");
    print("The sum is: ", x);
    print("the answer is: ", x + (y - 5), "!");

    magic_num = inputi("enter a magic number: "); 
    magic_num_no_prompt = inputi();

    a = 4 + inputi("enter a number: ");
    b = 3 - (3 + (2 + inputi()));    
}"""

new_interpreter = Interpreter(console_output = True, inp = None, trace_output = True)
new_interpreter.run(test_program)