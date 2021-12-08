import unittest
import subprocess
from autocomplete import APPLICATIONS, Completer


class TestCommandEvaluator(unittest.TestCase):
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
        self.completer = Completer(APPLICATIONS.keys())

    def tearDown(self):
        p = subprocess.run(["rm", "-r", "unittests"], stdout=subprocess.DEVNULL)
        if p.returncode != 0:
            print("error: failed to remove unittests directory")
            exit(1)
        
    
    def test_set_options(self):
        current_opts = self.completer.options
        self.completer.set_options(["cd", "clear", "cat"])
        new_opts = self.completer.options
        self.assertListEqual(current_opts, new_opts)
        self.assertCountEqual(new_opts, ["cd", "clear", "cat"])
    


if __name__ == "__main__":
    unittest.main()