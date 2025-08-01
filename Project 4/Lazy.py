import copy
from enum import Enum

class Lazy:
    def __init__(self, equation_func):
        self.equation_func = equation_func
        self.actual_val = None
        self.solved = False

    def get(self):
        if self.solved == False:
            self.actual_val = self.equation_func()
            self.solved = True
        return self.actual_val
    
    def copy(self):
        return Lazy(self.equation_func)