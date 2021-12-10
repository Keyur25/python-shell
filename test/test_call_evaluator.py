import unittest
from collections import deque
import subprocess
from parser import Parser
from call_evaluator import (
    CommandSubstituitionVisitor,
    CallTreeVisitor,
    InvalidCommandSubstitution,
)


class TestCallEvaluator(unittest.TestCase):
    @classmethod
    def prepare(cls, cmdline):
        args = [
            "/bin/bash",
            "-c",
            cmdline,
        ]
        p = subprocess.run(args, capture_output=True)
        return p.stdout.decode()

    def setUp(self):
        p = subprocess.run(["mkdir", "unittests"], stdout=subprocess.DEVNULL)
        if p.returncode != 0:
            print("error: failed to create unittest directory")
            exit(1)
        filesystem_setup = ";".join(
            [
                "cd unittests",
                "echo AAA > test1.txt",
                "echo BBB > test2.txt",
                "echo CCC > test3.txt",
            ]
        )
        self.prepare(filesystem_setup)
        self.parser = Parser()
        self.out = deque()

    def tearDown(self):
        p = subprocess.run(
            ["rm", "-r", "unittests"], stdout=subprocess.DEVNULL
            )
        if p.returncode != 0:
            print("error: failed to remove unittests directory")
            exit(1)

    def _call_tree_visitor(self, cmd):
        call_tree = self.parser.call_level_parse(cmd)

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        return (
            call_tree_visitor.application,
            call_tree_visitor.args,
            call_tree_visitor.file_output,
        )

    def test_command_substitution_visitor(self):
        call_tree = self.parser.call_level_parse("echo `echo foo`")

        command_substituition_visitor = CommandSubstituitionVisitor(self.out)
        command_substituition_visitor.visit(call_tree)

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(len(self.out), 0)
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "foo")
        self.assertEqual(call_tree_visitor.file_output, None)

    def test_command_substitution_visitor_with_invalid_command(self):
        call_tree = self.parser.call_level_parse("echo `'''`")

        command_substituition_visitor = CommandSubstituitionVisitor(self.out)

        self.assertRaises(
            InvalidCommandSubstitution,
            command_substituition_visitor.visit,
            call_tree
        )

    def test_redirection_visitor_input(self):
        application, args, file_output = self._call_tree_visitor(
            "echo < file.txt"
            )

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "file.txt")
        self.assertEqual(file_output, None)

    def test_redirection_visitor_output(self):
        application, args, file_output = self._call_tree_visitor(
            "echo foo > file.txt"
            )

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "foo")
        self.assertEqual(file_output, "file.txt")

    def test_redirection_visitor_with_single_quoted_file_name(self):
        application, args, file_output = self._call_tree_visitor(
            "echo < 'file.txt'"
            )

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "file.txt")
        self.assertEqual(file_output, None)

    def test_redirection_visitor_with_double_quoted_file_name(self):
        application, args, file_output = self._call_tree_visitor(
            'echo < "file.txt"'
            )

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "file.txt")
        self.assertEqual(file_output, None)

    def test_redirection_visitor_with_back_quoted_file_name(self):
        application, args, file_output = self._call_tree_visitor(
            "echo < `echo file.txt`"
        )

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "echo file.txt")
        self.assertEqual(file_output, None)

    def test_redirection_visitor_with_nested_back_quoted_file_name_in_double_quotes(
        self,
    ):
        application, args, file_output = self._call_tree_visitor(
            'echo < "`echo file.txt`"'
        )

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "echo file.txt")
        self.assertEqual(file_output, None)

    def test_redirection_visitor_with_empty_quoted_file_name(self):
        application, args, file_output = self._call_tree_visitor("echo < ''")

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "")
        self.assertEqual(file_output, None)

    def test_call_visitor_with_single_quotes(self):
        application, args, file_output = self._call_tree_visitor("echo 'foo'")

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "foo")
        self.assertEqual(file_output, None)

    def test_call_visitor_with_double_quotes(self):
        application, args, file_output = self._call_tree_visitor('echo "bar"')

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "bar")
        self.assertEqual(file_output, None)

    def test_call_visitor_with_back_quotes(self):
        application, args, file_output = self._call_tree_visitor("echo `fizz`")

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "fizz")
        self.assertEqual(file_output, None)

    def test_call_visitor_with_back_quotes_nested_in_double_quotes(self):
        application, args, file_output = self._call_tree_visitor(
            'echo "`fizz`"'
            )

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "fizz")
        self.assertEqual(file_output, None)

    def test_call_visitor_with_empty(self):
        application, args, file_output = self._call_tree_visitor("echo ''")

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "")
        self.assertEqual(file_output, None)

    def test_call_with_two_arguments_containing_no_quotes(self):
        application, args, file_output = self._call_tree_visitor(
            "echo foo bar"
            )

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 2)
        self.assertEqual(args[0], "foo")
        self.assertEqual(args[1], "bar")
        self.assertEqual(file_output, None)

    def test_call_with_argument_containing_quotes_with_spaces(self):
        application, args, file_output = self._call_tree_visitor(
            'echo "foo bar"'
            )

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "foo bar")
        self.assertEqual(file_output, None)

    def test_call_with_argument_containing_quoted_and_unquoted_content(self):
        application, args, file_output = self._call_tree_visitor('echo f"o"o')

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "foo")
        self.assertEqual(file_output, None)

    def test_call_with_argument_containing_quoted_asterisk(self):
        application, args, file_output = self._call_tree_visitor(
            'echo "*.txt"'
            )

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "*.txt")
        self.assertEqual(file_output, None)

    def test_argument_with_globbing(self):
        application, args, file_output = self._call_tree_visitor(
            'echo unittests/*.txt'
            )
        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)

        res = args[0].split(' ')
        res.sort()

        self.assertListEqual(
            res, [
                "unittests/test1.txt",
                "unittests/test2.txt",
                "unittests/test3.txt"
                ]
                )
        self.assertEqual(file_output, None)

    def test_argument_with_unquoted_asterisk_and_globbing_equal_to_false(self):
        application, args, file_output = self._call_tree_visitor("echo *.lark")

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "*.lark")
        self.assertEqual(file_output, None)

    def test_call_with_quoted_application(self):
        application, args, file_output = self._call_tree_visitor('"echo" foo')

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "foo")
        self.assertEqual(file_output, None)

    def test_call_with_part_quoted_and_unquoted_application(self):
        application, args, file_output = self._call_tree_visitor("e'ch'o foo")

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "foo")
        self.assertEqual(file_output, None)

    def test_call_with_prefix_redirection(self):
        application, args, file_output = self._call_tree_visitor(
            "< file.txt echo"
            )

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "file.txt")
        self.assertEqual(file_output, None)

    def test_invalid_call(self):
        self.assertEqual(
            self.parser.call_level_parse("echo AAA >> file.txt"), False
            )


if __name__ == "__main__":
    unittest.main()
