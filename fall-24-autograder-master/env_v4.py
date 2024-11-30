import copy

# The EnvironmentManager class keeps a mapping between each variable name (aka symbol)
# in a brewin program and the Value object, which stores a type, and a value.
trace_output = False

class EnvironmentManager:
    def __init__(self):
        self.environment = []

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
        cur_func_env.pop() 

    # used when we exit a nested block to discard the environment for that block
    def pop_func(self):
        self.environment.pop()

    # def deep_copy_environment(self):
    #     return copy.deepcopy(self.environment)
    
    # def deep_copy_environment(self): #we can't just deepcopy unfort
    #     copied_env = EnvironmentManager()
        
    #     for func_scope in self.environment:
    #         copied_env.push_func()
    #         for block_scope in copied_env:
    #             if trace_output:
    #                 print("COPIED ENV WTF IS HAPPENIG: ", copied_env)

    #         return copied_env

    def deep_copy_environment(self): #we can't just deepcopy unfort
        copied_env = EnvironmentManager()

        for func_scope in self.environment:
            self.copy_func_scope(func_scope, copied_env)
        if trace_output:
            print("FINAL COPIED ENVIORMNET: ", copied_env)

        return copied_env

    def copy_func_scope(self, func_scope, copied_env):
        copied_env.push_func()

        for block_scope in func_scope:
            self.copy_block_scope(block_scope, copied_env)

    def copy_block_scope(self, block_scope, copied_env):
        if trace_output:
            print("block_scope: ", block_scope)

        copied_env.push_block()
        self.create_bulk_pairs(block_scope, copied_env)
        # self.create_bulk_entries(block_scope, copied_env)

    # def create_bulk_entries(self, key_value_pairs, copied_env):
    #     copied_env.create_bulk_pairs(key_value_pairs)

    def create_bulk_pairs(self, key_value_pairs, copied_env): #Travels upwards, create pairs for each block and function
        if trace_output:
            print("keyValPairs: ", key_value_pairs)

        for key, value in key_value_pairs.items():
            copied_env.create(key, value)
