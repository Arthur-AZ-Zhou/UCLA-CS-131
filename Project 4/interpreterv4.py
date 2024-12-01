import copy
from enum import Enum

from brewparse import parse_program
from env_v4 import EnvironmentManager
from intbase import InterpreterBase, ErrorType
from type_valuev4 import Type, Value, create_value, get_printable
from Lazy import Lazy


class ExecStatus(Enum):
    CONTINUE = 1
    RETURN = 2
    ERROR_CODE = 3

#WARNING EVERYTHING NOW REQUIRES YOU TO PUT A SNAPSHOT DICT FROM ADVICE VID
# REPLACE ALL self.env... with snapshot...
# for outputs need to use super(Interpreter, self)...?
# for CERTAIN errors need to raise it to EvaledVal
class Interpreter(InterpreterBase):
    # constants
    NIL_VALUE = create_value(InterpreterBase.NIL_DEF)
    TRUE_VALUE = create_value(InterpreterBase.TRUE_DEF)
    BIN_OPS = {"+", "-", "*", "/", "==", "!=", ">", ">=", "<", "<=", "||", "&&"}

    # methods
    def __init__(self, console_output=True, inp=None, trace_output=False): #this should be unchanged
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.__setup_ops()

    # run a program that's provided in a string
    # usese the provided Parser found in brewparse.py to parse the program
    # into an abstract syntax tree (ast)
    def run(self, program):
        ast = parse_program(program)
        self.__set_up_function_table(ast)
        self.curr_snapshot_env = EnvironmentManager() # CURRENT SNAPSHOT
        main_result = self.__call_func_aux(self.curr_snapshot_env, "main", [])

        if main_result.get()[0] == True: #PRINT IF SUCCESSFUL FOR DEBUG
            if self.trace_output:
                print("PROGRAM: ", program, " SUCCESSFULLY RAN")
        else: 
            if self.trace_output:
                print("SHOULD RETURN AN ERROR")
            if isinstance(main_result.get()[1], str):
                super().error(ErrorType.FAULT_ERROR, f"FAULT ERROR IN PROGRAM ", program)
            else:
                super().error(main_result.get()[1], "")

    def __set_up_function_table(self, ast): #works on curr snapshot so we don't actually need to mark this
        self.func_name_to_ast = {}
        for func_def in ast.get("functions"):
            func_name = func_def.get("name")
            num_params = len(func_def.get("args"))
            if func_name not in self.func_name_to_ast:
                self.func_name_to_ast[func_name] = {}
            self.func_name_to_ast[func_name][num_params] = func_def

    def __get_func_by_name(self, snapshot, name, num_params):
        if name not in self.func_name_to_ast:
            super().error(ErrorType.NAME_ERROR, f"Function {name} not found")
        candidate_funcs = self.func_name_to_ast[name]
        if num_params not in candidate_funcs:
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {name} taking {num_params} params not found",
            )
        return candidate_funcs[num_params]

    def __run_statements(self, snapshot, statements):
        snapshot.push_block()

        # self.snapshot.push_block()
        # for statement in statements:
        #     if self.trace_output:
        #         print(statement)
        #         print("ENVIRONMENT LEVEL: ", snapshot, "\n")
        #     status, return_val = self.__run_statement(statement)
        #     if status == ExecStatus.RETURN:
        #         self.snapshot.pop_block()
        #         return (status, return_val)

        # self.snapshot.pop_block()
        # return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

        try: #try catch for errors
            for statement in statements:
                if self.trace_output:
                    print("ENVIRONMENT LEVEL: ", snapshot, "\n")
                    print(statement)

                status, return_val = self.__run_statement(snapshot, statement)
                if status == ExecStatus.ERROR_CODE or status == ExecStatus.RETURN:
                    return (status, return_val)
        finally:
            snapshot.pop_block()
            # return self.get_exec_result()       

        return self.nil_exec_result(snapshot)  

    # def __run_statement(self, statement):
    def __run_statement(self, snapshot, statement):
        status, return_val = self.nil_exec_result(snapshot)
        # status = ExecStatus.CONTINUE
        # return_val = None

        #cancer part=======================================================================================
        if statement.elem_type == InterpreterBase.FCALL_NODE:
            fcall_result = self.__call_func(snapshot, statement).get() #get value of fcall function
            # if  self.__call_func(snapshot, statement).get()[0] == False:
            #     print("wtf is going on")
            #     status, return_val = ExecStatus.ERROR_CODE, Lazy(lambda:  self.__call_func(snapshot, statement).get())

            if fcall_result[0] == False:
                status, return_val = ExecStatus.ERROR_CODE, Lazy(lambda: fcall_result)
            return status, return_val
        #end of cancer part=======================================================================================
        
        elif statement.elem_type == "=":
            self.__assign(snapshot, statement)
            return status, return_val
        elif statement.elem_type == InterpreterBase.VAR_DEF_NODE:
            self.__var_def(snapshot, statement)
            return status, return_val
        elif statement.elem_type == InterpreterBase.RETURN_NODE:
            status, return_val = self.__do_return(snapshot, statement)
            return status, return_val
        elif statement.elem_type == Interpreter.IF_NODE:
            status, return_val = self.__do_if(snapshot, statement)
            return status, return_val
        elif statement.elem_type == Interpreter.FOR_NODE:
            status, return_val = self.__do_for(snapshot, statement)
            return status, return_val
        elif statement.elem_type == Interpreter.RAISE_NODE:
            status, return_val = self.do_raise(snapshot, statement)
            return status, return_val
        elif statement.elem_type == Interpreter.TRY_NODE:
            status, return_val = self.do_try_catch(snapshot, statement)
            return status, return_val
        else:
            super().error(ErrorType.NAME_ERROR, f"Statement: {statement} is of unknown type")
            return self.nil_exec_result()

        # return status, return_val
        if self.trace_output:
            print("SHOULD NEVER GET HERE")
        return self.nil_exec_result(snapshot)

    def nil_exec_result(self, snapshot):
        # return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)
        ret_lazy_val = Lazy(lambda: (True, Interpreter.NIL_VALUE))
        if self.trace_output:
            print("ret_lazy_val: ", ret_lazy_val)
        return (ExecStatus.CONTINUE, ret_lazy_val)

    def error_response_result(self, error_type, message):
        return (ExecStatus.ERROR_CODE, Lazy(lambda: (False, error_type)))

    def val_exec_result(self, snapshot, value):
        return Lazy(lambda: (True, value))

    def exec_expression(self, snapshot, expr):
        return self.__eval_expr(snapshot, expr).get()
    
    def __call_func(self, snapshot, call_node):
        func_name = call_node.get("name")
        actual_args = call_node.get("args")
        return self.__call_func_aux(snapshot, func_name, actual_args)

    def __call_func_aux(self, snapshot, func_name, actual_args):
        if func_name in ["print", "inputi", "inputs"]: #Take care of basic functions
            return self.handle_basic_funcs(snapshot, func_name, actual_args)

        # saved_snapshot = EnvironmentManager()

        # for func_scope in self.snapshot:
        #     self.copy_func_scope(func_scope, copied_env)
        # if self.trace_output:
        #     print("FINAL COPIED ENVIRONMENT: ", copied_env)
        # saved_snapshot = snapshot.copy()
        saved_snapshot = snapshot.deep_copy_environment() #saves lambda func in this singular snapshot
        if self.trace_output:
            if saved_snapshot is None:
                print("SAVED SNAPSHOT IS NOTHING")
            else:
                print("SAVED SNAPSHOT: ", saved_snapshot)

        def lambda_func():
            return self.handle_user_defined_funcs(saved_snapshot, func_name, actual_args)

        return Lazy(lambda_func)

    def handle_basic_funcs(self, snapshot, func_name, actual_args):
        # if self.trace_output:
        if func_name == "print":
            return self.__call_print(snapshot, actual_args)
        elif func_name in {"inputi", "inputs"}:
            return self.__call_input(snapshot, func_name, actual_args)
        
        if self.trace_output:
            print("WE SHOULD NEVER BE HERE")
        super().error(ErrorType.NAME_ERROR, f"NO FUNCTION WITH NAME {func_name}") #should never get here

    def handle_user_defined_funcs(self, snapshot, func_name, actual_args):
        func_ast = self.__get_func_by_name(snapshot, func_name, len(actual_args))
        formal_args = func_ast.get("args")
        if self.trace_output:
            print("LENGTH OF FORMAL ARGS: ", len(formal_args))
            print("FORMAL ARGS: ", formal_args)

        if len(actual_args) != len(formal_args):
            return (False, ErrorType.NAME_ERROR)
        args = self.process_args(snapshot, formal_args, actual_args)

        # then create the new activation record 
        snapshot.push_func()
        # and add the formal arguments to the activation record

        for arg_name, value in args.items():
        # for arg_name, value in args.keys():
        #     snapshot.set(arg_name, value)
        #     if self.trace_output:
        #         print("NEW ROTATION========================")
        #         print("ARG NAME: ", arg_name)
        #         print("VALUE: ", value)
            snapshot.create(arg_name, value)
        # snapshot.clear_all()

        _, return_val = self.__run_statements(snapshot, func_ast.get("statements"))
        snapshot.pop_func()
        # return return_val
        return return_val.get()

    def process_args(self, snapshot, formal_args, actual_args):
        args = {}
        for formal_ast, actual_ast in zip(formal_args, actual_args):
            arg_name = formal_ast.get("name")
            args[arg_name] = self.__eval_expr(snapshot, actual_ast)

        # if self.trace_output:
        #     print(args)
        return args
        
    def __call_print(self, snapshot, args):
        def lambda_func():
            formatted_output = self.eval_to_print_args(snapshot, args)
            if self.trace_output:
                print("FORMATTED OUTPUT: [", formatted_output, "]")
                
            if isinstance(formatted_output, tuple) and (formatted_output[0] == False):
                if self.trace_output:
                    print("EVAL NOT SUCCESSFUL AT lambda_func() LEVEL")
                return formatted_output
                
            # super().output(formatted_output)
            super(Interpreter, self).output(formatted_output) # output at current interpreter level and search up rather than base down
            return (True, Interpreter.NIL_VALUE)

        return Lazy(lambda_func)

    def eval_to_print_args(self, snapshot, args):
        output = ""

        for arg in args:
            # print("INDIVIDUAL ARG: ", arg)
            result = self.exec_expression(snapshot, arg)
            if result[0] == False:
                if self.trace_output:
                    print("EVAL NOT SUCCESSFUL AT eval_to_print_args() LEVEL")
                return result
            output += get_printable(result[1])
            # if result[0] == False:
            #     return result

        return output

    def __call_input(self, snapshot, name, args): #Only thing we really have to do is encapsulate the entire thing
        if self.trace_output:
            print("encapsulating lambda for input:")

        def lambda_func(): #only evaluate this when it gets called
            if args is not None and len(args) == 1:
                if self.trace_output and args is not None:
                    print("ARGS IS NOT NONE FOR ARGS", args)
                elif self.trace_output:
                    print("ARGS IS NONE")
                    
                first_arg = args[0]
                result = self.__eval_expr(snapshot, first_arg).get()
                if result[0] == False:
                    return result
                else:
                    fetched_result = result[1]
                super(Interpreter, self).output(get_printable(fetched_result))

            elif args is not None and len(args) > 1:
                return (False, ErrorType.NAME_ERROR)
                # super().error(ErrorType.NAME_ERROR, "No inputi() function that takes > 1 parameter")

            input_type = Type.NIL
            if name == "inputi":
                input_type = Type.INT
                return self.val_exec_result(snapshot, Value(Type.INT, int(super(Interpreter, self).get_input()))).get()
            if name == "inputs":
                input_type = Type.STRING
                return self.val_exec_result(snapshot, Value(Type.STRING, super(Interpreter, self).get_input())).get()

            if self.trace_output:
                print("SHOULD NEVER OCCUR=========================================================================================")
            return self.val_exec_result(snapshot, Value(input_type, int(super(Interpreter, self).get_input()))).get()

        return Lazy(lambda_func)

    def __assign(self, snapshot, assign_ast):
        var_name = assign_ast.get("name")
        # value_obj = Lazy(lambda: self.__eval_expr(assign_ast.get("expression")).get())
        ast_expr = assign_ast.get("expression")
        value_obj = self.__eval_expr(snapshot, ast_expr) 
        if self.trace_output:
            print("NAME AND VALUES: =======================================================================")
            print("NAME: ", var_name)
            print("VALUE: ", value_obj)
        
        if not snapshot.set(var_name, value_obj): # Connor said no self.snapshot.set(...)??? 
            if self.trace_output: # OH BECAUSE WE ARE OPERATING ON OUR OWN SNAPSHOT RN
                print("CURR SNAPSHOT: ", snapshot[-1] if not None else "NO SNAPSHOT")
            super().error(ErrorType.NAME_ERROR, f"Undefined variable {var_name} in assignment")
    
    def __var_def(self, snapshot, var_ast):
        var_name = var_ast.get("name")
        status, lazy_eval = self.nil_exec_result(snapshot)
        if self.trace_output:
            print("LAZY EVALUATION: ", lazy_eval)

        # if not self.env.create(var_name, Interpreter.NIL_VALUE):
        if not snapshot.create(var_name, lazy_eval):
            super().error(ErrorType.NAME_ERROR, f"Duplicate definition for variable {var_name}", f"LAZY EVAL: {lazy_eval}")

    def __eval_expr(self, snapshot, expr_ast):
        ast_val = expr_ast.get("val")

        # if expr_ast.elem_type == InterpreterBase.NIL_NODE:
        #     return Lazy(lambda: Interpreter.NIL_VALUE)
        # if expr_ast.elem_type == InterpreterBase.INT_NODE:
        #     return Lazy(lambda: Value(Type.INT, ast_val))
        # if expr_ast.elem_type == InterpreterBase.STRING_NODE:
        #     return Lazy(lambda: Value(Type.STRING, expr_ast.get("val")))
        # if expr_ast.elem_type == InterpreterBase.BOOL_NODE:
        #     return Lazy(lambda: Value(Type.BOOL, expr_ast.get("val")))
        if self.trace_output:
            print(ast_val if not None else "NO AST VALUE expr_ast.get('val')")
        saved_snapshot = snapshot.deep_copy_environment()
        # saved_snapshot = copy.deep_copy_environment(snapshot)
        if self.trace_output:
            print("SAVED SNAPSHOT: ", saved_snapshot)

        # LITERALS===============================================================================
        if expr_ast.elem_type == InterpreterBase.NIL_NODE:
            return self.nil_exec_result(snapshot)[1]
        if expr_ast.elem_type == InterpreterBase.INT_NODE:
            return Lazy(lambda: (True, Value(Type.INT, ast_val)))
        if expr_ast.elem_type == InterpreterBase.STRING_NODE:
            return Lazy(lambda: (True, Value(Type.STRING, ast_val)))
        if expr_ast.elem_type == InterpreterBase.BOOL_NODE:
            return Lazy(lambda: (True, Value(Type.BOOL, ast_val)))

        #MENTALLY INCOMPREHENSIBLE==============================================================
        if expr_ast.elem_type == InterpreterBase.VAR_NODE:
            if self.trace_output:
                print("WE ENTERED VAR NODE TRIGGER!!!!!!!!!!!!!!!!!!!!!!!!!!")
            return self.handle_var_node(saved_snapshot, expr_ast, )
        #MENTALLY INCOMPREHENSIBLE==============================================================
            
        # KEEP THESE UNCHANGED================================================================== (other than adding snapshot)
        if expr_ast.elem_type == InterpreterBase.FCALL_NODE:
            # print("WE ARE IN FCALL")
            return self.__call_func(saved_snapshot, expr_ast)
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            # print("WE ARE IN BIN")
            return self.__eval_op(saved_snapshot, expr_ast)
        if expr_ast.elem_type == Interpreter.NEG_NODE:
            # print("WE ARE IN NEGNODE")
            return self.__eval_unary(saved_snapshot, expr_ast, Type.INT, lambda x: -1 * x)
        if expr_ast.elem_type == Interpreter.NOT_NODE:
            # print("WE ARE IN NOTNODE")
            return self.__eval_unary(saved_snapshot, expr_ast, Type.BOOL, lambda x: not x)

        # if expr_ast.elem_type == InterpreterBase.FCALL_NODE:
        #     # if self.trace_output:
        #     #     print("WE ARE IN FCALL")
        #     return Lazy(lambda: self.__call_func(saved_snapshot, expr_ast))
        # if expr_ast.elem_type in Interpreter.BIN_OPS:
        #     # if self.trace_output:
        #     #     print("WE ARE IN BIN")
        #     return Lazy(lambda: self.__eval_op(saved_snapshot, expr_ast))
        # if expr_ast.elem_type == Interpreter.NEG_NODE:
        #     # if self.trace_output:
        #     #     print("WE ARE IN NEGNODE")
        #     return Lazy(lambda: self.__eval_unary(saved_snapshot, expr_ast, Type.INT, lambda x: -1 * x))
        # if expr_ast.elem_type == Interpreter.NOT_NODE:
        #     # if self.trace_output:
        #     #     print("WE ARE IN NOT")
        #     return Lazy(lambda: self.__eval_unary(saved_snapshot, expr_ast, Type.BOOL, lambda x: not x))

    def handle_var_node(self, snapshot, expr_ast):
        if self.trace_output:
            print("WE ENTERED VAR NODE TRIGGER!!!!!!!!!!!!!!!!!!!!!!!!!!")

        var_name = expr_ast.get("name")
        # var_name = expr_ast.get("var")
        value = snapshot.get(var_name)
        if self.trace_output:
            print("IS VAR NOME NONE?!")
            if var_name == None:
                print("VAR NAME IS NONE")
            else:
                print("VAR NAME: ", var_name)

        def lambda_func():
            if value is None:
                # return EvaledVal(True, (ErrorType.NAME_ERROR, f"Variable {var_name} not found")) # HOLY FUCK IM SOS TUPID
                return (False, ErrorType.NAME_ERROR)
            return value.get()

        return Lazy(lambda_func)

    def __eval_op(self, snapshot, arith_ast): #split this up into multiple steps
        def evaluate_operand(operator):
            value_obj = self.__eval_expr(snapshot, operator)
            
            if value_obj.get()[0] == True:
                if self.trace_output:
                    print("TRUE VAL OF LEFTMOST OBJECT: ", value_obj.get()[1])
                return value_obj.get()[1]
            return value_obj.get()

        def short_circuit(value_obj, operator): #remember only trues can short circuit || and falses can short circuit &&
            if self.trace_output:
                print("SHORT CIRCUITED ENTER")
            if value_obj == Value(Type.BOOL, True) and operator == "||":
                if self.trace_output:
                    print("|| WAS RESPONSIBLE, OUTPUT: TRUE")
                return (True, Value(Type.BOOL, True))
            if value_obj == Value(Type.BOOL, False) and operator == "&&":
                if self.trace_output:
                    print("&& WAS RESPONSIBLE, OUTPUT: FALSE")
                return (True, Value(Type.BOOL, False))

        def div_by_zero(left_value_obj, right_value_obj, operator):
            if operator == '/':
                if right_value_obj.type() == Type.INT and right_value_obj.value() == 0:
                    return (False, "div0")

        def check_type_compatibility(left_value_obj, right_value_obj, operator):
            if self.__compatible_types(operator, left_value_obj, right_value_obj) == False:
                return (False, ErrorType.TYPE_ERROR)

        def check_operator_compatibility(left_value_obj, operator):
            if operator not in self.op_to_lambda[left_value_obj.type()]:
                return (False, ErrorType.TYPE_ERROR)

        def perform_operation(left_value_obj, right_value_obj, operator):
            operator_func = self.op_to_lambda[left_value_obj.type()][operator]
            return (True, operator_func(left_value_obj, right_value_obj))

        def lambda_func():
            operator = arith_ast.elem_type

            left_value_obj = evaluate_operand(arith_ast.get("op1"))
            if isinstance(left_value_obj, tuple) and not left_value_obj[0]:
                return left_value_obj

            #MUST EVALUATE SHORT CIRCUIT BEFORE MOVING ONTO THE RIGHT
            short_circuit_result = short_circuit(left_value_obj, operator)
            if short_circuit_result != None:
                return short_circuit_result

            right_value_obj = evaluate_operand(arith_ast.get("op2"))
            if isinstance(right_value_obj, tuple) and not right_value_obj[0]:
                return right_value_obj

            div_zero_result = div_by_zero(left_value_obj, right_value_obj, operator)
            if div_zero_result != None:
                return div_zero_result

            type_check_result = check_type_compatibility(left_value_obj, right_value_obj, operator)
            if type_check_result != None:
                return type_check_result

            operator_check_result = check_operator_compatibility(left_value_obj, operator)
            if operator_check_result:
                return operator_check_result

            return perform_operation(left_value_obj, right_value_obj, operator)

        return Lazy(lambda_func)

    # def __compatible_types(self, snapshot, operator, obj1, obj2):
    def __compatible_types(self, oper, obj1, obj2): #WE SHOULD NOT NEED SNAPSHOT FOR THIS
        # DOCUMENT: allow comparisons ==/!= of anything against anything
        if oper in ["==", "!="]:
            return True
        return obj1.type() == obj2.type()

    def is_unary_compatible(self, value_obj, expected_type, arith_ast):
        # if unary_func in ["!", "-"]:
        #     return True
        return value_obj.type() == expected_type

    def eval_operand(self, snapshot, arith_ast):
        # operand = arith_ast.get("op2") 
        # if operand is None: 
        #     return None  
        # return self.__eval_expr(snapshot, operand) 
        return self.__eval_expr(snapshot, arith_ast.get("op1")).get()

    # def __eval_unary(self, snapshot, arith_ast, expected_type, unary_func):
    #     def lambda_func():
    #         value_obj = self.eval_operand(snapshot, arith_ast);
    #         if value_obj[0]: 
    #             return EvaledVal(False, (ErrorType.NAME_ERROR, "Operand evaluation failed"))

    #         if self.is_unary_compatible(value_obj, expected_type, arith_ast):  
    #             return EvaledVal(True, Value(expected_type, unary_func(value_obj[1].value()))) 

    #         return EvaledVal(False, (ErrorType.TYPE_ERROR, f"Incompatible type for {arith_ast.elem_type} operation"));

    #     return lambda_func

    def __eval_unary(self, snapshot, arith_ast, expected_type, unary_func):
        def lambda_func():
            value_obj = self.eval_operand(snapshot, arith_ast)
            if value_obj[0] == False:
                return value_obj

            if self.is_unary_compatible(value_obj[1], expected_type, arith_ast) == False:
                return (False, ErrorType.TYPE_ERROR)
            else:
                return (True, Value(expected_type, unary_func(value_obj[1].value())))

        return Lazy(lambda_func)

    def __setup_ops(self): #SHOULD NOT REQUIRE SNAPSHOT EITHER SINCE IT IS A 1 TIME THING
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

    def __do_if(self, snapshot, if_ast):
        result = self.validate_if_condition(snapshot, if_ast.get("condition"))
        if self.trace_output:
            print("result: ", result)
            if result is tuple:
                print("RESULT IS A TUPLE -> ERROR!!!!!")
        # if result.value()[0] == False:
        #     return result
        if isinstance(result, tuple): #if returns a tuple it is an ERROR
            return result

        # Execute the appropriate branch based on the condition value
        if result.value():
            # if self.trace_output:
            #     print("EVALUATE IFS")
            statements = if_ast.get("statements")
            if statements:
                return self.__run_statements(snapshot, statements)
            return self.nil_exec_result(snapshot)
        else:
            # if self.trace_output:
            #     print("EVALUATE ELSES")
            else_statements = if_ast.get("else_statements")
            if else_statements:
                return self.__run_statements(snapshot, else_statements)
            return self.nil_exec_result(snapshot)

        if self.trace_output:
            print("__do_if: SHOULD NEVER GET TO THIS STATEMENT")
        return self.nil_exec_result(snapshot)

    # def execute_ifs(self, snapshot, statements):
    #     if statements:
    #         return self.__run_statements(snapshot, statements)

    # def execute_elses(self, snapshot, else_statements):
    #     if else_statements:
    #         return self.__run_statements(snapshot, else_statements)

    def validate_if_condition(self, snapshot, cond_ast):
        result = self.__eval_expr(snapshot, cond_ast).get()

        if result[0] == False:
            if self.trace_output:
                print("EVAL NOT SUCCESSFUL ON validate_if_condition() LEVEL")
            return ExecStatus.ERROR_CODE, Lazy(lambda: result)

        condition_value = result[1]
        if condition_value.type() != Type.BOOL:
            return self.error_response_result(ErrorType.TYPE_ERROR, "Incompatible type for if condition")
        return condition_value

    def __do_for(self, snapshot, for_ast):
        init_ast = for_ast.get("init") 
        cond_ast = for_ast.get("condition")
        update_ast = for_ast.get("update") 

        self.__run_statement(snapshot, init_ast)  # initialize counter variable
        # run_for = Interpreter.TRUE_VALUE

        # while run_for.value():
        #     run_for = self.__eval_expr(snapshot, cond_ast).get()  # check for-loop condition
        #     if run_for.type() != Type.BOOL:
        #         super().error(ErrorType.TYPE_ERROR,
        #             "Incompatible type for for condition",
        #         )
        while True:
            condition = self.__eval_expr(snapshot, cond_ast).get()
            # if self.trace_output:
            #     print("condition: ", condition)
            
            if condition[0] == False:
                return ExecStatus.ERROR_CODE, Lazy(lambda: condition)

            fetched_condition = condition[1]
            
            if fetched_condition.type() != Type.BOOL:
                return self.error_response_result(ErrorType.TYPE_ERROR, "Incompatible type for for condition")

            if not fetched_condition.value(): # OUR ONLY EXIT CONDITION 
                if self.trace_output:
                    print("BROKE OUT OF LOOP")
                break

            # FOR LOOP BODY
            status, return_val = self.__run_statements(snapshot, for_ast.get("statements"))
            # if self.trace_output:
            #     print("RETURN VAL: ", return_val)
            if status == ExecStatus.RETURN or status == ExecStatus.ERROR_CODE:
                return status, return_val

            # Update iterator
            self.__run_statement(snapshot, update_ast)

        return self.nil_exec_result(snapshot)
        # return (ExecStatus.CONTINUE, Lazy(lambda: EvaledVal(True, Interpreter.NIL_VALUE)))

    def __do_return(self, snapshot, return_ast): #MUST DEEPCOPY
        expr_ast = return_ast.get("expression")
        if expr_ast is None:
            return (ExecStatus.RETURN, self.nil_exec_result(snapshot)[1])
        # value_obj = self.copy(self.__eval_expr(expr_ast))
        # return ExecStatus.RETURN, value_obj)
        return ExecStatus.RETURN, copy.deepcopy(self.__eval_expr(snapshot, expr_ast))
    
    def do_raise(self, snapshot, raise_ast):
        result_type = self.__eval_expr(snapshot, raise_ast.get("exception_type")).get()
        
        if result_type[0] == False:
            # return self.error_response_result(result_type[1], "unsuccessful evaluation")
            return (ExecStatus.ERROR_CODE, Lazy(lambda: (False, result_type[1])))

        exec_value = result_type[1]
        if exec_value.type() != Type.STRING:
            return self.error_response_result(ErrorType.TYPE_ERROR, "raise type must be string")
        else:
            return self.error_response_result(exec_value.value(), f"Unknown raise type {exec_value.value()}")

    def do_try_catch(self, snapshot, try_catch_ast):
        status, return_val = self.__run_statements(snapshot, try_catch_ast.get("statements"))
        lazy_return_val = return_val.get()
        # return_val = return_val.get()

        # print(try_catch_ast)
        if self.trace_output:
            # print("TRY STATEMENTS: ", try_catch_ast.get("statements"))
            print("CATCH STATEMENTS: ", try_catch_ast.get("catchers"), "-----------------------------------------------------------!") #SHOULD NOT BE NONE

        if status == ExecStatus.ERROR_CODE:
            # for i in range (len(try_catch_ast.get("catchers"))):
            #     curr_statement = try_catch_ast.get("catchers")[i]
            for curr_statement in try_catch_ast.get("catchers"):
                if curr_statement.get("exception_type") == lazy_return_val[1]:
                    if self.trace_output:
                        print("GOTO CATCH STATEMENT")
                    return self.__run_statements(snapshot, curr_statement.get("statements"))

        return status, return_val

