# document that we won't have a return inside the init/update of a for loop

import copy
from enum import Enum

from brewparse import parse_program
from env_v2 import EnvironmentManager
from intbase import InterpreterBase, ErrorType
from type_valuev2 import Type, Value, create_value, get_printable


class ExecStatus(Enum):
    CONTINUE = 1
    RETURN = 2

class Interpreter(InterpreterBase):
    NIL_VALUE = create_value(InterpreterBase.NIL_DEF)
    TRUE_VALUE = create_value(InterpreterBase.TRUE_DEF)
    BIN_OPS = {"+", "-", "*", "/", "==", "!=", ">", ">=", "<", "<=", "||", "&&"}

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.__setup_ops()

    def run(self, program):
        ast = parse_program(program)
        self.__set_up_function_table(ast)
        self.env = EnvironmentManager()
        self.must_return = False
        self.__call_func_aux("main", [])

    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}

        for func_def in ast.get("functions"):
            func_name = func_def.get("name")
            num_params = len(func_def.get("args"))
            params = func_def.get("args")

            if func_name not in self.func_name_to_ast:
                self.func_name_to_ast[func_name] = {}

            for arg in params:
                if not arg.get("var_type") or not self.valid_type_var(arg.get("var_type")):
                    super().error(ErrorType.TYPE_ERROR, description=f"Invalid type for formal parameter {arg.get('name')} for function {func_name}")

            func_return_type = func_def.get("return_type")
            
            if not func_return_type or not self.valid_type_return(func_return_type):
                super().error(ErrorType.TYPE_ERROR, description=f"Invalid return type {func_return_type} for function {func_name}")

            self.func_name_to_ast[func_name][num_params] = func_def #literally only do this if all else succeeds

    def valid_type_var(self, var_type): # MUST INITIALIZE DEFAULT TYPES
        return var_type == InterpreterBase.INT_NODE or var_type == InterpreterBase.BOOL_NODE or var_type == InterpreterBase.STRING_NODE

    def valid_type_return(self, return_type):
        return self.valid_type_var(return_type) or return_type == Type.VOID;

    def defaults(self, default_var):
        if default_var == InterpreterBase.INT_NODE:
            return Value(type=Type.INT, value=0)
        elif default_var == InterpreterBase.STRING_NODE:
            return Value(type=Type.STRING, value="")
        elif default_var == InterpreterBase.BOOL_NODE:
            return Value(type=Type.BOOL, value=False)
        elif default_var == InterpreterBase.VOID_DEF:
            return Value(type=Type.VOID, value=Type.VOID)
        elif default_var == _:  # STRUCTS BUT COME BACK TO THIS LATER=======================
            return Value(type=var_type, value=Type.NIL)

    def __get_func_by_name(self, name, num_params):
        if name not in self.func_name_to_ast:
            super().error(ErrorType.NAME_ERROR, f"Function {name} not found")
        candidate_funcs = self.func_name_to_ast[name]
        if num_params not in candidate_funcs:
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {name} taking {num_params} params not found",
            )
        
        return candidate_funcs[num_params]

    def __run_statements(self, statements):
        self.env.push_block()
        for statement in statements:
            if self.trace_output:
                print(statement)

            status, return_val = self.__run_statement(statement)
            if status == ExecStatus.RETURN:
                if self.trace_output:
                    print("STATUS: ", status, "===================================================================")
                    print("RETURN VAL: ", return_val.type(), "===========================================================")

                if self.env.is_in_function:
                    expected_return_type = self.env.get("return")
                    print("EXPECTED_RETURN_TYPE: ", expected_return_type, " ====================================================")
                    if return_val.value() is None:
                        return_val = self.defaults(expected_return_type)

                    if return_val.type() != expected_return_type:
                        if return_val.type() == Type.INT and expected_return_type == Type.BOOL:
                            return_val = Value(Type.BOOL, self.int_to_bool_coercion(return_val))
                        elif return_val.type == Type.NIL and expected_return_type in self.type_manager.struct_types:
                            return_val = Value(expected_return_type, Type.NIL)
                        else: 
                            super().error(ErrorType.TYPE_ERROR, description=f"Returned value's type {return_val.type()} is inconsistent with function's return type {expected_return_type}")

                self.env.pop_block()
                return (status, return_val)

        if self.env.is_in_function:
            expected_return_type = self.env.get("return")
            print("EXPECTED_RETURN_TYPE: ", expected_return_type, " ====================================================")
            return_val = self.defaults(expected_return_type)
        self.env.pop_block()
        return (ExecStatus.CONTINUE, return_val)

    def __run_statement(self, statement):
        status = ExecStatus.CONTINUE
        return_val = None
        if statement.elem_type == InterpreterBase.FCALL_NODE:
            self.__call_func(statement)
        elif statement.elem_type == "=":
            self.__assign(statement)
        elif statement.elem_type == InterpreterBase.VAR_DEF_NODE:
            self.__var_def(statement)
        elif statement.elem_type == InterpreterBase.RETURN_NODE:
            status, return_val = self.__do_return(statement)
        elif statement.elem_type == Interpreter.IF_NODE:
            status, return_val = self.__do_if(statement)
        elif statement.elem_type == Interpreter.FOR_NODE:
            status, return_val = self.__do_for(statement)

        return (status, return_val)
    
    def __call_func(self, call_node):
        func_name = call_node.get("name")
        actual_args = call_node.get("args")
        
        # if self.trace_output:
        #     print("CALLNODE: ", call_node)
        #     print("func_name: ", func_name)
        #     print("actual_args: ", actual_args)
        return self.__call_func_aux(func_name, actual_args)

    def __call_func_aux(self, func_name, actual_args):
        # if self.trace_output:
        #     print("func_name in AUX: ", func_name)
        if func_name == "print":
            return self.__call_print(actual_args)
        if func_name == "inputi" or func_name == "inputs":
            return self.__call_input(func_name, actual_args)

        func_ast = self.__get_func_by_name(func_name, len(actual_args))
        # if self.trace_output:
        #     print("we get here for: ", func_name)
        formal_args = func_ast.get("args")
        # if self.trace_output:
        #     print("formal_args: ", formal_args)
        if len(actual_args) != len(formal_args):
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {func_ast.get('name')} with {len(actual_args)} args not found",
            )

        # args = self.func_name_to_ast[name][num_params].get("args")
        for i in range(len(actual_args)):
            # if self.trace_output:
            #     print("i: ", i)
            #     print("actual_args: ", actual_args)
            #     print("formal_args: ", formal_args)
            #     print("actual_args[i]'s type HOLY SHIT THIS WAS FUCKING: ", self.__eval_expr(actual_args[i]).type())
            #     print("formal_args[i].get('var_type'): ", formal_args[i].get('var_type'))

            if (self.__eval_expr(actual_args[i]).type() != formal_args[i].get("var_type") and not ((self.__eval_expr(actual_args[i]).type() == Type.INT and formal_args[i].get('var_type') == Type.BOOL)
                    # or (arg.type() == Type.NIL and args[i].get("var_type") in self.type_manager.struct_types)
                )
            ):
                super().error(ErrorType.TYPE_ERROR, description=f"Type mismatch on formal parameter {formal_args[i].get('name')}")
        

        # first evaluate all of the actual parameters and associate them with the formal parameter names
        args = {}
        for formal_ast, actual_ast in zip(formal_args, actual_args):
            result = copy.copy(self.__eval_expr(actual_ast))
            arg_name = formal_ast.get("name")
            # if self.trace_output:
            #     print("arg_name: ", arg_name)
            args[arg_name] = result

        # then create the new activation record 
        self.env.push_func()
        # and add the formal arguments to the activation record
        self.env.environment[-1][-1]["return"] = self.__get_func_by_name(func_name, len(actual_args)).get("return_type")
        if self.trace_output:
            print("RETURN TYPE: ", self.__get_func_by_name(func_name, len(actual_args)).get("return_type"))
            print("ENV GET: ", self.env.get("return"))
        
        for arg_name, value in args.items():
          self.env.create(arg_name, value)
        _, return_val = self.__run_statements(func_ast.get("statements"))
        self.env.pop_func()
        return return_val

    def __call_print(self, args):
        output = ""
        for arg in args:
            result = self.__eval_expr(arg)  # result is a Value object
            if result.type() == Type.VOID:
                result = Value(Type.NIL, None)
            output = output + get_printable(result)
        super().output(output)
        return self.defaults(Type.VOID)

    def __call_input(self, name, args):
        if args is not None and len(args) == 1:
            result = self.__eval_expr(args[0])
            super().output(get_printable(result))
        elif args is not None and len(args) > 1:
            super().error(
                ErrorType.NAME_ERROR, "No inputi() function that takes > 1 parameter"
            )
        inp = super().get_input()
        if name == "inputi":
            return Value(Type.INT, int(inp))
        if name == "inputs":
            return Value(Type.STRING, inp)

    def __assign(self, assign_ast):
        var_name = assign_ast.get("name")
        var_obj = self.env.get(var_name)
        val = self.__eval_expr(assign_ast.get("expression"))
        if not self.env.set(var_name, val):
            super().error(
                ErrorType.NAME_ERROR, f"Undefined variable {var_name} in assignment"
            )

        # if self.trace_output:
        #     print("var_name type: ", var_obj.type())
        #     print("value_obj type: ", val.type())
        
        if var_obj.type() != val.type(): #COME BACK TO STRUCTS LATER
            if var_obj.type() == Type.BOOL and val.type() == Type.INT:
                val = Value(Type.BOOL, self.int_to_bool_coercion(val))
            else:
                super().error(ErrorType.TYPE_ERROR, description=f"Type mismatch b/t {var_obj.type()} and {val.type()}")
        self.env.set(var_name, val)

    def int_to_bool_coercion(self, val):
        if self.trace_output:
            print("val.type(): ", val.type())
            print("val.value(): ", val.value())

        if val.type() == Type.INT:
            if val.value() == 0:
                return False;
            else:
                return True;
        elif val.type() == Type.BOOL:
            return val.value()
        else: 
            super().error(ErrorType.TYPE_ERROR, f"Incompatible types")
    
    def __var_def(self, var_ast):
        var_name = var_ast.get("name")
        var_type = var_ast.get("var_type")
        if not var_type or not self.valid_type_var(var_type):
            super().error(ErrorType.TYPE_ERROR, description=f"Invalid type {var_type} for var {var_name}")
            
        default_val = self.defaults(var_type)

        if not self.env.create(var_name, default_val):
            super().error(
                ErrorType.NAME_ERROR, f"Duplicate definition for variable {var_name}"
            )

    def __eval_expr(self, expr_ast):
        if expr_ast.elem_type == InterpreterBase.NIL_NODE:
            # print("NIL NODE TRIGGERE")
            return Value(Type.NIL, Type.NIL)
        if expr_ast.elem_type == InterpreterBase.INT_NODE:
            # print("INT NODE TRIGGERE")
            return Value(Type.INT, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.STRING_NODE:
            # print("STRING NODE TRIGGERE")
            return Value(Type.STRING, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.BOOL_NODE:
            # print("BOOL NODE TRIGGERE")
            return Value(Type.BOOL, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.VAR_NODE:
            # print("VAR NODE TRIGGER")
            var_name = expr_ast.get("name")
            # if self.trace_output:
            #     print("var_name: ", var_name)
            val = self.env.get(var_name)
            # if self.trace_output:
            #     print("val: ", val)
            if val is None:
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
            return val
        if expr_ast.elem_type == InterpreterBase.FCALL_NODE:
            # print("FCALL TRIGGER")
            return self.__call_func(expr_ast)
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            return self.__eval_op(expr_ast)
        if expr_ast.elem_type == Interpreter.NEG_NODE:
            return self.__eval_unary(expr_ast, Type.INT, lambda x: -1 * x)
        if expr_ast.elem_type == Interpreter.NOT_NODE:
            return self.__eval_unary(expr_ast, Type.BOOL, lambda x: not x)

    def __eval_op(self, arith_ast):
        left_value_obj = self.__eval_expr(arith_ast.get("op1"))
        right_value_obj = self.__eval_expr(arith_ast.get("op2"))

        operator = arith_ast.elem_type

        if operator in {"&&", "||"}:
            left_bool = self.int_to_bool_coercion(left_value_obj)
            right_bool = self.int_to_bool_coercion(right_value_obj)
            result = left_bool and right_bool if operator == "&&" else left_bool or right_bool
            return Value(Type.BOOL, result)

        if operator in {"==", "!="}:
            # Coerce both operands to BOOL if one of them is BOOL
            # if left_value_obj.type() == Type.INT and right_value_obj.type() == Type.BOOL:
            #     left_val = self.int_to_bool_coercion(left_value_obj)
            #     right_val = right_value_obj.value()
            # elif left_value_obj.type() == Type.BOOL and right_value_obj.type() == Type.INT:
            #     left_val = left_value_obj.value()
            #     right_val = self.int_to_bool_coercion(right_value_obj)
            # elif left_value_obj.type() == Type.INT and right_value_obj.type() == Type.INT:
            #     left_val = left_value_obj.value()
            #     right_val = right_value_obj.value()
            # else:
            #     left_val = left_value_obj.value()
            #     right_val = right_value_obj.value()

            left_val = self.int_to_bool_coercion(left_value_obj)
            right_val = self.int_to_bool_coercion(right_value_obj)

            is_equal = left_val == right_val
            result = is_equal if operator == "==" else not is_equal
            return Value(Type.BOOL, result)

        # if left_value_obj.type() != right_value_obj.type():
        #     super().error(ErrorType.TYPE_ERROR, f"Incompatible types for {arith_ast.elem_type} operation")

        # if not self.__compatible_types(arith_ast.elem_type, left_value_obj, right_value_obj):
        #     super().error(
        #         ErrorType.TYPE_ERROR,
        #         f"Incompatible types for {arith_ast.elem_type} operation",
        #     )

        if arith_ast.elem_type not in self.op_to_lambda[left_value_obj.type()]:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible operator {arith_ast.elem_type} for type {left_value_obj.type()}",
            )
        f = self.op_to_lambda[left_value_obj.type()][arith_ast.elem_type]
        return f(left_value_obj, right_value_obj)

    # def __compatible_types(self, oper, obj1, obj2):
    #     # DOCUMENT: allow comparisons ==/!= of anything against anything
    #     if oper in ["==", "!="]:
    #         return True
    #     return obj1.type() == obj2.type()

    def __eval_unary(self, arith_ast, t, f):
        value_obj = self.__eval_expr(arith_ast.get("op1"))
        if value_obj.type() != t:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible type for {arith_ast.elem_type} operation",
            )
        return Value(t, f(value_obj.value()))

    def __setup_ops(self):
        self.op_to_lambda = {}
        # set up operations on integers
        self.op_to_lambda[Type.INT] = {}
        self.op_to_lambda[Type.INT]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.INT]["-"] = lambda x, y: Value(
            x.type(), x.value() - y.value()
        )
        self.op_to_lambda[Type.INT]["*"] = lambda x, y: Value(
            x.type(), x.value() * y.value()
        )
        self.op_to_lambda[Type.INT]["/"] = lambda x, y: Value(
            x.type(), x.value() // y.value()
        )
        self.op_to_lambda[Type.INT]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.INT]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )
        self.op_to_lambda[Type.INT]["<"] = lambda x, y: Value(
            Type.BOOL, x.value() < y.value()
        )
        self.op_to_lambda[Type.INT]["<="] = lambda x, y: Value(
            Type.BOOL, x.value() <= y.value()
        )
        self.op_to_lambda[Type.INT][">"] = lambda x, y: Value(
            Type.BOOL, x.value() > y.value()
        )
        self.op_to_lambda[Type.INT][">="] = lambda x, y: Value(
            Type.BOOL, x.value() >= y.value()
        )
        
        # def coerce_and_op(x, y, op):
        #     x_val = self.int_to_bool_coercion(x) if x.type() == Type.INT else x.value()
        #     y_val = self.int_to_bool_coercion(y) if y.type() == Type.INT else y.value()
        #     return Value(Type.BOOL, op(x_val, y_val))

        # self.op_to_lambda[Type.INT]["&&"] = lambda x, y: coerce_and_op(x, y, lambda a, b: a and b)
        # self.op_to_lambda[Type.INT]["||"] = lambda x, y: coerce_and_op(x, y, lambda a, b: a or b)
        # self.op_to_lambda[Type.BOOL]["&&"] = lambda x, y: coerce_and_op(x, y, lambda a, b: a and b)
        # self.op_to_lambda[Type.BOOL]["||"] = lambda x, y: coerce_and_op(x, y, lambda a, b: a or b)

        #  set up operations on strings
        self.op_to_lambda[Type.STRING] = {}
        self.op_to_lambda[Type.STRING]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.STRING]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.STRING]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )
        #  set up operations on bools
        self.op_to_lambda[Type.BOOL] = {}
        self.op_to_lambda[Type.BOOL]["&&"] = lambda x, y: Value(
            x.type(), x.value() and y.value()
        )
        self.op_to_lambda[Type.BOOL]["||"] = lambda x, y: Value(
            x.type(), x.value() or y.value()
        )
        self.op_to_lambda[Type.BOOL]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.BOOL]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

        #  set up operations on nil
        self.op_to_lambda[Type.NIL] = {}
        self.op_to_lambda[Type.NIL]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.NIL]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

    def __do_if(self, if_ast):
        cond_ast = if_ast.get("condition")
        result = self.__eval_expr(cond_ast)

        if result.type() == Type.INT:
            result = Value(Type.BOOL, self.int_to_bool_coercion(result))

        if result.type() != Type.BOOL:
            super().error(
                ErrorType.TYPE_ERROR,
                "Incompatible type for if condition",
            )
        if result.value():
            statements = if_ast.get("statements")
            status, return_val = self.__run_statements(statements)
            return (status, return_val)
        else:
            else_statements = if_ast.get("else_statements")
            if else_statements is not None:
                status, return_val = self.__run_statements(else_statements)
                return (status, return_val)

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __do_for(self, for_ast):
        init_ast = for_ast.get("init") 
        cond_ast = for_ast.get("condition")
        eval_cond = self.__eval_expr(cond_ast)
        update_ast = for_ast.get("update") 

        if eval_cond.type() == Type.INT:
            if self.trace_output:
                print("CONDITION IS OF TYPE INTEGER")
            eval_cond = Value(Type.BOOL, self.int_to_bool_coercion(eval_cond))
        if eval_cond.type() != Type.BOOL:
            super().error(ErrorType.TYPE_ERROR, description="loop condition not compatible w/ brewin")

        self.__run_statement(init_ast)  # initialize counter variable
        run_for = Interpreter.TRUE_VALUE
        while run_for.value():
            run_for = self.__eval_expr(cond_ast)  # check for-loop condition

            if run_for.type() == Type.INT:
                if self.trace_output:
                    print("CONDITION IS OF TYPE INTEGER")
                run_for = Value(Type.BOOL, self.int_to_bool_coercion(run_for))

            if run_for.type() != Type.BOOL:
                super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible type for for condition",
                )
            if run_for.value():
                statements = for_ast.get("statements")
                status, return_val = self.__run_statements(statements)
                if status == ExecStatus.RETURN:
                    return status, return_val
                self.__run_statement(update_ast)  # update counter variable

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __do_return(self, return_ast):
        expr_ast = return_ast.get("expression")
        if expr_ast is None:
            if self.trace_output:
                print("RETURN IS NONE?!?!?!?!?!!?!?")
            return (ExecStatus.RETURN, Interpreter.NIL_VALUE)
        value_obj = copy.copy(self.__eval_expr(expr_ast))
        return (ExecStatus.RETURN, value_obj)

