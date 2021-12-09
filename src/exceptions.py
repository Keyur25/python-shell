class ApplicationExcecutionError(Exception):

    """raised when an application cannot be executed"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class InvalidCommandSubstitution(Exception):

    """raised when there is an invalid command substitution"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
