# Add to spec:
# - printing out a nil value is undefined

from env_v1 import EnvironmentManager
from type_valuev1 import Type, Value, create_value, get_printable
from intbase import InterpreterBase, ErrorType
from brewparse import parse_program


# Main interpreter class
class Interpreter(InterpreterBase):
    # constants
    BIN_OPS = {"+", "-", "*", "/", "==", "!=", "<", "<=", ">", ">=", "||", "&&"}

    # methods
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.__setup_ops()

    # run a program that's provided in a string
    # usese the provided Parser found in brewparse.py to parse the program
    # into an abstract syntax tree (ast)
    def run(self, program):
        ast = parse_program(program)
        self.__set_up_function_table(ast)
        main_func = self.__get_func_by_name("main", 0)
        self.env = EnvironmentManager()
        self.__run_statements(main_func.get("statements"))

    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}
        for func_def in ast.get("functions"):
            func_name = func_def.get("name")
            num_args = len(func_def.get("args"))

            if func_name not in self.func_name_to_ast:
                self.func_name_to_ast[func_name] = {}
            self.func_name_to_ast[func_name][num_args] = func_def
            if self.trace_output:
                print(func_name + " " + str(num_args))

            # if self.trace_output:
            #     for func_name, versions in self.func_name_to_ast.items():
            #         print(f"Function: {func_name}")
            #         for num_args, func_def in versions.items():
            #             print(f"  Argument count: {num_args}")
            #             print(f"  Definition: {func_def}")

    def __get_func_by_name(self, name, num_args):
        # if self.trace_output:
        #     for func_name, versions in self.func_name_to_ast.items():
        #         print(f"Function: {func_name}")
        #         for num_args, func_def in versions.items():
        #             print(f"  Argument count: {num_args}")
        #             print(f"  Definition: {func_def}")

        if name in self.func_name_to_ast and num_args in self.func_name_to_ast[name]:
            if self.trace_output:
                print("found function " + name + " with " + str(num_args) + " arguments!")
            return self.func_name_to_ast[name][num_args] 
        super().error(ErrorType.NAME_ERROR, f"Function {name} not found")

    def __run_statements(self, statements):
        # all statements of a function are held in arg3 of the function AST node
        for statement in statements:
            if self.trace_output:
                print(statement)

            if statement.elem_type == InterpreterBase.FCALL_NODE:
                self.__call_func(statement)
            elif statement.elem_type == "=":
                self.__assign(statement)
            elif statement.elem_type == InterpreterBase.VAR_DEF_NODE:
                self.__var_def(statement)
            elif statement.elem_type == InterpreterBase.RETURN_NODE:
                result = self.__eval_expr(statement.get("expression")) if statement.get("expression") else (Type.NIL)
                return result
            elif statement.elem_type == InterpreterBase.IF_NODE:
                if self.trace_output:
                    print("IF NODE FOUND")
                self.__handle_if(statement)
            elif statement.elem_type == InterpreterBase.FOR_NODE:
                if self.trace_output:
                    print("FOR NODE FOUND")
                self.__handle_for(statement)
            
        return (Type.NIL)
            
    def __handle_if(self, statement):
        condition = self.__eval_expr(statement.get("condition"))
        if condition.type() != Type.BOOL:
            super().error(ErrorType.TYPE_ERROR, "If condition must be a boolean")

        if condition.value() == True: 
            self.__run_statements(statement.get("statements"))
        elif statement.get("else_statements"): #includes elses and falses hopefully!?!!?!?
            self.__run_statements(statement.get("else_statements"))

    def __handle_for(self, statement):
        self.__assign(statement.get("init"))

        while True:
            condition = self.__eval_expr(statement.get("condition"))
            if condition.type() != Type.BOOL:
                super().error(ErrorType.TYPE_ERROR, "For condition must be a boolean")
            if not condition.value():
                break

            self.__run_statements(statement.get("statements"))

            # print("UPDATE: ", self.__assign(statement.get("update")))
            self.__assign(statement.get("update"))

    def __call_func(self, call_node):
        func_name = call_node.get("name")
        num_args = call_node.get("args")

        if func_name == "print":
            return self.__call_print(call_node)
        if func_name == "inputi":
            return self.__call_input(call_node)
        if func_name == "inputs":
            return self.__call_inputs(call_node)

        func_def = self.__get_func_by_name(func_name, len(num_args))
        if func_def is None: 
            super().error(ErrorType.NAME_ERROR, f"Function {func_name} was not found")

        old_env = self.env
        self.env = EnvironmentManager(old_env)

        for param, arg in zip(func_def.get("args"), num_args):
            evaluated_arg = self.__eval_expr(arg)
            if self.trace_output:
                print(f"ARGSSSSSSSSSSSSSSSSSSSS: {param.get('name')} {evaluated_arg.type()} {evaluated_arg.value()}")
            self.env.create(param.get("name"), create_value(evaluated_arg.value()))

        if self.trace_output:
            print("VARIABLES IN TEMP ENVIRONMENT: ")
            for variable in self.env.environment:
                print("KEY: ", variable, " | VALUE: ", self.env.environment[variable].v)

        result = self.__run_statements(func_def.get("statements"))
        if self.trace_output:
            print("RESULT===============================", result)
        self.env = old_env 
        if result == None:
            return (Type.NIL)
        else:
            return result

    def __call_print(self, call_ast):
        output = ""
        for arg in call_ast.get("args"):
            result = self.__eval_expr(arg)  # result is a Value object
            output = output + get_printable(result)
        super().output(output)
        return (Type.NIL)

    def __call_input(self, call_ast):
        args = call_ast.get("args")
        if args is not None and len(args) == 1:
            result = self.__eval_expr(args[0])
            super().output(get_printable(result))
        elif args is not None and len(args) > 1:
            super().error(
                ErrorType.NAME_ERROR, "No inputi() function that takes > 1 parameter"
            )
        inp = super().get_input()
        if call_ast.get("name") == "inputi":
            return Value(Type.INT, int(inp))
        # we can support inputs here later

    def __call_inputs(self, call_ast):
        args = call_ast.get("args")
        if args is not None and len(args) == 1:
            prompt_value = self.__eval_expr(args[0])
            super().output(get_printable(prompt_value))
        elif args is not None and len(args) > 1:
            super().error(ErrorType.NAME_ERROR, "inputs() function takes at most one argument")

        inp = super().get_input()
        return Value(Type.STRING, inp)

    def __assign(self, assign_ast):
        var_name = assign_ast.get("name")
        value_obj = self.__eval_expr(assign_ast.get("expression"))
        if not self.env.set(var_name, value_obj):
            super().error(
                ErrorType.NAME_ERROR, f"Undefined variable {var_name} in assignment"
            )

    def __var_def(self, var_ast):
        var_name = var_ast.get("name")
        if not self.env.create(var_name, Value(Type.INT, 0)):
            super().error(
                ErrorType.NAME_ERROR, f"Duplicate definition for variable {var_name}"
            )

    def __eval_expr(self, expr_ast):
        if expr_ast.elem_type == InterpreterBase.INT_NODE:
            # if self.trace_output:
            #     print("IT IS AN INTEGER")
            return Value(Type.INT, expr_ast.get("val"))
        
        if expr_ast.elem_type == InterpreterBase.STRING_NODE:
            # if self.trace_output:
            #     print("IT IS A STRING")
            return Value(Type.STRING, expr_ast.get("val"))
        
        if expr_ast.elem_type == InterpreterBase.BOOL_NODE:
            # if self.trace_output:
            #     print("THIS IS THE BOOLEAN VALUE: ", expr_ast.get("val"))
            return Value(Type.BOOL, expr_ast.get("val"))
        
        if expr_ast.elem_type == InterpreterBase.NIL_NODE:
            if self.trace_output:
                print("WE FOUND A NIL")
            return (Type.NIL)
        
        if expr_ast.elem_type == InterpreterBase.VAR_NODE:
            # if self.trace_output:
            #     print("IT IS A VARIABLE")
            var_name = expr_ast.get("name")
            val = self.env.get(var_name)
            if val is None:
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
            return val
        
        if expr_ast.elem_type == InterpreterBase.FCALL_NODE:
            # if self.trace_output:
            #     print("IT IS A FCALL")
            return self.__call_func(expr_ast)
        
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            # if self.trace_output:
            #     print("BIN OPS TRIGGER")
            return self.__eval_op(expr_ast)
        
        if expr_ast.elem_type == InterpreterBase.NEG_NODE:
            operand = self.__eval_expr(expr_ast.get("op1"))
            if operand.type() != Type.INT:
                super().error(ErrorType.TYPE_ERROR, "Unary '-' applied to non-integer")
            return Value(Type.INT, -operand.v)
        
        if expr_ast.elem_type == InterpreterBase.NOT_NODE:
            operand = self.__eval_expr(expr_ast.get("op1"))
            if operand.type() != Type.BOOL:
                super().error(ErrorType.TYPE_ERROR, "Unary '!' applied to non-boolean")
            return Value(Type.BOOL, not operand.v)

    def __eval_op(self, arith_ast):
        left_value_obj = self.__eval_expr(arith_ast.get("op1"))
        right_value_obj = self.__eval_expr(arith_ast.get("op2"))

        if arith_ast.elem_type in {"=="}:
            if left_value_obj == (Type.NIL) and right_value_obj == (Type.NIL):
                return Value(Type.BOOL, True)
            elif left_value_obj == (Type.NIL) or right_value_obj == (Type.NIL):
                return Value(Type.BOOL, False)
        elif arith_ast.elem_type in {"!="}:
            if left_value_obj == (Type.NIL) and right_value_obj == (Type.NIL):
                return Value(Type.BOOL, False)
            elif left_value_obj == (Type.NIL) or right_value_obj == (Type.NIL):
                return Value(Type.BOOL, True)

        # if not isinstance(left_value_obj, Value) or not isinstance(right_value_obj, Value):
        #     print("LEFT ERROR: ", left_value_obj)
        #     print("RIGHT ERROR: ", right_value_obj)
        #     super().error(ErrorType.TYPE_ERROR, "Expected Value type for comparison")

        if left_value_obj.type() != right_value_obj.type():
            if arith_ast.elem_type in {"=="}:
                return Value(Type.BOOL, False)
            elif arith_ast.elem_type in {"!="}:
                return Value(Type.BOOL, True)
            super().error(ErrorType.TYPE_ERROR, f"Incompatible types for {arith_ast.elem_type} operation")

        if arith_ast.elem_type not in self.op_to_lambda[left_value_obj.type()]:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible operator {arith_ast.elem_type} for type {left_value_obj.type()}",
            )
        f = self.op_to_lambda[left_value_obj.type()][arith_ast.elem_type]
        return f(left_value_obj, right_value_obj)

    def __setup_ops(self):
        self.op_to_lambda = {}
        # set up operations on integers
        self.op_to_lambda[Type.INT] = {}
        self.op_to_lambda[Type.INT] = {
            "+": lambda x, y: Value(Type.INT, x.value() + y.value()),
            "-": lambda x, y: Value(Type.INT, x.value() - y.value()),
            # "-": lambda x: Value(Type.INT, -x.value()),
            "*": lambda x, y: Value(Type.INT, x.value() * y.value()),
            "/": lambda x, y: Value(Type.INT, x.value() // y.value()),
            "==": lambda x, y: Value(Type.BOOL, x.value() == y.value()),
            "!=": lambda x, y: Value(Type.BOOL, x.value() != y.value()),
            "<": lambda x, y: Value(Type.BOOL, x.value() < y.value()),
            "<=": lambda x, y: Value(Type.BOOL, x.value() <= y.value()),
            ">": lambda x, y: Value(Type.BOOL, x.value() > y.value()),
            ">=": lambda x, y: Value(Type.BOOL, x.value() >= y.value()),
        }

        self.op_to_lambda[Type.BOOL] = {}
        self.op_to_lambda[Type.BOOL] = {
            "&&": lambda x, y: Value(Type.BOOL, x.value() and y.value()),
            "||": lambda x, y: Value(Type.BOOL, x.value() or y.value()),
            "==": lambda x, y: Value(Type.BOOL, x.value() == y.value()),
            # "!": lambda x: Value(Type.BOOL, not x.value()),
            "!=": lambda x, y: Value(Type.BOOL, x.value() != y.value())
        }

        self.op_to_lambda[Type.STRING] = {}
        self.op_to_lambda[Type.STRING] = {
            "+": lambda x, y: Value(Type.STRING, x.value() + y.value()),
            "==": lambda x, y: Value(Type.BOOL, x.value() == y.value()),
            "!=": lambda x, y: Value(Type.BOOL, x.value() != y.value()),
        }

test_program = """

func foo(a) {
    print("THIS IS a: ", a);
    return a + a;
}

func foo(a,b) {
    print(a," ",b);
}

func foo() { 
    print("bruh this is foo again hello");
}

func bar() {
    print("returning nil rn");
    return;  
}

func testPrintBool() {
    return true;
}

func fooPrint(a,b) {
    var returnStr;
    returnStr = a + b;
    return returnStr;
}

func fooOnCrack(x) {
    if (x < 0) {
        print(x);
        return -x;
        print("this will not print");
    }
    print("this will not print either");
    return 5*x;
}

func main() {
    print(foo(5));
    foo(6,7);
    print(fooPrint(4, 5));

    print("TESTPRINTBOOLEAN (SHOULD BE TRUE): ", testPrintBool());

    var justinTrudeau;
    justinTrudeau = false;
    print("justinTrudeau (SHOULD BE FALSE): ", justinTrudeau);

    print("HERE COMES THE FUN PART===================================================================");
    print(true || false);  /* prints true */
    print(true || false && false); /* prints true */
    print(5/3);            /* prints 1 */
    print(-6);             /* prints -6 */
    print(-(4 + 3));       /* prints -7 */
    print(true == -(3 + 3)); /* prints false */
    print(!true);          /* prints false */
    print(true && !true);  /* prints false */
    print(true && true);  /* prints true */
    print("FUN PART ENDS=============================================================================");

    var a;
    a = 3;
    print(a > 5);          /* prints false */
    print("abc"+"def");    /* prints abcdef */

    var testInputS;
    testInputS = inputs("enter a string! ");
    print(testInputS);
    
    var x;
    var y;
    x = inputi("enter x: "); 
    y = inputi("enter y: "); 

    if (x > 5) {
        print(x);
    }

    if (10 < x && x < 30) {
        print(3*x);
    }

    if (y > 0) {
        print(y);
    } else {
        print(-y);
    }

    if (y != nil) {
        print("throw an error party");
    }

    var val;
    print("created val");
    val = nil;
    print("assigned val the value of nil");
    if (foo() == nil && bar() == nil) { print("this should print!"); }

    var i;
    for (i=0; i+3 < 10; i=i+1) {
        print(i);
    }

    print("the positive value is ", fooOnCrack(-10));
}
"""

new_interpreter = Interpreter(console_output = True, inp = None, trace_output = True)
new_interpreter.run(test_program)