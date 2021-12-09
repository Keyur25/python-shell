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
    
    def test_eval(self):
        out = deque()
        shell_evaluator("echo foo", out)
        self.assertEqual(out.popleft(), "foo\n")
        self.assertEqual(len(out), 0)

    def test_eval_with_unrecognised_command(self):
        out = deque()
        shell_evaluator("echo '''", out)
        self.assertEqual(out.popleft(), "Unrecognized Input: echo '''")
        self.assertEqual(len(out), 0)

      
      
if __name__ == "__main__":
    unittest.main()
    
