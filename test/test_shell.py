import subprocess
import unittest
from collections import deque
import os

# from hypothesis import example, given, strategies as st
# export PYTHONPATH="./src"
from shell import eval as shell_evaluator
import applications as app
from commands import Call, Pipe, Seq
from parser import Parser
from command_evaluator import extract_raw_commands

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


class TestApplications(unittest.TestCase):
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
                "echo DDD > dir1/.test3.txt",
                "mkdir dir2",
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

    def test_pwd_with_args(self):
        pwd = app.Pwd()
        self.assertRaises(
            app.ApplicationExcecutionError, pwd.exec, [""], self.out, False
        )

    def test_pwd(self):
        pwd = app.Pwd()
        pwd.exec([], self.out, False)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop().strip(), os.getcwd())

    def test_cd_no_args(self):
        cd = app.Cd()
        self.assertRaises(app.ApplicationExcecutionError, cd.exec, [], self.out, False)

    def test_cd_multiple_args(self):
        cd = app.Cd()
        self.assertRaises(
            app.ApplicationExcecutionError, cd.exec, ["dir1", "dir2"], self.out, False
        )

    def test_cd_fake_directory(self):
        cd = app.Cd()
        self.assertRaises(FileNotFoundError, cd.exec, ["dir3"], self.out, False)

    def test_cd(self):
        cd = app.Cd()
        old_file_path = os.getcwd()
        cd.exec(["unittests"], self.out, False)
        self.assertEqual(len(self.out), 0)
        self.assertEqual(old_file_path + "/unittests", os.getcwd())
        cd.exec([".."], self.out, False)

    def test_ls_get_directory_no_args(self):
        ls = app.Ls()
        self.assertEqual(ls._get_directory([]), os.getcwd())

    def test_ls_get_directory_one_arg(self):
        ls = app.Ls()
        self.assertEqual(ls._get_directory(["dir1"]), "dir1")

    def test_ls_get_directory_multiple_args(self):
        ls = app.Ls()
        self.assertRaises(
            app.ApplicationExcecutionError, ls._get_directory, ["dir1", "dir2"]
        )

    def test_ls_invalid_arg(self):
        ls = app.Ls()
        self.assertRaises(FileNotFoundError, ls.exec, ["dir3"], self.out, False)

    def test_ls_hidden_file(self):
        ls = app.Ls()
        ls.exec(["unittests/dir1"], self.out, False)
        self.assertEqual(len(self.out), 1)
        result = self.out.pop().splitlines()
        result.sort()
        self.assertListEqual(result, ["hello.txt"])

    def test_ls_valid_arg(self):
        ls = app.Ls()
        ls.exec(["unittests"], self.out, False)
        self.assertEqual(len(self.out), 1)
        result = self.out.pop().splitlines()
        result.sort()
        self.assertListEqual(
            result, ["dir1", "dir2", "test1.txt", "test2.txt", "test3.txt"]
        )

    def test_cat_no_args(self):
        cat = app.Cat()
        self.assertRaises(app.ApplicationExcecutionError, cat.exec, [], self.out, False)

    def test_cat_no_args_in_pipe(self):
        self.out.append("unittests/test2.txt")
        print("unittests/test2.txt".strip())
        cat = app.Cat()
        cat.exec([], self.out, True)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(
            self.out.pop().strip(),
            "BBB",
        )

    def test_cat_invalid_file(self):
        cat = app.Cat()
        self.assertRaises(
            FileNotFoundError, cat.exec, ["dir5/test.txt"], self.out, False
        )

    def test_cat_folder(self):
        cat = app.Cat()
        self.assertRaises(FileNotFoundError, cat.exec, ["dir5"], self.out, False)

    def test_cat(self):
        cat = app.Cat()
        cat.exec(["unittests/test1.txt"], self.out, False)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(
            self.out.pop().strip(),
            "abcdef had a dog, then they had a book \n When it asdtnnasn it wanted to asjdiansdnainsd it siansdinanis",
        )

    def test_echo_no_args(self):
        echo = app.Echo()
        echo.exec([], self.out, False)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop().strip(), "")

    def test_echo_multiple_args(self):
        echo = app.Echo()
        echo.exec(["hello", "world"], self.out, False)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop().strip(), "hello world")

    def test_echo(self):
        echo = app.Echo()
        echo.exec(["foo bar"], self.out, False)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop().strip(), "foo bar")


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
