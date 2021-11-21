from lark import Lark, UnexpectedCharacters, Tree


class Parser:
    def __init__(self):
        self.command_level_parser = Lark(
            self._get_command_level_grammar(), start="command"
        )
        self.call_command_parser = Lark(self._get_call_command_grammar(), start="call")

    def _get_command_level_grammar(self):
        file = open("command_level_grammar.lark", "r")
        grammar = file.read()
        file.close()
        return grammar

    def _get_call_command_grammar(self):
        file = open("call_command_grammar.lark", "r")
        grammar = file.read()
        file.close()
        return grammar

    def command_level_parse(self, input):
        try:
            return self.command_level_parser.parse(input)
        except UnexpectedCharacters:
            return False

    def call_level_parse(self, input):
        try:
            return self.call_command_parser.parse(input)
        except UnexpectedCharacters:
            return False