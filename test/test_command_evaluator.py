import unittest
from parser import Parser
from command_evaluator import extract_raw_commands
from commands import Call, Pipe


class TestCommandEvaluator(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()

    def _get_raw_commands(self, cmd):
        command_tree = self.parser.command_level_parse(cmd)
        raw_commands = extract_raw_commands(command_tree)
        return raw_commands

    def test_pipe(self):
        raw_commands = self._get_raw_commands("echo foo | echo")

        self.assertEqual(len(raw_commands), 1)
        self.assertEqual(type(raw_commands[0]), Pipe)
        self.assertEqual(type(raw_commands[0].lhs()), Call)
        self.assertEqual(type(raw_commands[0].rhs()), Call)
        self.assertEqual(raw_commands[0].lhs().raw_command.strip(), "echo foo")
        self.assertEqual(raw_commands[0].rhs().raw_command.strip(), "echo")

    def test_extract_quoted_content_with_content_between_quotes(self):
        raw_commands = self._get_raw_commands("'foo'")

        self.assertEqual(len(raw_commands), 1)
        self.assertEqual(type(raw_commands[0]), Call)
        self.assertEqual(raw_commands[0].raw_command, "'foo'")

    def test_extract_quoted_content_with_no_content_between_quotes(self):
        raw_commands = self._get_raw_commands("''")

        self.assertEqual(len(raw_commands), 1)
        self.assertEqual(type(raw_commands[0]), Call)
        self.assertEqual(raw_commands[0].raw_command, "''")

    def test_double_quotes(self):
        raw_commands = self._get_raw_commands('"bar"')

        self.assertEqual(len(raw_commands), 1)
        self.assertEqual(type(raw_commands[0]), Call)
        self.assertEqual(raw_commands[0].raw_command, '"bar"')

    def test_double_quotes_with_nested_backquotes(self):
        raw_commands = self._get_raw_commands('"bar`foo`"')

        self.assertEqual(len(raw_commands), 1)
        self.assertEqual(type(raw_commands[0]), Call)
        self.assertEqual(raw_commands[0].raw_command, '"bar`foo`"')

    def test_quoted_with_single_quotes(self):
        raw_commands = self._get_raw_commands("'bar'")

        self.assertEqual(len(raw_commands), 1)
        self.assertEqual(type(raw_commands[0]), Call)
        self.assertEqual(raw_commands[0].raw_command, "'bar'")

    def test_quoted_with_backquotes(self):
        raw_commands = self._get_raw_commands("`echo foo`")

        self.assertEqual(len(raw_commands), 1)
        self.assertEqual(type(raw_commands[0]), Call)
        self.assertEqual(raw_commands[0].raw_command, "`echo foo`")

    def test_call_with_no_quotes(self):
        raw_commands = self._get_raw_commands("echo bar")

        self.assertEqual(len(raw_commands), 1)
        self.assertEqual(type(raw_commands[0]), Call)
        self.assertEqual(raw_commands[0].raw_command, "echo bar")


if __name__ == "__main__":
    unittest.main()
