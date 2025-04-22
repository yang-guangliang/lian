checkers = {
    "input_format": lambda x: "=" in x[1:-1],
    # ...
}

class Validation:
    def __init__(self):
        self.validation = {}

    def init(self):
        for key in checkers:
            self.validation[key] = checkers[key]

    def config(self, key, value):
        self.validation[key] = value

    def validate(self, content):
        for key in self.validation:
            self.validation[key](content)

def content_evaluation(user_input):
    if user_input:
        eval(user_input)

if __name__ == "__main__":
    validator = Validation()
    validator.init()
    validator.config("content_evaluation", content_evaluation)
    validator.validate("print(1)")

