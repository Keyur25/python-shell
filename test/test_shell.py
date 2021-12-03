import subprocess
import unittest
from collections import deque
from hypothesis import example, given, strategies as st

# TODO: Search up mutant testing
# TODO: research hypothesis libary for Python
#! We can use hypothesis-> See Q&A Lab For Wed Nov 17 -> 42:00
#! Use property based testing -> Using advanced librarys +3 and good reflection +2 on report

# Use python3 test/test_shell.py TestShell.test_shell to execute


class TestShell(unittest.TestCase):
    @classmethod
    def eval(cls, cmdline, shell="sh"):
        args = [
            shell,
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
                "echo \"''\" > test.txt",
                "mkdir dir1",
                "mkdir -p dir2/subdir",
                "echo AAA > dir1/file1.txt",
                "echo BBB >> dir1/file1.txt",
                "echo AAA >> dir1/file1.txt",
                "echo CCC > dir1/file2.txt",
                "for i in {1..20}; do echo $i >> dir1/longfile.txt; done",
                "echo AAA > dir2/subdir/file.txt",
                "echo aaa >> dir2/subdir/file.txt",
                "echo AAA >> dir2/subdir/file.txt",
                "touch dir1/subdir/.hidden",
                "cd ..",
            ]
        )
        self.eval(filesystem_setup, shell="/bin/bash")
        self.out = deque()

    def tearDown(self):
        p = subprocess.run(["rm", "-r", "unittests"], stdout=subprocess.DEVNULL)
        if p.returncode != 0:
            print("error: failed to remove unittests directory")
            exit(1)

    def test_shell(self):
        cmd = "echo foo"
        result = self.eval(cmd)
        self.assertEqual(result, "foo\n")

    @given(cmd=st.sampled_from(["pwd"]))
    def test_single_and_no_arg_commands(self, cmd):
        result = self.eval(cmd)
        self.assertEqual(result, "/workspaces/comp0010-shell-python-p22\n")


if __name__ == "__main__":
    unittest.main()
