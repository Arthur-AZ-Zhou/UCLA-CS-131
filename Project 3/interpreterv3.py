
import copy
from enum import Enum
from copy import deepcopy
from collections import defaultdict, deque

from env_v2 import EnvironmentManager
from type_valuev2 import *
from intbase import InterpreterBase, ErrorType
from brewparse import parse_program

# class ExecStatus(Enum):
#     CONTINUE = 1
#     RETURN = 2

class Interpreter(InterpreterBase):
    NIL_VALUE = create_value(InterpreterBase.NIL_DEF)
    TRUE_VALUE = create_value(InterpreterBase.TRUE_DEF)
    BIN_OPS = {"+", "-", "*", "/", "==", "!=", ">", ">=", "<", "<=", "||", "&&"}

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.type_manager = Type()
        self.__setup_ops() 

    def run(self, program):
        Type().reset_struct_types() #CLEAN UP FROM BEFORE HOLY THIS ALMOST MURDERED MY TEST CASES
        if self.trace_output:
            print("REMAINING STRUCT_TYPES??!?!: ", Type.struct_types)

        ast = parse_program(program)
        self.process_structs(ast) 
        self.__set_up_function_table(ast)

        main_func = self.__get_func_by_name("main", [])
        self.env = EnvironmentManager()
        self.env.environment[-1]["return"] = Type.VOID
        if self.trace_output:
            print("MAIN'S RETURN TYPE: ", main_func.get("return_type"))
        self.must_return = False
        self.__run_statements(main_func.get("statements"))

    def valid_type_var(self, var_type): # MUST INITIALIZE DEFAULT TYPES
        valid_types = {InterpreterBase.INT_NODE, InterpreterBase.BOOL_NODE, InterpreterBase.STRING_NODE}
        return var_type in valid_types or var_type in self.type_manager.struct_types.keys()

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
        else:  # STRUCTS BUT COME BACK TO THIS LATER=======================
            return Value(type=default_var, value=Type.NIL)

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

    def process_structs(self, ast):
        for struct_node in ast.get("structs"):
            node_struct_fields = {}

            name_struct = struct_node.get("name")
            if self.trace_output:
                print("NAME STRUCT: ", name_struct)

            self.type_manager.add_struct_type(name_struct) # for non-primitives
            node_struct_fields = self.process_struct_fields(struct_node, name_struct)
            self.type_manager.add_struct(name_struct, node_struct_fields)

    def process_struct_fields(self, struct_node, name_struct):  
        struct_fields = {}
        
        for field in struct_node.get("fields"):
            field_name = field.get("name")
            var_type_field = field.get("var_type")
            if self.trace_output:
                print("FIELD VARIABLE TYPE: ", var_type_field)

            if var_type_field in self.type_manager.struct_types:
                if self.trace_output:
                    print("WE HAVE TO PRIORITIZE NON PRIMMIE TYPES: ", var_type_field)
                struct_fields[field_name] = Value(var_type_field, Type.NIL)
            elif var_type_field in [Type.INT, Type.BOOL, Type.STRING]:
                struct_fields[field_name] = self.defaults(var_type_field)
            else:
                super().error(ErrorType.TYPE_ERROR, description=f"Invalid type {var_type_field} when defining {name_struct}")
        return struct_fields

    def __set_up_function_table(self, ast):
        # self.func_name_to_ast = {}
        self.func_name_to_ast = defaultdict(dict)
        
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

    def __get_func_by_name(self, name, params):
        num_params = len(params)

        if name not in self.func_name_to_ast:
            super().error(ErrorType.NAME_ERROR, description=f"Function {name} not found")
        if num_params not in self.func_name_to_ast[name]:
            super().error(ErrorType.NAME_ERROR, description=f"Function {name} taking {num_params} args not found")

        self.check_arg_types(params, self.func_name_to_ast[name][num_params].get("args"))

        return self.func_name_to_ast[name][num_params]

    def check_arg_types(self, args, formal_args):
        num_args = len(args)

        for i in range(num_args):
            arg = self.__eval_expr(args[i])
            if arg.type() != formal_args[i].get("var_type"):
                if self.trace_output:
                    print("CHECKING FOR COERCION FOR TYPES:")
                    print("arg.type(): ", arg.type())
                    print("formal_args[i].get('var_type'): ",formal_args[i].get("var_type"))

                if not ((arg.type() == Type.INT and formal_args[i].get("var_type") == Type.BOOL)
                    or (arg.type() == Type.NIL and formal_args[i].get("var_type") in self.type_manager.struct_types)):
                    super().error(
                        ErrorType.TYPE_ERROR, description=f"Type mismatch on formal parameter {formal_args[i].get('name')}")

    def __run_statements(self, statements):
        self.env.push_block()
        return_val = Value(Type.NIL, None)

        for statement in statements:
            if self.trace_output:
                print("CURRENT STATEMENT: ", statement)

            return_val = self.__run_statement(statement)
            if self.must_return:
                break

        self.env.pop_block()

        if self.env.is_in_function(-1):
            return_type = self.env.environment[-1]["return"]
            
            if self.trace_output:
                print("EXPECTED_RETURN_TYPE: ", return_type, " ====================================================")
                print("current struct types: ", self.type_manager.struct_types)
                print("should this trigger structs?!?!?!: ", return_val.type() == Type.NIL and return_type in self.type_manager.struct_types)
            if not self.must_return or return_val.value() is None: #DEFAULTS TO WHATEVER
                return_val = self.defaults(return_type)
            self.must_return = False

            if return_val.type() != return_type:
                if return_val.type() == Type.INT and return_type == Type.BOOL:
                    return_val = Value(Type.BOOL, self.int_to_bool_coercion(return_val))
                elif return_val.type() == Type.NIL and return_type in self.type_manager.struct_types:
                    if self.trace_output:
                        print("INFERNO TRIGGER")
                    return_val = Value(return_type, Type.NIL)
                else: 
                    super().error(ErrorType.TYPE_ERROR, description=f"Returned value's type {return_val.type()} is inconsistent with function's return type {return_type}")
        
        return return_val

    def __run_statement(self, statement):
        return_val = None

        if statement.elem_type == InterpreterBase.FCALL_NODE:
            return_val = self.__call_func(statement)

            if self.must_return:
                return return_val
        elif statement.elem_type == "=":
            self.__assign(statement)
        elif statement.elem_type == InterpreterBase.VAR_DEF_NODE:
            self.__var_def(statement)
        elif statement.elem_type == InterpreterBase.RETURN_NODE:
            return_val = self.__do_return(statement)

            self.must_return = True
            return return_val
        elif statement.elem_type == InterpreterBase.IF_NODE:
            return_val = self.__do_if(statement)

            if self.must_return:
                return return_val
        elif statement.elem_type == InterpreterBase.FOR_NODE:
            return_val = self.__do_for(statement)

            if self.must_return:
                return return_val

        return return_val

    def __call_func(self, call_node): #TAKES CARE OF BASIC FUNCTIONS
        func_name = call_node.get("name")
        actual_args = call_node.get("args")

        if self.trace_output:
            print("CALLNODE: ", call_node)
            print("func_name: ", func_name)
            print("actual_args: ", actual_args)

        if func_name == "print":
            return self.__call_print(actual_args)
        elif func_name in ["inputi", "inputs"]:
            return self.__call_input(func_name, actual_args)
        elif func_name in self.func_name_to_ast:
            return self.__call_func_aux(self.__get_func_by_name(func_name, actual_args), actual_args)
        else:
            super().error(ErrorType.NAME_ERROR, f"Function {func_name} not found")

    def __call_func_aux(self, func_node, args):
        all_params = func_node.get("args")
        statements = func_node.get("statements")
        return_type = func_node.get("return_type")

        arg_map = {}  # maps params to respective arguments
        self.env.push_block()
        self.env.environment[-1]["return"] = return_type
        self.must_return = False

        for i in reversed(range(len(args))):
            if self.trace_output:
                print("i: ", i)
                print("actual_args: ", actual_args)
                print("formal_args: ", formal_args)
                print("actual_args[i]'s type HOLY SHIT THIS WAS FUCKING: ", self.__eval_expr(actual_args[i]).type())
                print("formal_args[i].get('var_type'): ", formal_args[i].get('var_type'))

            formal_args = all_params[i].get("name")
            actual_arg = self.__eval_expr(args[i])
            if actual_arg.type() == Type.VOID:
                super().error(ErrorType.TYPE_ERROR, description="Void cannot be arg")
            if (actual_arg.type() == Type.INT and all_params[i].get("var_type") == InterpreterBase.BOOL_NODE):
                actual_arg = Value(Type.BOOL, self.int_to_bool_coercion(actual_arg))
            arg_map[formal_args] = actual_arg

        self.env.environment[-1]["isFunctionCall"] = True

        for formal_args, actual_arg in arg_map.items():
            self.env.create(formal_args, actual_arg)

        res = self.__run_statements(statements)
        self.env.pop_block() 
        return res

    def __call_print(self, args):
        output = ""

        for arg in args:
            result = self.__eval_expr(arg)  # result is a Value object
            if result.type() == Type.VOID:
                super().error(ErrorType.TYPE_ERROR, description="Void not allowed as an argument")
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
        full_var_name = assign_ast.get("name")
        var_name_and_keys = full_var_name.split(".")
        var_name = var_name_and_keys[0]
        
        var_obj = self.get_variable_including_structs(assign_ast)
        if not var_obj:
            super().error(ErrorType.NAME_ERROR, f"Undefined variable {var_name}")
        
        value_obj = self.__eval_expr(assign_ast.get("expression"))
        
        self._handle_type_mismatch(var_obj, value_obj)
        
        if not self.env.set(full_var_name, value_obj):
            super().error(ErrorType.NAME_ERROR, f"Undefined variable {var_name} in assignment")

    def _handle_type_mismatch(self, var_obj, value_obj):
        if var_obj.type() != value_obj.type():
            if var_obj.type() == Type.BOOL and value_obj.type() == Type.INT:
                value_obj = Value(Type.BOOL, self.int_to_bool_coercion(value_obj))
            elif var_obj.type() in self.type_manager.struct_types and value_obj.type() == Type.NIL:
                value_obj = Value(var_obj.type(), Type.NIL)
            else:
                super().error(ErrorType.TYPE_ERROR, description=f"Type mismatch between {var_obj.type()} vs {value_obj.type()} in assignment")

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
            return self.__run_statements(statements)
        else:
            else_statements = if_ast.get("else_statements")
            if else_statements is not None:
                return self.__run_statements(else_statements)

        return Interpreter.NIL_VALUE

    def __do_for(self, for_ast):
        init_ast = for_ast.get("init")
        self.__assign(init_ast) #WE REQUIRE THIS FOR NON PRIMITIVE END CONS
        cond_ast = for_ast.get("condition")
        eval_cond = self.__eval_expr(cond_ast)
        update_ast = for_ast.get("update")

        if eval_cond.type() == Type.INT:
            if self.trace_output:
                print("CONDITION IS OF TYPE INTEGER")
            eval_cond = Value(Type.BOOL, self.int_to_bool_coercion(eval_cond))
        elif eval_cond.type() != Type.BOOL:
            super().error(ErrorType.TYPE_ERROR, description="loop condition not compatible w/ brewin")

        # Main loop execution
        res = Value(Type.NIL, None)
        while True:
            # Evaluate condition
            eval_cond = self.__eval_expr(cond_ast)
            if eval_cond.type() == Type.INT:
                eval_cond = Value(Type.BOOL, self.int_to_bool_coercion(eval_cond))
            elif eval_cond.type() != Type.BOOL:
                super().error(
                    ErrorType.TYPE_ERROR, description="Incompatible type for loop condition"
                )

            # Exit loop if condition is False
            if not eval_cond.value():
                break

            # Execute loop body
            res = self.__run_statements(for_ast.get("statements"))
            if self.must_return:
                if self.trace_output:
                    print("WE EXIT NOW under condition: ", eval_cond)
                break

            # Update counter variable
            self.__assign(update_ast)

        return res

    def __do_return(self, return_ast):
        expr_ast = return_ast.get("expression")

        if expr_ast is None:
            if self.trace_output:
                print("RETURN IS NONE?!?!?!?!?!!?!?")
            return Interpreter.NIL_VALUE
        return copy.copy(self.__eval_expr(expr_ast))

    def __eval_expr(self, expr_ast):
        if expr_ast.elem_type == InterpreterBase.NIL_NODE:
            if self.trace_output:
                print("NILL NODE TRIGGER")
            return Value(Type.NIL, Type.NIL)
        if expr_ast.elem_type == InterpreterBase.INT_NODE:
            if self.trace_output:
                print("INT NODE TRIGGER")
            return Value(Type.INT, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.STRING_NODE:
            if self.trace_output:
                print("STRING NODE TRIGGER")
            return Value(Type.STRING, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.BOOL_NODE:
            if self.trace_output:
                print("BOOL NODE TRIGGERE")
            return Value(Type.BOOL, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.VAR_NODE:
            return self.get_variable_including_structs(expr_ast)

            # # print("VAR NODE TRIGGER")
            # var_name = expr_ast.get("name")
            # # if self.trace_output:
            # #     print("var_name: ", var_name)
            # val = self.env.get(var_name)
            # # if self.trace_output:
            # #     print("val: ", val)
            # if val is None:
            #     super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
            # return val
        if expr_ast.elem_type == InterpreterBase.FCALL_NODE:
            if self.trace_output:
                print("FCALL NODE TRIGGERE")
            return self.__call_func(expr_ast)
            
        if expr_ast.elem_type in self.BIN_OPS:
            return self.__eval_op(expr_ast)
        if expr_ast.elem_type == InterpreterBase.NEG_NODE:
            return self.__eval_unary(expr_ast, [Type.INT], lambda x: -1 * x)
        if expr_ast.elem_type == InterpreterBase.NOT_NODE:
            return self.__eval_unary(expr_ast, [Type.BOOL, Type.INT], lambda x: not x)
        if expr_ast.elem_type == InterpreterBase.NEW_NODE:
            return self.create_new_struct(expr_ast)

    def get_variable_including_structs(self, var_ast):
        full_var_name = var_ast.get("name")
        var_name_and_keys = full_var_name.split(".")
        var_name = var_name_and_keys[0]

        val = self.env.get(var_name)
        if self.trace_output:
            print("VAR NAME: ", var_name)
            print("VAR KEYS: ", var_name_and_keys[1:])
            print("VAL OF VAR NAME: ", val.value())

        if val == None:
            super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")

        for key in var_name_and_keys[1:]:
            if self.trace_output:
                print("Resolving key:", key)

            if val.type() == Type.NIL:
                super().error(ErrorType.FAULT_ERROR, description=f"Error dereferencing nil value in {full_var_name}")

            if val.type() not in self.type_manager.struct_types:
                super().error(ErrorType.TYPE_ERROR, description=f"Dot used with non-struct in {full_var_name}")
            struct = val.value()

            if not isinstance(struct, dict):
                super().error(ErrorType.FAULT_ERROR, description=f"Error dereferencing {struct} value in {full_var_name}")
            if key not in struct:
                super().error(ErrorType.NAME_ERROR, description=f"Unknown member {key} in {full_var_name}")

            val = struct[key]
            if self.trace_output:
                print(f"Resolved {key}: {val.value()}")
                
        return val

    def create_new_struct(self, new_ast):
        struct_type = new_ast.get("var_type")
        if struct_type not in self.type_manager.struct_types:
            super().error(ErrorType.TYPE_ERROR, description=f"Invalid type {struct_type} for new operation")
        struct = self.type_manager.get_struct(struct_type)
        return Value(struct_type, deepcopy(struct))

    def __eval_unary(self, arith_ast, valid_types, operation):
        value_obj = self.__eval_expr(arith_ast.get("op1"))
        if value_obj.type() not in valid_types:
            super().error(ErrorType.TYPE_ERROR, f"Incompatible type for {arith_ast.elem_type} operation")

        result_type = Type.BOOL if arith_ast.elem_type == InterpreterBase.NOT_NODE else value_obj.type()
        return Value(result_type, operation(value_obj.value()))

    def __eval_op(self, arith_ast):
        operator = arith_ast.elem_type
        left_value_obj: Value = self.__eval_expr(arith_ast.get("op1"))
        right_value_obj: Value = self.__eval_expr(arith_ast.get("op2"))

        if self.trace_output:
            print("ENTERED EVAL")
            print("LEFT: ", left_value_obj)
            print("AWP: ", operator)
            print("right: ", right_value_obj)

        def valid_binary(op1: Value, op, op2: Value): # HANDLES ALL STRUCTS
            COERCABLES = [Type.BOOL, Type.INT]
            STRUCTS = set(self.type_manager.struct_types.keys()).union({Type.NIL})

            if op in {"==", "!="}:
                if op1.type() in COERCABLES and op2.type() in COERCABLES:
                    return True
                if op1.type() in STRUCTS and op2.type() in STRUCTS:
                    if op1.type() == Type.NIL or op2.type() == Type.NIL:
                        return True

                    return op1.type() == op2.type()

                return op1.type() == op2.type()

            if op in {"&&", "||"}:
                return op1.type() in COERCABLES and op2.type() in COERCABLES
                
            return op1.type() == op2.type() and op in self.op_to_lambda.get(op1.type(), {})
            
        if valid_binary(left_value_obj, operator, right_value_obj):
            if self.trace_output:
                print("ENTERED VALID BINARY============================================")
                print("LEFT: ", left_value_obj)
                print("AWP: ", operator)
                print("right: ", right_value_obj)

            if operator in {"&&", "||"}:
                left_bool = self.int_to_bool_coercion(left_value_obj)
                right_bool = self.int_to_bool_coercion(right_value_obj)
                result = left_bool and right_bool if operator == "&&" else left_bool or right_bool
                return Value(Type.BOOL, result)

            if operator in {"==", "!="}:
                left_val = (
                    self.int_to_bool_coercion(left_value_obj)
                    if left_value_obj.type() in {Type.INT, Type.BOOL}
                    else left_value_obj.value()
                )
                right_val = (
                    self.int_to_bool_coercion(right_value_obj)
                    if right_value_obj.type() in {Type.INT, Type.BOOL}
                    else right_value_obj.value()
                )
                is_equal = left_val == right_val
                result = is_equal if operator == "==" else not is_equal
                return Value(Type.BOOL, result)

            f = self.op_to_lambda[left_value_obj.type()][operator]
            return f(left_value_obj, right_value_obj)
        else:
            super().error(
                ErrorType.TYPE_ERROR,
                description=f"Incompatible operator {operator} on {left_value_obj.type()} to {right_value_obj.type()}",
            )

    def __setup_ops(self):
        def struct_equality(x: Value, y: Value):
            if x.type() == y.type() and x.type() in self.type_manager.struct_types:
                return Value(Type.BOOL, x.value() is y.value())
            if x.type() == Type.NIL and y.type() in self.type_manager.struct_types:
                return Value(Type.BOOL, y.value() == Type.NIL)
            if y.type() == Type.NIL and x.type() in self.type_manager.struct_types:
                return Value(Type.BOOL, x.value() == Type.NIL)

            return Value(Type.BOOL, False)

        def struct_inequality(x: Value, y: Value):
            return Value(Type.BOOL, not struct_equality(x, y).value())

        self.op_to_lambda = defaultdict(dict)
        # INTS========================================================================
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
        self.op_to_lambda[Type.INT]["||"] = lambda x, y: Value(
            Type.BOOL, self.int_to_bool_coercion(x) or self.int_to_bool_coercion(y)
        )
        self.op_to_lambda[Type.INT]["&&"] = lambda x, y: Value(
            Type.BOOL, self.int_to_bool_coercion(x) and self.int_to_bool_coercion(y)
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

        # STRINGS======================================================
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

        # BOOLS=========================================================
        self.op_to_lambda[Type.BOOL] = {}
        self.op_to_lambda[Type.BOOL]["||"] = lambda x, y: Value(
            Type.BOOL, self.int_to_bool_coercion(x) or self.int_to_bool_coercion(y)
        )
        self.op_to_lambda[Type.BOOL]["&&"] = lambda x, y: Value(
            Type.BOOL, self.int_to_bool_coercion(x) and self.int_to_bool_coercion(y)
        )
        self.op_to_lambda[Type.BOOL]["=="] = lambda x, y: Value(
            Type.BOOL, self.int_to_bool_coercion(x) == self.int_to_bool_coercion(y)
        )
        self.op_to_lambda[Type.BOOL]["!="] = lambda x, y: Value(
            Type.BOOL, self.int_to_bool_coercion(x) != self.int_to_bool_coercion(y)
        )

        # NIL=======================================================================
        self.op_to_lambda[Type.NIL] = {}
        self.op_to_lambda[Type.NIL]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.NIL]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

        # legal struct operators: ==, !=
        for struct_type in self.type_manager.struct_types:
            self.op_to_lambda[struct_type]["=="] = struct_equality
            self.op_to_lambda[struct_type]["!="] = struct_inequality

# test_program = """
# struct node {
#     value: int;
#     next: node;
# }

# func main() : void {
#     var n : node;
#     var p : node;
#     var q : node; 
#     print(n);
#     n = new node;
#     p = new node;
#     q = new node;
#     n.value = 9;
#     print("DONE ASSIGNING 9 ===================================================");
#     n.next = p;
#     print(n.value);
#     p.value = 9;
#     print(p.value);
#     print(p.next);
#     print(n.next.value);
#     print("BEGIN CANCER LINE=====================================================");
#     n.next.next = q;
#     print("DONE WITH CANCER LINE==================================================");
#     n.next.next.value = 10;
#     print(p.next.value);
#     print(q.value + 1);
# }
# """

test_program1 = """
struct dog {
    name: string;
    vaccinated: bool;  
}

func main() : void {
    var d: dog;
    d = steal_dog(new dog, "Spots");
    print(d.name);

}

func steal_dog(d : dog, name: string) : dog {
    d.name = name;
    return d;
}
"""

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
    if ("bruh" == "bruh") {
        print("bruh true");
    }

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

    print("defaultIntReturner: ", defaultIntReturner());
    print("defaultBoolReturner: ", defaultBoolReturner());
    print("defaultStringReturner: ", defaultStringReturner());

    var a : int;
    a = 5;
    print(testParams(a));
}
"""

# new_interpreter = Interpreter(console_output = True, inp = None, trace_output = True)
# new_interpreter.run(test_program)
# print("BETWEEN WORLDS=======================================================================================")
# new_interpreter.run(test_program1)