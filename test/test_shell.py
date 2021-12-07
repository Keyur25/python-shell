import subprocess
import unittest
from collections import deque
# from hypothesis import example, given, strategies as st
# export PYTHONPATH="./src"
from shell import eval as shell_evaluator
import applications as app
from commands import Call, Pipe, Seq
from parser import Parser
from command_evaluator import extract_raw_commands
from collections import deque

from call_evaluator import CommandSubstituitionVisitor, CallTreeVisitor, InvalidCommandSubstitution


# TODO: Search up mutant testing
# TODO: research hypothesis libary for Python
#! We can use hypothesis-> See Q&A Lab For Wed Nov 17 -> 42:00
#! Use property based testing -> Using advanced librarys +3 and good reflection +2 on report

class TestShell(unittest.TestCase):
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
                "echo 'abcdef had a dog, then they had a book \n When it asdtnnasn it wanted to asjdiansdnainsd it siansdinanis' > test1.txt",
                "echo BBB > test2.txt",
                "echo CCC > test3.txt",
                "mkdir dir1",
                "echo 'HELLO THERE' > dir1/hello.txt",
            ]
        )
        self.prepare(filesystem_setup)
        self.out = deque()

    def tearDown(self):
        p = subprocess.run(["rm", "-r", "unittests"], stdout=subprocess.DEVNULL)
        if p.returncode != 0:
            print("error: failed to remove unittests directory")
            exit(1)

    def _eval_cmd(self, cmd):
        shell_evaluator("pwd", self.out)
        start_dir = self.out.pop()
        shell_evaluator("cd unittests", self.out)

        shell_evaluator(cmd, self.out)
        shell_result = self.out.pop()

        shell_evaluator(f"cd {start_dir}", self.out)

        return shell_result

    """********************************************************* Test Safe Applications *******************************************************************"""

    def test_ls(self):
        ls = app.Ls()
        ls.exec(["unittests"], self.out, False)
        result = self.out.pop().splitlines()
        result.sort()
        self.assertListEqual(result, ["dir1", "test1.txt", "test2.txt", "test3.txt"])

    def test_cat(self):
        cat = app.Cat()
        cat.exec(["unittests/test1.txt"], self.out, False)
        result = self.out.pop()
        self.assertEqual(
            result.strip(),
            "abcdef had a dog, then they had a book \n When it asdtnnasn it wanted to asjdiansdnainsd it siansdinanis",
        )

    def test_cat_no_args(self):
        cat = app.Cat()
        self.assertRaises(app.ApplicationExcecutionError, cat.exec, [], self.out, False)

    def test_cat_invalid_file(self):
        cat = app.Cat()
        self.assertRaises(
            FileNotFoundError, cat.exec, ["dir5/test.txt"], self.out, False
        )

    def test_cat_folder(self):
        cat = app.Cat()
        self.assertRaises(FileNotFoundError, cat.exec, ["dir5"], self.out, False)

    """**********************************************************************************************************************************************************"""

    """********************************************************* Test Unsafe Applications *******************************************************************"""

    def test_unsafe_ls(self):
        call = Call("_ls unittests/dir1")
        call.application = "_ls"
        call.args = ["unittests/dir1"]
        u_ls = app.UnsafeDecorator(app.Ls(), call)
        u_ls.exec(["unittests/dir1"], self.out, False)
        result = self.out.pop().splitlines()
        result.sort()
        self.assertListEqual(result, ["hello.txt"])

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

class TestCallEvaluator(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()
        self.out = deque()

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

        self.assertRaises(InvalidCommandSubstitution, command_substituition_visitor.visit, call_tree)

    def test_redirection_visitor_input(self):
        call_tree = self.parser.call_level_parse("echo < file.txt")

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "file.txt")
        self.assertEqual(call_tree_visitor.file_output, None)
    
    def test_redirection_visitor_output(self):
        call_tree = self.parser.call_level_parse("echo foo > file.txt")

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "foo")
        self.assertEqual(call_tree_visitor.file_output, "file.txt")

    def test_redirection_visitor_with_single_quoted_file_name(self):
        call_tree = self.parser.call_level_parse("echo < 'file.txt'")

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "file.txt")

    def test_redirection_visitor_with_double_quoted_file_name(self):
        call_tree = self.parser.call_level_parse('echo < "file.txt"')

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "file.txt")
    
    def test_redirection_visitor_with_back_quoted_file_name(self):
        call_tree = self.parser.call_level_parse("echo < `echo file.txt`")

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "echo file.txt")

    def test_redirection_visitor_with_nested_back_quoted_file_name_in_double_quotes(self):
        call_tree = self.parser.call_level_parse('echo < "`echo file.txt`"')

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "echo file.txt")

    def test_redirection_visitor_with_empty_quoted_file_name(self):
        call_tree = self.parser.call_level_parse("echo < ''")

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "")
    
    def test_call_visitor_with_single_quotes(self):
        call_tree = self.parser.call_level_parse("echo 'foo'")

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "foo")
    
    def test_call_visitor_with_double_quotes(self):
        call_tree = self.parser.call_level_parse('echo "bar"')

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "bar")

    def test_call_visitor_with_back_quotes(self):
        call_tree = self.parser.call_level_parse('echo `fizz`')

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "fizz")
    
    def test_call_visitor_with_back_quotes_nested_in_double_quotes(self):
        call_tree = self.parser.call_level_parse('echo "`fizz`"')

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "fizz")
    
    def test_call_with_two_arguments_containing_no_quotes(self):
        call_tree = self.parser.call_level_parse('echo foo bar')

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 2)
        self.assertEqual(call_tree_visitor.args[0], "foo")
        self.assertEqual(call_tree_visitor.args[1], "bar")

    def test_call_with_argument_containing_quotes_with_spaces(self):
        call_tree = self.parser.call_level_parse('echo "foo bar"')

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "foo bar")
    
    def test_call_with_argument_containing_quoted_and_unquoted_content(self):
        call_tree = self.parser.call_level_parse('echo f"o"o')

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "foo")
    
    def test_call_with_argument_containing_quoted_asterisk(self):
        call_tree = self.parser.call_level_parse('echo "*.txt"')

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "*.txt")

    # insert globbing test

    def test_call_with_quoted_application(self):
        call_tree = self.parser.call_level_parse('"echo" foo')

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "foo")
    
    def test_call_with_part_quoted_and_unquoted_application(self):
        call_tree = self.parser.call_level_parse("e'ch'o foo")

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        self.assertEqual(call_tree_visitor.application, "echo")
        self.assertEqual(len(call_tree_visitor.args), 1)
        self.assertEqual(call_tree_visitor.args[0], "foo")


    



    
    
    


    
    

if __name__ == "__main__":
    unittest.main()
