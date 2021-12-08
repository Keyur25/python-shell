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
                "mkdir dir1",
                "mkdir dir2",
                "echo 'HELLO THERE' > dir1/hello.txt",
                "echo 'random' > dir1/random.txt",
                "echo CCC > outer.txt",
                "echo SOMETHING > outer2.txt"
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
        self.assertNotEqual(current_opts, new_opts)
        self.assertCountEqual(new_opts, ["cd", "clear", "cat"])
    
    def test_options_to_files_and_folders(self):
        self.completer.set_options_to_files_and_folders("unittests/")
        self.assertCountEqual(self.completer.options, ["dir1", "dir2", "outer.txt", "outer2.txt"])

        self.completer.set_options_to_files_and_folders("unittests/dir1/")
        self.assertCountEqual(self.completer.options, ["hello.txt", "random.txt"])
    
    def test_autocomplete_application(self):
        apps = APPLICATIONS.keys()
        text = "c"
        i = 0
        res = []
        for app in apps:
            if app.startswith(text):
                res.append(self.completer.autocomplete_application(text, i))
                i += 1
        res.append(self.completer.autocomplete_application(text, i+1))
        self.assertCountEqual(res, ["cd", "cat", "clear", "cut", None])

    def test_autocomplete_flag(self):
        text = "head -"
        text_split = text.split(' ')
        apps = APPLICATIONS.keys()
        for app in apps:
            if APPLICATIONS.get(app) != "" and text_split[0] == app:
                res = self.completer.autocomplete_flag(text_split, "", 0)
                break
        self.assertEqual(res, 'n')
    
    def test_autocomplete_folder(self):
        text = "cd unit"
        text_split = text.split(' ')
        res = []
        for i in range(0, 2):
            res.append(self.completer.autocomplete_files_and_folders(text_split, text_split[-1], i))
        self.assertCountEqual(res, ["unittests/", None])

    def test_autocomplete_folder_duplicate(self):
        text = "cd unittests/dir"
        text_split = text.split(' ')
        res = []
        for i in range(0, 3):
            res.append(self.completer.autocomplete_files_and_folders(text_split, "dir", i))
        self.assertCountEqual(res, ["dir1/", "dir2/", None])

    def test_autocomplete_file(self):
        text = "cd unittests/dir1/h"
        text_split = text.split(' ')
        res = []
        for i in range(0, 2):
            res.append(self.completer.autocomplete_files_and_folders(text_split, "h", i))
        self.assertCountEqual(res, ["hello.txt", None])

    def test_autocomplete_file_duplicate(self):
        text = "cd unittests/dir1/"
        text_split = text.split(' ')
        res = []
        for i in range(0, 3):
            res.append(self.completer.autocomplete_files_and_folders(text_split, "", i))
        self.assertCountEqual(res, ["hello.txt", "random.txt", None])
    
        

    


if __name__ == "__main__":
    unittest.main()