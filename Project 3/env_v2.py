from type_valuev2 import *

# The EnvironmentManager class keeps a mapping between each variable name (aka symbol)
# in a brewin program and the Value object, which stores a type, and a value.
class EnvironmentManager:
    def __init__(self):
        self.trace_output = False #FEEL FREE TO CHANGE
        self.environment = [{"isFunctionCall" : True}]  # stack of dictionairies

    def push_block(self):
        self.environment.append({"isFunctionCall" : False})

    def pop_block(self):
        self.environment.pop()

    def push_func(self):
        self.environment.append([{}])

    def pop_func(self):
        cur_func_env = self.environment[-1]
        self.environment.pop()

    # create a new symbol in the top-most environment, regardless of whether that symbol exists
    # in a lower environment
    def create(self, symbol, value):
        cur_func_env = self.environment[-1]
        if symbol in cur_func_env:    # symbol already defined in current scope
            return False
        cur_func_env[symbol] = value
        return True

    # Gets the data associated with the var name at the most recent scope within cur func call
    def get(self, symbol):
        cur_func_env = self.environment  

        for env in reversed(cur_func_env): 
            if symbol in env:
                return env[symbol]  
            elif env["isFunctionCall"]: 
                return None  

    def set(self, all_symbols, value): # have to search thru nested structs
        found_symbol, env, symbols, last_symbol = self.find_symbol(all_symbols) #throw it all into a helper

        if self.trace_output:
            print("FOUND_SYMBOL: ", found_symbol)
            print("ENV: ", env)
            print("SYMBOLS: ", symbols)
            print("LAST_SYMBOL: ", last_symbol)

        if self.trace_output:
            print(f"Setting value for: {all_symbols}")
        if found_symbol is None:
            return False 
        if not isinstance(found_symbol.value(), dict) or len(symbols) == 1:
            env[symbols[0]] = value
            return True

        for key in symbols[1:-1]:
            found_symbol = found_symbol.value().get(key)
            if found_symbol is None:
                return False  # Key not found

        # Assign to the final nested symbol
        if last_symbol:
            found_symbol.value()[last_symbol] = value
            return True

        return False

    def find_symbol(self, all_symbols): #helper for set()
        symbols = all_symbols.split(".")
        cur_symbol = symbols[0]
        cur_func_env = self.environment

        if len(symbols) > 1:
            if self.trace_output:       
                print("LAST SYMBOL IS NOT NONE")
            last_symbol = symbols[-1]
        else:
            last_symbol = None

        for env in reversed(cur_func_env):
            if cur_symbol in env:
                found_symbol = env[cur_symbol]

                # Return all
                return found_symbol, env, symbols, last_symbol

            if env["isFunctionCall"]:
                break

        return None, None, None, None  # Symbol not found

    def is_in_function(self, index):
        return self.environment[index]["isFunctionCall"]

    def reset_structs(self):
        Type.reset_struct_types()

    def cleanup_structs(self, block_env):
        for symbol, value in list(block_env.items()):  # Use list to avoid runtime changes
            if value in Type.struct_types:  # Check if the value is a struct
                # Perform any cleanup logic specific to struct instances
                block_env.pop(symbol)  # Remove struct instance from environment

    def reset(self):
        self.environment = []  # Clear the environment stack
        self.push_func()