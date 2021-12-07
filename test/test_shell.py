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
        p = subprocess.run(["rm", "-r", "unittests"], stdout=subprocess.DEVNULL)
        if p.returncode != 0:
            print("error: failed to remove unittests directory")
            exit(1)

    def _call_tree_visitor(self, cmd):
        call_tree = self.parser.call_level_parse(cmd)

        call_tree_visitor = CallTreeVisitor()
        call_tree_visitor.visit_topdown(call_tree)

        return call_tree_visitor.application, call_tree_visitor.args, call_tree_visitor.file_output


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
        application, args, file_output = self._call_tree_visitor("echo < file.txt")

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "file.txt")
        self.assertEqual(file_output, None)
    
    def test_redirection_visitor_output(self):
        application, args, file_output = self._call_tree_visitor("echo foo > file.txt")

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "foo")
        self.assertEqual(file_output, "file.txt")

    def test_redirection_visitor_with_single_quoted_file_name(self):
        application, args, file_output = self._call_tree_visitor("echo < 'file.txt'")

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "file.txt")
        self.assertEqual(file_output, None)

    def test_redirection_visitor_with_double_quoted_file_name(self):
        application, args, file_output = self._call_tree_visitor('echo < "file.txt"')

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "file.txt")
        self.assertEqual(file_output, None)
    
    def test_redirection_visitor_with_back_quoted_file_name(self):
        application, args, file_output = self._call_tree_visitor("echo < `echo file.txt`")

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "echo file.txt")
        self.assertEqual(file_output, None)

    def test_redirection_visitor_with_nested_back_quoted_file_name_in_double_quotes(self):
        application, args, file_output = self._call_tree_visitor('echo < "`echo file.txt`"')

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
        application, args, file_output = self._call_tree_visitor('echo `fizz`')

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "fizz")
        self.assertEqual(file_output, None)
    
    def test_call_visitor_with_back_quotes_nested_in_double_quotes(self):
        application, args, file_output = self._call_tree_visitor('echo "`fizz`"')

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
        application, args, file_output = self._call_tree_visitor('echo foo bar')

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 2)
        self.assertEqual(args[0], "foo")
        self.assertEqual(args[1], "bar")
        self.assertEqual(file_output, None)

    def test_call_with_argument_containing_quotes_with_spaces(self):
        application, args, file_output = self._call_tree_visitor('echo "foo bar"')

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
        application, args, file_output = self._call_tree_visitor('echo "*.txt"')

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "*.txt")
        self.assertEqual(file_output, None)

    def test_argument_with_globbing(self):
        application, args, file_output = self._call_tree_visitor('echo unittests/*.txt')

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "unittests/test1.txt unittests/test3.txt unittests/test2.txt")
        self.assertEqual(file_output, None)

    def test_argument_with_unquoted_asterisk_and_globbing_equal_to_false(self):
        application, args, file_output = self._call_tree_visitor('echo *.lark')

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
        application, args, file_output = self._call_tree_visitor("< file.txt echo")

        self.assertEqual(application, "echo")
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], "file.txt")
        self.assertEqual(file_output, None)

    def test_invalid_call(self):
        self.assertEqual(self.parser.call_level_parse("echo AAA >> file.txt"), False)

class TestCommands(unittest.TestCase):

    def setUp(self):
        self.out = deque()

    def test_call(self):
        call = Call("echo foo")
        call.eval(self.out)

        self.assertEquals(call.application, "echo")
        self.assertEquals(len(call.args), 1)
        self.assertEquals(call.args[0], "foo")

        self.assertEquals(self.out.pop().strip(), "foo")
    
    def test_invalid_call(self):
        call = Call("echo AAA >> file.txt")
        call.eval(self.out)

        self.assertEquals(self.out.pop(), "Unrecognized Command: echo AAA >> file.txt")
    
    def test_empty_call(self):
        call = Call("")
        call.eval(self.out)
        self.assertEquals(len(self.out), 0)

    def test_empty_application(self):
        call = Call("'' foo")
        call.eval(self.out)
        self.assertEquals(len(self.out), 0)
        self.assertEquals(call.application, "")

    def test_pipe(self):
        pipe = Pipe(Call("echo abc"), Call("cut -b 1"))
        pipe.eval(self.out)
        self.assertEquals(len(self.out), 1)
        self.assertEquals(self.out.pop().strip(), "a")
    
    def test_nested_pipe(self):
        pipe = Pipe(Pipe(Call("echo abc"), Call("cut -b -1,2-")), Call("cut -b 1"))
        pipe.eval(self.out)
        self.assertEquals(len(self.out), 1)
        self.assertEquals(self.out.pop().strip(), "a") 

    def test_seq(self):
        seq = Seq([Call("echo foo"), Call("echo bar")])
        seq.eval(self.out)
        self.assertEquals(len(self.out), 2)
        self.assertEquals(self.out.pop().strip(), "bar")
        self.assertEquals(self.out.pop().strip(), "foo")


if __name__ == "__main__":
    unittest.main()
