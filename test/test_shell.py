import subprocess
import unittest
from collections import deque
# from hypothesis import example, given, strategies as st
# export PYTHONPATH="./src"
from shell import eval as shell_evaluator
import applications as app
from commands import Call, Pipe, Seq

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


if __name__ == "__main__":
    unittest.main()
