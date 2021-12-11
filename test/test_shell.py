import subprocess
import unittest
from collections import deque
from shell import eval as shell_evaluator


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
        self.text = ('abcdef had a dog, then they had a book \n'
                     ' When it asdtnnasn it wanted to asjdiansdnainsd it'
                     ' siansdinanis')
        filesystem_setup = ";".join(
            [
                "cd unittests",
                "echo '' > test1.txt",
                "echo BBB > test2.txt",
                "echo CCC > test3.txt",
                "mkdir dir1",
                "echo 'HELLO THERE' > dir1/hello.txt",
            ]
        )
        self.prepare(filesystem_setup)
        self.out = deque()

    def tearDown(self):
        p = subprocess.run(
            ["rm", "-r", "unittests"], stdout=subprocess.DEVNULL
            )
        if p.returncode != 0:
            print("error: failed to remove unittests directory")
            exit(1)

    def test_eval(self):
        out = deque()
        shell_evaluator("echo foo", out)
        self.assertEqual(out.popleft(), "foo\n")
        self.assertEqual(len(out), 0)

    def test_eval_with_unrecognised_command(self):
        out = deque()
        shell_evaluator("echo '''", out)
        self.assertEqual(out.popleft(), "Unrecognized Input: echo '''\n")
        self.assertEqual(len(out), 0)


if __name__ == "__main__":
    unittest.main()
