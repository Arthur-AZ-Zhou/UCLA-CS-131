trace_output = False;

# class ResultEvaluator:
#     def __init__(self, success, parameters):
#         self.parameters = parameters
#         self.success = success

class EvaluatedResult:
    def __init__(self, successful_eval, args):
        self.args = args
        self.successful_eval = successful_eval

#     def fetch(self):
#         if not self.success:
#             if trace_output:
#                 print("FETCHING VALUE EVEN WHEN UNSUCCESSFUL")
#             return self.parameters
#         else:
#             return None

    def get(self):
        if self.successful_eval:
            if trace_output:
                print("EVAL IS SUCCESSFUL AT VALUE LEVEL")
            return self.args
        else:
            return None

    def return_error(self):
        if not self.successful_eval: # IF EVAL NOT SUCCESSFUL WE RETURN THE ERROR
            # print("EVAL SUCCKSESS ")
            return self.args
        else:
            return None

    def return_error_type(self):
        # if self.successful_eval: #if successful proceed
        #     return self.args[0]
        # else:
        #     return self.args
        if not self.successful_eval: #IF EVAL NOT SUCCESSFUL WE RETURN THE ERROR TYPE
            return self.args[0]
        else:
            return None
        