FailingTestCase = """

func f(x) {
    print("running f");
    return g(5) + 3;
}

func g(x) {
    print("running g");
    return x;
}

func main() {
    f(3);
    print("end");
}

"""

shortCircuit = """

func t() {
    print("t");
    return true;
}

func f() {
    print("f");
    return false;
}

func main() {
    print(t() && f());
    print("---");
    print(f() && t());
}

"""

divby0 = """

func divide(a, b) {
    return a / b;
}

func main() {
    try {
        var result;
        result = divide(10, 0);  /* evaluation deferred due to laziness */
        print("Result: ", result); /* evaluation occurs here */
    }
    catch "div0" {
        print("Caught division by zero!");
    }
}

"""

bruh = """

func error_function() {
    raise "error";
    return 0;
}

func main() {
    var x;
    x = error_function() + 10;  // Exception occurs when x is evaluated
    print("Before x is evaluated");
    try {
        print(x);  // Evaluation of x happens here
    }
    catch "error" {
        print("Caught an error during evaluation of x");
    }
}

"""

try_catch_on_crack = """

func foo() {
    try {
        raise "z";
    }
    catch "x" {
        print("x");
    }
    catch "y" {
        print("y");
    }
    catch "z" {
        print("z");
        raise "a";
    }
    print("q");
}

func main() {
    try {
        foo();
        print("b");
    }
    catch "a" {
        print("a");
    }
}

"""

