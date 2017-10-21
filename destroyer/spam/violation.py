class Violation(Exception):
    def __init__(self, rule, message):
        self.rule = rule
        self.message = message

        self.author = self.message.author