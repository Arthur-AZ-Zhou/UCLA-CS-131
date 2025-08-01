from intbase import InterpreterBase

# Enumerated type for our different language data types
class Type:
    INT = "int"
    BOOL = "bool"
    STRING = "string"
    NIL = "nil"
    VOID = "void"
    struct_types = {} 

    def add_struct_type(self, struct_type): #IMPORTANT FOR NON PRIMITIVES
        Type.struct_types[struct_type] = None

    def add_struct(self, struct_type, struct):
        Type.struct_types[struct_type] = struct

    def get_struct(self, struct_type):
        return Type.struct_types[struct_type]

    @staticmethod
    def reset_struct_types():
        """Reset all struct type definitions."""
        Type.struct_types.clear()

# Represents a value, which has a type and its value
class Value:
    def __init__(self, type, value=None):
        self.t = type
        self.v = value

    def type(self):
        return self.t

    def value(self):
        return self.v

    def cleanup(self):
        if self.type() in Type.struct_types:
            self.v = None  # Reset the value for cleanup

def create_value(val):
    if val == InterpreterBase.TRUE_DEF:
        return Value(Type.BOOL, True)
    elif val == InterpreterBase.FALSE_DEF:
        return Value(Type.BOOL, False)
    elif val == InterpreterBase.NIL_DEF:
        return Value(Type.NIL, None)
    elif isinstance(val, str):
        return Value(Type.STRING, val)
    elif isinstance(val, int):
        return Value(Type.INT, val)
    else:
        raise ValueError("Unknown value type")

def get_printable(val):
    if val.type() == Type.INT:
        return str(val.value())
    if val.type() == Type.STRING:
        return val.value()
    if val.type() == Type.BOOL:
        if val.value() is True:
            return "true"
        return "false"
    if val.type() in Type().struct_types:
        return f"{val.value()}"
    # if val.type() == Type.NIL:
    #     return "nil"
    return Type.NIL #undefined behavior