new_test_program = """

func foo() {
    print("foo");
    return true;
}

func bar() {
    print("bar");
    return false;
}

func fooRaise() {
    print("F1");
    raise "except1";
    print("F3");
}

func barTryCatch() {
    try {
        print("B1");
        foo();
        print("B2");
    }
    catch "except2" {
        print("B3");
    }

    print("B4");
}

func functionThatRaises() {
    raise "some_exception";  /* Exception occurs here when func is called */
    return 0;
}

func main() {
    print(foo() || bar() || foo() || bar());
    print("done");
    try {
        print("M1");
        bar();
        print("M2");
    }
    catch "except1" {
        print("M3");
    }
    catch "except3" {
        print("M4");
    }
    print("M5");

    print("TESTING LAZY EVALUATION NOW=====================================================================");
    print("x");
    foo();
    inputi("Enter a number");

    result = functionThatRaises();
    print("Assigned result!");

    raise "foo";
    x = "foo"+"bar";
    raise x;
    raise "foo" + "bar";
}

"""

old_test_program = """

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

func fooOnMeth(x) {
    var it;
    for (it = 0; it < x; it = it + 1) {
        if (it == 5) {
            print("IT HAS REACHED 5");
            return;
        }
        print("it value: ", it);
    }
}

func fooShadow(c) { 
    if (c == 10) {
        var c;     /* variable of the same name as parameter c */
        c = "hi";
        print(c);  /* prints "hi"; the inner c shadows the parameter c*/
    }
    print(c); /* prints 10 */
}

func fact(n) {
    if (n <= 1) { return 1; }
    return n * fact(n-1);
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
    if (foo() == val && bar() == nil) { print("this should print!"); }

    var i;
    for (i=0; i+3 < 10; i=i+1) {
        print(i);
    }

    print("the positive value is ", fooOnCrack(-10));
    fooOnMeth(10);

    var c;
    c = 10;
    if (c == 10) {
        var c;     /* variable of the same name as outer variable */
        c = "hi";
        print(c);  /* prints "hi"; the inner c shadows the outer c*/
    }
    print(c); /* prints 10 */

    print("FOO SHADOW TIME:");
    fooShadow(10);

    print("TESTING FOR ONE LAST TIME:");
    var iter;
    for (iter = 3; iter > 0; iter = iter - 1) {
        print(iter);
    }
    
    print(fact(5));
}
"""

new_interpreter = Interpreter(console_output = True, inp = None, trace_output = True)
# new_interpreter.run(old_test_program)
# new_interpreter.run(new_test_program)
# new_interpreter.run(try_catch_on_crack)
# new_interpreter.run(bruh)
# new_interpreter.run(FailingTestCase)
# new_interpreter.run(divby0)