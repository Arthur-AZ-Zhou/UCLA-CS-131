# document that we won't have a return inside the init/update of a for loop

import copy
from enum import Enum

from brewparse import parse_program
from env_v4 import EnvironmentManager
from intbase import InterpreterBase, ErrorType
from type_valuev4 import Type, Value, create_value, get_printable
from Lazy import Lazy
from EvaluatedResult import EvaluatedResult


class ExecStatus(Enum):
    CONTINUE = 1
    RETURN = 2
    ERROR = 3

#WARNING EVERYTHING NOW REQUIRES YOU TO PUT A ENV BLOCK
class Interpreter(InterpreterBase):
    # constants
    NIL_VALUE = create_value(InterpreterBase.NIL_DEF)
    TRUE_VALUE = create_value(InterpreterBase.TRUE_DEF)
    BIN_OPS = {"+", "-", "*", "/", "==", "!=", ">", ">=", "<", "<=", "||", "&&"}

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
        self.env = EnvironmentManager()
        result = self.__call_func_aux("main", [], self.env).get() 

        if not result.successful_eval: #PRINT IF SUCCESSFUL FOR DEBUG
            if type(result.return_error_type()) == str:
                super().error(ErrorType.FAULT_ERROR, f"{result.return_error()}")
            else:
                super().error(*result.return_error())

    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}
        for func_def in ast.get("functions"):
            func_name = func_def.get("name")
            num_params = len(func_def.get("args"))
            if func_name not in self.func_name_to_ast:
                self.func_name_to_ast[func_name] = {}
            self.func_name_to_ast[func_name][num_params] = func_def

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

    def __run_statements(self, statements, env):
        env.push_block()
        for statement in statements:
            if self.trace_output:
                print(statement)
                print(env)
                print()
            status, return_val = self.__run_statement(statement, env)
            if status in (ExecStatus.RETURN, ExecStatus.ERROR):
                env.pop_block()
                return (status, return_val)

        env.pop_block()
        return (ExecStatus.CONTINUE, Lazy(lambda: EvaluatedResult(True, Interpreter.NIL_VALUE)))

    def __run_statement(self, statement, env):
        status = ExecStatus.CONTINUE
        return_val = Lazy(lambda: EvaluatedResult(True, Interpreter.NIL_VALUE))
        if statement.elem_type == InterpreterBase.FCALL_NODE:
            exec_result = self.__call_func(statement, env).get()
            if not exec_result.successful_eval:
                status, return_val = ExecStatus.ERROR, Lazy(lambda: exec_result)
        elif statement.elem_type == "=":
            self.__assign(statement, env)
        elif statement.elem_type == InterpreterBase.VAR_DEF_NODE:
            self.__var_def(statement, env)
        elif statement.elem_type == InterpreterBase.RETURN_NODE:
            status, return_val = self.__do_return(statement, env)
        elif statement.elem_type == Interpreter.IF_NODE:
            status, return_val = self.__do_if(statement, env)
        elif statement.elem_type == Interpreter.FOR_NODE:
            status, return_val = self.__do_for(statement, env)
        elif statement.elem_type == Interpreter.TRY_NODE:
            status, return_val = self.__do_try(statement, env)
        elif statement.elem_type == Interpreter.RAISE_NODE:
            status, return_val = self.__do_raise(statement, env)
        else:
            print('Unrecognized statement.elem_type {statement.elem_type}')
            exit(-1)

        return (status, return_val)
    
    def __call_func(self, call_node, env):
        func_name = call_node.get("name")
        actual_args = call_node.get("args")
        return self.__call_func_aux(func_name, actual_args, env)

    def __call_func_aux(self, func_name, actual_args, env):
        if func_name == "print":
            return self.__call_print(actual_args, env)
        if func_name == "inputi" or func_name == "inputs":
            return self.__call_input(func_name, actual_args, env)

        # env_snapshot = copy.deep_copy_environment(env)
        snapshot = env.deep_copy_environment()
        def f():
            func_ast = self.__get_func_by_name(func_name, len(actual_args))
            formal_args = func_ast.get("args")
            if len(actual_args) != len(formal_args):
                return EvaluatedResult(False, (ErrorType.NAME_ERROR, f"Function {func_ast.get('name')} with {len(actual_args)} args not found"))

            # first evaluate all of the actual parameters and associate them with the formal parameter names
            args = {}
            for formal_ast, actual_ast in zip(formal_args, actual_args):
                result = self.__eval_expr(actual_ast, snapshot)
                arg_name = formal_ast.get("name")
                args[arg_name] = result

            # then create the new activation record 
            snapshot.push_func()
            # and add the formal arguments to the activation record
            for arg_name, value in args.items():
                snapshot.create(arg_name, value)
            _, return_val = self.__run_statements(func_ast.get("statements"), snapshot)
            snapshot.pop_func()
            return return_val.get()

        return Lazy(f)

    def __call_print(self, args, env):
        def f():
            output = ""
            for arg in args:
                result = self.__eval_expr(arg, env).get()
                if not result.successful_eval:
                    return result
                output = output + get_printable(result.get())
            super(Interpreter, self).output(output)
            return EvaluatedResult(True, Interpreter.NIL_VALUE)
        return Lazy(f)

    def __call_input(self, name, args, env):
        def f():
            if args is not None and len(args) == 1:
                result = self.__eval_expr(args[0], env).get()
                if not result.successful_eval:
                    return result
                super(Interpreter, self).output(get_printable(result.get()))
            elif args is not None and len(args) > 1:
                return EvaluatedResult(False, (ErrorType.NAME_ERROR, "No inputi() function that takes > 1 parameter"))
            inp = super(Interpreter, self).get_input()
            if name == "inputi":
                return EvaluatedResult(True, Value(Type.INT, int(inp)))
            if name == "inputs":
                return EvaluatedResult(True, Value(Type.STRING, inp))
        return Lazy(f)

    def __assign(self, assign_ast, env):
        var_name = assign_ast.get("name")
        value_obj = self.__eval_expr(assign_ast.get("expression"), env)
        
        if not env.set(var_name, value_obj):
            super().error(
                ErrorType.NAME_ERROR, f"Undefined variable {var_name} in assignment"
            )
    
    def __var_def(self, var_ast, env):
        var_name = var_ast.get("name")
        if not env.create(var_name, Lazy(lambda: EvaluatedResult(True, Interpreter.NIL_VALUE))):
            super().error(
                ErrorType.NAME_ERROR, f"Duplicate definition for variable {var_name}"
            )

    def __eval_expr(self, expr_ast, env):
        if expr_ast.elem_type == InterpreterBase.NIL_NODE:
            return Lazy(lambda: EvaluatedResult(True, Interpreter.NIL_VALUE))
        if expr_ast.elem_type == InterpreterBase.INT_NODE:
            return Lazy(lambda: EvaluatedResult(True, Value(Type.INT, expr_ast.get("val"))))
        if expr_ast.elem_type == InterpreterBase.STRING_NODE:
            return Lazy(lambda: EvaluatedResult(True, Value(Type.STRING, expr_ast.get("val"))))
        if expr_ast.elem_type == InterpreterBase.BOOL_NODE:
            return Lazy(lambda: EvaluatedResult(True, Value(Type.BOOL, expr_ast.get("val"))))
        
        snapshot = env.deep_copy_environment()
        if self.trace_output:
            print("SNAPSHOT: ")
        # snapshot = copy.deep_copy_environment(env)
        if expr_ast.elem_type == InterpreterBase.VAR_NODE:
            var_name = expr_ast.get("name")
            def f():
                val = snapshot.get(var_name)
                if val is None:
                    return EvaluatedResult(False, (ErrorType.NAME_ERROR, f"Variable {var_name} not found"))
                return val.get()
            return Lazy(f)
        if expr_ast.elem_type == InterpreterBase.FCALL_NODE:
            return self.__call_func(expr_ast, snapshot)
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            return self.__eval_op(expr_ast, snapshot)
        if expr_ast.elem_type == Interpreter.NEG_NODE:
            return self.__eval_unary(expr_ast, Type.INT, lambda x: -1 * x, snapshot)
        if expr_ast.elem_type == Interpreter.NOT_NODE:
            return self.__eval_unary(expr_ast, Type.BOOL, lambda x: not x, snapshot)

    def __eval_op(self, arith_ast, env):
        def f():
            left_value_obj = self.__eval_expr(arith_ast.get("op1"), env).get()
            if left_value_obj.successful_eval:
                left_value_obj = left_value_obj.get()
            else:
                return left_value_obj
            
            # Short circuit
            if left_value_obj == Value(Type.BOOL, True) and arith_ast.elem_type == '||':
                return EvaluatedResult(True, Value(Type.BOOL, True))
            if left_value_obj == Value(Type.BOOL, False) and arith_ast.elem_type == '&&':
                return EvaluatedResult(True, Value(Type.BOOL, False))

            right_value_obj = self.__eval_expr(arith_ast.get("op2"), env).get()
            if right_value_obj.successful_eval:
                right_value_obj = right_value_obj.get()
            else:
                return right_value_obj

            # Division by 0
            if right_value_obj == Value(Type.INT, 0) and arith_ast.elem_type == '/':
                return EvaluatedResult(False, ("div0", f"Division by 0: {left_value_obj} {arith_ast.elem_type} {right_value_obj}"))
            
            if not self.__compatible_types(
                arith_ast.elem_type, left_value_obj, right_value_obj
            ):
                return EvaluatedResult(False, (
                    ErrorType.TYPE_ERROR,
                    f"Incompatible types for {arith_ast.elem_type} operation",
                ))
            if arith_ast.elem_type not in self.op_to_lambda[left_value_obj.type()]:
                return EvaluatedResult(False, (
                    ErrorType.TYPE_ERROR,
                    f"Incompatible operator {arith_ast.elem_type} for type {left_value_obj.type()}",
                ))
            f = self.op_to_lambda[left_value_obj.type()][arith_ast.elem_type]
            return EvaluatedResult(True, f(left_value_obj, right_value_obj))
        return Lazy(f)

    def __compatible_types(self, oper, obj1, obj2):
        # DOCUMENT: allow comparisons ==/!= of anything against anything
        if oper in ["==", "!="]:
            return True
        return obj1.type() == obj2.type()

    def __eval_unary(self, arith_ast, t, unary_func, env):
        def f():
            value_obj = self.__eval_expr(arith_ast.get("op1"), env).get()
            if value_obj.successful_eval:
                value_obj = value_obj.get()
            else:
                return value_obj
            
            if value_obj.type() != t:
                return EvaluatedResult(False, (
                    ErrorType.TYPE_ERROR,
                    f"Incompatible type for {arith_ast.elem_type} operation",
                ))
            return EvaluatedResult(True, Value(t, unary_func(value_obj.value())))
        return Lazy(f)

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

    def __do_if(self, if_ast, env):
        cond_ast = if_ast.get("condition")
        result = self.__eval_expr(cond_ast, env).get()
        if result.successful_eval:
            result = result.get()
        else:
            return (ExecStatus.ERROR, Lazy(lambda: result))
        if result.type() != Type.BOOL:
            return (ExecStatus.ERROR, Lazy(lambda: EvaluatedResult(False, (
                ErrorType.TYPE_ERROR,
                "Incompatible type for if condition",
            ))))
        if result.value():
            statements = if_ast.get("statements")
            status, return_val = self.__run_statements(statements, env)
            return (status, return_val)
        else:
            else_statements = if_ast.get("else_statements")
            if else_statements is not None:
                status, return_val = self.__run_statements(else_statements, env)
                return (status, return_val)

        return (ExecStatus.CONTINUE, Lazy(lambda: EvaluatedResult(True, Interpreter.NIL_VALUE)))

    def __do_for(self, for_ast, env):
        init_ast = for_ast.get("init") 
        cond_ast = for_ast.get("condition")
        update_ast = for_ast.get("update") 

        self.__run_statement(init_ast, env)  # initialize counter variable
        run_for = Interpreter.TRUE_VALUE
        while run_for.value():
            run_for = self.__eval_expr(cond_ast, env).get()
            if run_for.successful_eval:
                run_for = run_for.get()
            else:
                return (ExecStatus.ERROR, Lazy(lambda: run_for))
            
            if run_for.type() != Type.BOOL:
                return (ExecStatus.ERROR, Lazy(lambda: EvaluatedResult(False, (
                    ErrorType.TYPE_ERROR,
                    "Incompatible type for for condition",
                ))))
            
            if run_for.value():
                statements = for_ast.get("statements")
                status, return_val = self.__run_statements(statements, env)
                if status in (ExecStatus.RETURN, ExecStatus.ERROR):
                    return status, return_val
                self.__run_statement(update_ast, env)

        return (ExecStatus.CONTINUE, Lazy(lambda: EvaluatedResult(True, Interpreter.NIL_VALUE)))

    def __do_return(self, return_ast, env):
        expr_ast = return_ast.get("expression")
        if expr_ast is None:
            return (ExecStatus.RETURN, Lazy(lambda: EvaluatedResult(True, Interpreter.NIL_VALUE)))
        value_obj = copy.copy(self.__eval_expr(expr_ast, env))
        return (ExecStatus.RETURN, value_obj)
    
    def __do_try(self, try_ast, env):
        statements, catchers = try_ast.dict['statements'], try_ast.dict['catchers']
        status, exec_result_lazy = self.__run_statements(statements, env)
        if status == ExecStatus.ERROR:
            exec_result = exec_result_lazy.get()
            exec_error = exec_result.return_error_type()
            for catcher in catchers:
                exception_type = catcher.dict['exception_type']
                if exception_type == exec_error:
                    catch_status, catch_exec_result = self.__do_catch(catcher, env)
                    return (catch_status, catch_exec_result)
        return (status, exec_result_lazy)

    def __do_catch(self, catch_ast, env):
        catcher_statements = catch_ast.dict['statements']
        return self.__run_statements(catcher_statements, env)
    
    def __do_raise(self, raise_ast, env):
        exception_type = raise_ast.dict['exception_type']
        exception_type = self.__eval_expr(exception_type, env)
        exec_result = exception_type.get()
        if exec_result.successful_eval:
            exec_value = exec_result.get()
            if exec_value.type() != Type.STRING:
                return (ExecStatus.ERROR, Lazy(lambda: EvaluatedResult(False, (ErrorType.TYPE_ERROR, "Must raise a string"))))
            return (ExecStatus.ERROR, Lazy(lambda: EvaluatedResult(False, (exec_value.value(), f"Custom Raise {exec_value.value()}"))))
        else:
            return (ExecStatus.ERROR, Lazy(lambda: EvaluatedResult(False, exec_result.return_error())))

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

# new_interpreter = Interpreter(console_output = True, inp = None, trace_output = True)
# new_interpreter.run(test_program)