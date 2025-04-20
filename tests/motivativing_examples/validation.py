checkers = {
   "input_format": lambda x: "=" in x[1:-1],
}

class Validation:
    def __init__(self):
        self.validation = {}

    def init(self):
        self.config(checkers)

    def config(self, map):
        for name in map: # 第三阶段map应该要resolve到
            self.validation[name] = map[name]

    def validate(self, content):
        for name in self.validation:
            self.validation[name](content)

def wrapper():
    def content_evaluation(user_input):
        if user_input:
            eval(user_input)
    return content_evaluation

if __name__ == "__main__":
    validator = Validation()
    validator.init()
    validator.config({"content_evaluation": wrapper()})
    validator.validate("print(1)")