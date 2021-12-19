from pathlib import Path
from lark import Lark, UnexpectedCharacters, UnexpectedEOF


class Parser:
    def __init__(self):
        self.command_level_parser = Lark(self._command_level_grammar(), start="command")
        self.call_command_parser = Lark(self._call_level_grammar(), start="call")

    def _command_level_grammar(self):
        file = open(
            str(Path(__file__).parent.absolute())
            + "/grammars/command_level_grammar.lark",
            "r",
        )
        grammar = file.read()
        file.close()
        return grammar

    def _call_level_grammar(self):
        file = open(
            str(Path(__file__).parent.absolute()) + "/grammars/call_level_grammar.lark",
            "r",
        )
        grammar = file.read()
        file.close()
        return grammar

    def command_level_parse(self, cmd):
        try:
            return self.command_level_parser.parse(cmd)
        except (UnexpectedCharacters, UnexpectedEOF):
            return False

    def call_level_parse(self, call):
        try:
            return self.call_command_parser.parse(call)
        except (UnexpectedCharacters, UnexpectedEOF):
            return False
