from type_valuev2 import * 

# The EnvironmentManager class keeps a mapping between each variable name (aka symbol)
# in a brewin program and the Value object, which stores a type, and a value.
class EnvironmentManager:
    def __init__(self):
        self.environment = []
        # self.reset_structs()

    # returns a VariableDef object
    def get(self, symbol):
        cur_func_env = self.environment[-1]
        for env in reversed(cur_func_env):
            if symbol in env:
                return env[symbol]

        return None

    def set(self, symbol, value):
        cur_func_env = self.environment[-1]
        for env in reversed(cur_func_env):
            if symbol in env:
                env[symbol] = value
                return True

        return False

    def reset_structs(self):
        Type.reset_struct_types()

    # def reset(self):
    #     self.environment = []  # Clear the environment stack
    #     self.push_func()

    def is_in_function(self):
        return len(self.environment) > 0

    def cleanup_structs(self, block_env):
        for symbol, value in list(block_env.items()):  # Use list to avoid runtime changes
            if value in Type.struct_types:  # Check if the value is a struct
                # Perform any cleanup logic specific to struct instances
                block_env.pop(symbol)  # Remove struct instance from environment

    # create a new symbol in the top-most environment, regardless of whether that symbol exists
    # in a lower environment
    def create(self, symbol, value):
        cur_func_env = self.environment[-1]
        if symbol in cur_func_env[-1]:   # symbol already defined in current scope
            return False
        cur_func_env[-1][symbol] = value
        return True

    # used when we enter a new function - start with empty dictionary to hold parameters.
    def push_func(self):
        self.environment.append([{}])  # [[...]] -> [[...], [{}]]

    def push_block(self):
        cur_func_env = self.environment[-1]
        cur_func_env.append({})  # [[...],[{....}] -> [[...],[{...}, {}]]

    def pop_block(self):
        cur_func_env = self.environment[-1]
        self.cleanup_structs(cur_func_env[-1])  # Clean up structs in this block
        cur_func_env.pop() 

    # used when we exit a nested block to discard the environment for that block
    def pop_func(self):
        cur_func_env = self.environment[-1]
        for block in cur_func_env:
            self.cleanup_structs(block)  # Clean up structs in each block
        self.environment.pop()

