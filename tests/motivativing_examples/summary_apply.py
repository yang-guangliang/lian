import re
from default_checkers import *

class Validation:
    def __init__(self):
        self.validation = {}

    def init(self):
        self.validation["a"] = 1
        cond = True
        if cond:
            self.validation["c"] = {
                "d": {
                    "k": 5
                },
                "e": 3
            }
        else:
            self.validation["c"] = {
                "d": {
                    "g": 6
                },
                "h": 7
            }
        # global checkers
        # for key in checkers:
        #     self.validation[key] = checkers[key]

    def config(self, key, value):
        self.validation["b"] = 2
        self.validation["c"] = {
            "d": {
                "k": 9,
                "l": 8
            },
            "f": 4
        }
        # self.validation[key] = value

    def validate(self, content):
        array = content.split('&')
        for kv in array:
            for key in self.validation:
                result = self.validation[key](kv)
                if not result:
                    return False
        return True

def content_evaluation(user_input):
    matched = re.search(r"content=(.+)", user_input)
    if matched:
        eval(matched.group(1))
    return True

if __name__ == "__main__":
    validator = Validation()
    validator.init()
    validator.config("content_evaluation", content_evaluation)
    validator.validate("name=john&content=print(1)")
