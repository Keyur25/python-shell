import subprocess
import unittest
from collections import deque
import os
import re

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
                "echo 'a\nb\nc\nd\ne\nf\ng\nh\ni\nj\nk\nl\nm\nn\no\np\nq\nr\ns\nt\nu\nv\nw\nx\ny\nz' > alphabet.txt",
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
            result,
            ["alphabet.txt", "dir1", "dir2", "test1.txt", "test2.txt", "test3.txt"],
        )

    def test_cat_no_args(self):
        cat = app.Cat()
        self.assertRaises(app.ApplicationExcecutionError, cat.exec, [], self.out, False)

    def test_cat_stdin(self):
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

    def test_head_read_first_n_lines_from_file_fake_file(self):
        head = app.Head()
        self.assertRaises(
            FileNotFoundError,
            head._read_first_n_lines_from_file,
            "unittests/test4.txt",
            10,
            self.out,
        )

    def test_head_read_first_n_lines_from_file_n_is_zero(self):
        head = app.Head()
        head._read_first_n_lines_from_file("unittests/alphabet.txt", 0, self.out)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop().strip(), "")

    def test_head_read_first_n_lines_from_file_n_is_negative(self):
        head = app.Head()
        head._read_first_n_lines_from_file("unittests/alphabet.txt", -2, self.out)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop().strip(), "")

    def test_head_read_first_n_lines_from_file(self):
        head = app.Head()
        head._read_first_n_lines_from_file("unittests/alphabet.txt", 5, self.out)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(
            self.out.pop().split(),
            ["a", "b", "c", "d", "e"],
        )

    def test_head_no_args(self):
        head = app.Head()
        self.assertRaises(
            app.ApplicationExcecutionError, head.exec, [], self.out, False
        )

    def test_head_stdin(self):
        self.out.append("unittests/alphabet.txt")
        head = app.Head()
        head.exec([], self.out, True)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(
            self.out.pop().split(),
            ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
        )

    def test_head_two_args(self):
        head = app.Head()
        self.assertRaises(
            app.ApplicationExcecutionError,
            head.exec,
            ["15", "unittests/alphabet.txt"],
            self.out,
            False,
        )

    def test_head_wrong_flag(self):
        head = app.Head()
        self.assertRaises(
            app.ApplicationExcecutionError,
            head.exec,
            ["-number", "5", "unittests/alphabet.txt"],
            self.out,
            False,
        )

    def test_head_n_flag_string(self):
        head = app.Head()
        self.assertRaises(
            app.ApplicationExcecutionError,
            head.exec,
            ["-n", "five", "unittests/alphabet.txt"],
            self.out,
            False,
        )

    def test_head_n_flag_over_limit(self):
        head = app.Head()
        head.exec(["-n", "30", "unittests/alphabet.txt"], self.out, False)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(
            self.out.pop().split(),
            "a\nb\nc\nd\ne\nf\ng\nh\ni\nj\nk\nl\nm\nn\no\np\nq\nr\ns\nt\nu\nv\nw\nx\ny\nz".split(),
        )

    def test_head_n_flag(self):
        head = app.Head()
        head.exec(["-n", "4", "unittests/alphabet.txt"], self.out, False)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(
            self.out.pop().split(),
            ["a", "b", "c", "d"],
        )

    def test_head(self):
        head = app.Head()
        head.exec(["unittests/alphabet.txt"], self.out, False)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(
            self.out.pop().split(),
            ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
        )

    def test_tail_read_last_n_lines_from_file_fake_file(self):
        tail = app.Tail()
        self.assertRaises(
            FileNotFoundError,
            tail._read_last_n_lines_from_file,
            "unittests/test4.txt",
            10,
            self.out,
        )

    def test_tail_read_last_n_lines_from_file_n_is_zero(self):
        tail = app.Tail()
        tail._read_last_n_lines_from_file("unittests/alphabet.txt", 0, self.out)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop().strip(), "")

    def test_tail_read_last_n_lines_from_file_n_is_negative(self):
        tail = app.Tail()
        tail._read_last_n_lines_from_file("unittests/alphabet.txt", -2, self.out)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop().strip(), "")

    def test_tail_read_last_n_lines_from_file(self):
        tail = app.Tail()
        tail._read_last_n_lines_from_file("unittests/alphabet.txt", 5, self.out)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(
            self.out.pop().split(),
            ["v", "w", "x", "y", "z"],
        )

    def test_tail_no_args(self):
        tail = app.Tail()
        self.assertRaises(
            app.ApplicationExcecutionError, tail.exec, [], self.out, False
        )

    def test_tail_stdin(self):
        self.out.append("unittests/alphabet.txt")
        tail = app.Tail()
        tail.exec([], self.out, True)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(
            self.out.pop().split(),
            ["q", "r", "s", "t", "u", "v", "w", "x", "y", "z"],
        )

    def test_tail_two_args(self):
        tail = app.Tail()
        self.assertRaises(
            app.ApplicationExcecutionError,
            tail.exec,
            ["15", "unittests/alphabet.txt"],
            self.out,
            False,
        )

    def test_tail_wrong_flag(self):
        tail = app.Tail()
        self.assertRaises(
            app.ApplicationExcecutionError,
            tail.exec,
            ["-number", "5", "unittests/alphabet.txt"],
            self.out,
            False,
        )

    def test_tail_n_flag_string(self):
        tail = app.Tail()
        self.assertRaises(
            app.ApplicationExcecutionError,
            tail.exec,
            ["-n", "five", "unittests/alphabet.txt"],
            self.out,
            False,
        )

    def test_tail_n_flag_over_limit(self):
        tail = app.Tail()
        tail.exec(["-n", "30", "unittests/alphabet.txt"], self.out, False)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(
            self.out.pop().split(),
            "a\nb\nc\nd\ne\nf\ng\nh\ni\nj\nk\nl\nm\nn\no\np\nq\nr\ns\nt\nu\nv\nw\nx\ny\nz".split(),
        )

    def test_tail_n_flag(self):
        tail = app.Tail()
        tail.exec(["-n", "4", "unittests/alphabet.txt"], self.out, False)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(
            self.out.pop().split(),
            ["w", "x", "y", "z"],
        )

    def test_tail(self):
        tail = app.Tail()
        tail.exec(["unittests/alphabet.txt"], self.out, False)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(
            self.out.pop().split(),
            ["q", "r", "s", "t", "u", "v", "w", "x", "y", "z"],
        )
    
    """testing grep"""

    def test_grep_find_matches_from_stdin_with_match_all(self):
        grep = app.Grep()
        pattern = "..."
        lines = ["AAA", "BBB", "CCC"]
        grep._find_matches_from_stdin(pattern, lines, self.out)

        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop(), "AAA\nBBB\nCCC")
    
    def test_grep_find_matches_from_stdin_with_partial_match(self):
        grep = app.Grep()
        pattern = "A.."
        lines = ["AAA", "BBB", "CCC"]
        grep._find_matches_from_stdin(pattern, lines, self.out)

        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop(), "AAA")
    
    def test_grep_find_matches_from_stdin_with_no_match(self):
        grep = app.Grep()
        pattern = "D.."
        lines = ["AAA", "BBB", "CCC"]
        grep._find_matches_from_stdin(pattern, lines, self.out)

        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop(), "")
    
    def test__grep_with_match_all(self):
        grep = app.Grep()
        pattern = "..."
        multiple_files = False
        contents = []
        file = "test.txt"
        lines = ["AAA", "BBB", "CCC"]
        grep._grep(pattern, multiple_files, contents, file, lines)
        self.assertListEqual(contents, ["AAA", "BBB", "CCC"])
    
    def test__grep_with_partial_match(self):
        grep = app.Grep()
        pattern = "A.."
        multiple_files = False
        contents = []
        file = "test.txt"
        lines = ["AAA", "ABB", "CCC"]
        grep._grep(pattern, multiple_files, contents, file, lines)
        self.assertListEqual(contents, ["AAA", "ABB"])
    
    def test__grep_with_no_match(self):
        grep = app.Grep()
        pattern = "D.."
        multiple_files = False
        contents = []
        file = "test.txt"
        lines = ["AAA", "ABB", "CCC"]
        grep._grep(pattern, multiple_files, contents, file, lines)
        self.assertEqual(contents, [])
    
    def test__grep_with_multiple_files_set_to_true(self):
        grep = app.Grep()
        pattern = "A.."
        multiple_files = True
        contents = []
        file = "test.txt"
        lines = ["AAA", "ABB", "CCC"]
        grep._grep(pattern, multiple_files, contents, file, lines)
        self.assertListEqual(contents, ["test.txt:AAA", "test.txt:ABB"])
    
    def test_find_matches_from_files_with_one_file(self):
        grep = app.Grep()
        pattern = "BBB"
        files = ["unittests/test2.txt"]
        grep._find_matches_from_files(pattern, files, self.out)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop(), "BBB")
    
    def test_find_matches_from_files_with_multiple_files(self):
        grep = app.Grep()
        pattern = "..."
        files = ["unittests/test2.txt", "unittests/test3.txt"]
        grep._find_matches_from_files(pattern, files, self.out)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(self.out.pop().split("\n"), ["unittests/test2.txt:BBB", "unittests/test3.txt:CCC"])
    
    def test_grep_with_no_arguments(self):
        grep = app.Grep()
        args = []
        self.assertRaises(app.ApplicationExcecutionError, grep.exec, args, self.out, False)
    
    def test_grep_with_one_argument_and_in_pipe_set_to_false(self):
        grep = app.Grep()
        args = ["foo"]
        in_pipe = False
        self.assertRaises(app.ApplicationExcecutionError, grep.exec, args, self.out, in_pipe)

    def test_grep_in_pipe(self):
        grep = app.Grep()
        self.out.append("AAA") # simulate a prev. commands output in pipe
        args = ["..."]
        in_pipe = True
        grep.exec(args, self.out, in_pipe)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop(), "AAA")

    def test_grep(self):
        grep = app.Grep()
        args = ["B..", "unittests/test2.txt", "unittests/test3.txt"]
        in_pipe = False
        grep.exec(args, self.out, in_pipe)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(self.out.pop().split("\n"), ["unittests/test2.txt:BBB"])

    def test_find_get_path_and_pattern_no_args(self):
        find = app.Find()
        self.assertRaises(
            app.ApplicationExcecutionError,
            find._get_path_and_pattern,
            [],
        )

    def test_find_get_path_and_pattern_two_args_no_name(self):
        find = app.Find()
        self.assertRaises(
            app.ApplicationExcecutionError,
            find._get_path_and_pattern,
            ["-n", "pattern"],
        )

    def test_find_get_path_and_pattern_three_args_no_name(self):
        find = app.Find()
        self.assertRaises(
            app.ApplicationExcecutionError,
            find._get_path_and_pattern,
            ["path", "-n", "pattern"],
        )

    def test_find_get_path_and_pattern_two_args(self):
        find = app.Find()
        path, pattern = find._get_path_and_pattern(["-name", "pattern"])
        self.assertEqual(path, "./")
        self.assertEqual(pattern, "pattern")

    def test_find_get_path_and_pattern_three_args(self):
        find = app.Find()
        path, pattern = find._get_path_and_pattern(["path", "-name", "pattern"])
        self.assertEqual(path, "path")
        self.assertEqual(pattern, "pattern")

    def test_find_no_matches(self):
        find = app.Find()
        find.exec(["unittests", "-name", "test4.txt"], self.out, False)
        result = set(re.split("\n|\t", self.out.pop().strip()))
        self.assertEqual(result, {""})

    def test_find_asterisk(self):
        find = app.Find()
        find.exec(["unittests", "-name", "*.txt"], self.out, False)
        result = set(re.split("\n|\t", self.out.pop().strip()))
        self.assertEqual(
            result,
            {
                "unittests/test2.txt",
                "unittests/test3.txt",
                "unittests/test1.txt",
                "unittests/alphabet.txt",
                "unittests/dir1/hello.txt",
            },
        )

    def test_find(self):
        find = app.Find()
        find.exec(["unittests", "-name", "hello.txt"], self.out, False)
        result = set(re.split("\n|\t", self.out.pop().strip()))
        self.assertEqual(result, {"unittests/dir1/hello.txt"})

    def test_sort_sort_contents_empty_contents(self):
        sort = app.Sort()
        sort._sort_contents([], self.out)
        self.assertEqual(len(self.out), 0)

    def test_sort_sort_contents_reverse(self):
        sort = app.Sort()
        sort._sort_contents(["c", "o", "n", "t", "e", "n", "t", "s"], self.out, True)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop().strip(), "ttsonnec")

    def test_sort_sort_contents(self):
        sort = app.Sort()
        sort._sort_contents(["c", "o", "n", "t", "e", "n", "t", "s"], self.out)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop().strip(), "cennostt")

    def test_sort_read_file_fake_file(self):
        sort = app.Sort()
        self.assertRaises(
            FileNotFoundError,
            sort._read_file,
            "unittests/test4.txt",
        )

    def test_sort_read_file(self):
        sort = app.Sort()
        self.assertListEqual(
            sort._read_file("unittests/test1.txt"),
            [
                "abcdef had a dog, then they had a book \n",
                " When it asdtnnasn it wanted to asjdiansdnainsd it siansdinanis\n",
            ],
        )

    def test_sort_input_from_stdin_list(self):
        sort = app.Sort()
        self.assertListEqual(
            sort._input_from_stdin([["AAA"]]),
            ["AAA"],
        )

    def test_sort_input_from_stdin_str(self):
        sort = app.Sort()
        self.assertListEqual(
            sort._input_from_stdin(["AAA"]),
            ["AAA"],
        )

    def test_sort_input_from_stdin_int(self):
        sort = app.Sort()
        self.assertRaises(
            app.ApplicationExcecutionError,
            sort._input_from_stdin,
            [2],
        )

    def test_sort_reverse_options_no_args(self):
        sort = app.Sort()
        self.assertRaises(
            app.ApplicationExcecutionError,
            sort._reverse_options,
            [],
            self.out,
            0,
        )

    def test_sort_no_args(self):
        sort = app.Sort()
        self.assertRaises(
            app.ApplicationExcecutionError, sort.exec, [], self.out, False
        )

    def test_sort_stdin(self):
        sort = app.Sort()
        self.out.append("c\no\nn\nt\ne\nn\nt\ns\n")
        sort.exec([], self.out, True)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop(), "c\ne\nn\nn\no\ns\nt\nt\n")

    def test_sort_stdin_reverse(self):
        pass
        sort = app.Sort()
        self.out.append("c\no\nn\nt\ne\nn\nt\ns\n")
        sort.exec(["-r"], self.out, True)
        self.assertEqual(len(self.out), 1)
        self.assertEqual(self.out.pop(), "t\nt\ns\no\nn\nn\ne\nc\n")

    def test_sort_multiple_args(self):
        sort = app.Sort()
        self.assertRaises(
            app.ApplicationExcecutionError,
            sort.exec,
            ["-", "r", "unittests/test1.txt"],
            self.out,
            False,
        )

    def test_sort_reverse(self):
        sort = app.Sort()
        sort.exec(["-r", "unittests/alphabet.txt"], self.out, False)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(
            self.out.pop().strip().split("\n"),
            [
                "z",
                "y",
                "x",
                "w",
                "v",
                "u",
                "t",
                "s",
                "r",
                "q",
                "p",
                "o",
                "n",
                "m",
                "l",
                "k",
                "j",
                "i",
                "h",
                "g",
                "f",
                "e",
                "d",
                "c",
                "b",
                "a",
            ],
        )

    def test_sort(self):
        sort = app.Sort()
        sort.exec(["unittests/test1.txt"], self.out, False)
        self.assertEqual(len(self.out), 1)
        self.assertListEqual(
            self.out.pop().strip().split("\n"),
            [
                "When it asdtnnasn it wanted to asjdiansdnainsd it siansdinanis",
                "abcdef had a dog, then they had a book",
            ],
        )


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
