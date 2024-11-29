class Lazy:
    def __init__(self, equation_func):
        self.equation_func = equation_func
        self.actual_val = None
        self.solved = False

    def get(self):
        if not self.solved:
            self.actual_val = self.equation_func()
            self.solved = True
        return self.actual_val