test_program = """

func foo() : bool {
    return false;
}

func bar() : int {
    return 1;
}

func nilreturner123() : void {
    print("nilreturner123() running rn");
}

func defaultIntReturner() : int {
    print("defaultIntReturner() running rn");
}

func defaultBoolReturner() : bool {
    print("defaultBoolReturner() running rn");
}

func defaultStringReturner() : string {
    print("defaultStringReturner() running rn");
}

func testParams(a:bool) : int {
    print("a: ", a);
    return a + 5;
}

func main() : void{
    print("BEGIN THE DEBUGGING=======================================================================");

    var eyeballs: int; /* default is 0 */
    var theory: string; /* default is "" */
    var old: bool; /* default is false */
    
    print(eyeballs);
    eyeballs = 5;
    print(eyeballs);

    print("theory: ", theory);
    print("old: ", old);

    print("THIS IS VALID============================");
    old = eyeballs;
    if (old) {
        print("old is true!");
    } else {
        print("old is false!");
    }

    var i : int;
    for (i = 5; i; i = i - 1) {
        print("i: ", i);
    }

    var tester : int;
    tester = 1; 
    if (tester == true) {
        print("yup tester is true!");
    } else {
        print("tester is false!");
    }

    print("TAKBIR'S TEST CASES FOR ASSIGNMENTS=================================================================================================");

    /* Equality and Inequality tests with coercion */
    print(0 == false);        /* Expected: true (0 is coerced to false) */
    print(1 == true);         /* Expected: true (1 is coerced to true) */
    print(42 == true);        /* Expected: true (42 is non-zero, coerced to true) */
    print(-1 == true);        /* Expected: true (-1 is non-zero, coerced to true) */
    print(0 != true);         /* Expected: true (0 is coerced to false, not equal to true) */
    print(1 != false);        /* Expected: true (1 is coerced to true, not equal to false) */
    print(0 != false);        /* Expected: false (0 is coerced to false) */
    print("==========");
    
    /* Logical AND (&&) and OR (||) with coercion */
    print(0 && false);        /* Expected: false (0 is coerced to false, false && false is false) */
    print(1 && true);         /* Expected: true (1 is coerced to true, true && true is true) */
    print(0 || true);         /* Expected: true (0 is coerced to false, false || true is true) */
    print(0 || false);        /* Expected: false (0 is coerced to false, false || false is false) */
    print(42 && false);       /* Expected: false (42 is coerced to true, true && false is false) */
    print(42 || false);       /* Expected: true (42 is coerced to true, true || false is true) */
    print("==========");
    
    /* Nested expressions with coerced booleans */
    print((0 || 1) && true);  /* Expected: true ((0 || 1) coerces to true, true && true is true) */
    print((0 && 1) || true);  /* Expected: true ((0 && 1) coerces to false, false || true is true) */
    print(0 || (0 && true));  /* Expected: false (0 || (false) is false) */
    print(1 && (0 || true));  /* Expected: true (1 coerces to true, true && true is true) */
    print("==========");
    
    /* Comparison with multiple types */
    print((0 == false) && (1 == true));  /* Expected: true (both coerced comparisons are true) */
    print((0 != true) || (1 != false));  /* Expected: true (both coerced comparisons are true) */
    print((0 && foo()) == false);        /* Expected: true (0 is coerced to false, foo() returns false, (false && false) == false is true) */
    print((1 && foo()) != true);         /* Expected: true (1 is coerced to true, foo() returns false, (true && false) != true is true) */
    print((1 || foo()) != true);         /* Expected: false (1 is coerced to true, foo() returns false, (true || false) != true is false) */
    print(bar());
    print(bar() == false); /* should be false */
    print("END OF TAKBIR'S TEST CASES FOR ASSIGNMENTS=================================================================================================");

    print(nilreturner123());
    print("defaultIntReturner: ", defaultIntReturner());
    print("defaultBoolReturner: ", defaultBoolReturner());
    print("defaultStringReturner: ", defaultStringReturner());

    var a : int;
    a = 5;
    print(testParams(a));
}
"""

# var n: node;  /* default is nil */ 
# print("THIS SHOULD ERROR=======================");
#     eyeballs = "bruh"; /* NOT SUPPORTED!!! */
#     print(eyeballs);

new_interpreter = Interpreter(console_output = True, inp = None, trace_output = True)
new_interpreter.run(test_program)