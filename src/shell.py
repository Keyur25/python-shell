import re
import sys
import os
from os import listdir
from collections import deque
from glob import glob


class Pwd:
    def exec(self, args, out):
        out.append(os.getcwd())


class Cd:

    """Change current working directory to args[0]"""

    def exec(self, args, out):
        if len(args) == 0 or len(args) > 1:
            raise ValueError("wrong number of command line arguments")
        os.chdir(args[0])


class Echo:

    """Prints the argument passed into echo"""

    def exec(self, args, out):
        out.append(" ".join(args) + "\n")


class Ls:

    """List the files in current directory"""

    def exec(self, args, out):
        if len(args) == 0:
            ls_dir = os.getcwd()
        elif len(args) > 1:
            raise ValueError("wrong number of command line arguments")
        else:
            ls_dir = args[0]
        for f in listdir(ls_dir):
            if not f.startswith("."):
                out.append(f + "\n")


class Cat:

    """Print the contents of a file specified by args line by line"""

    def exec(self, args, out):
        for a in args:
            with open(a) as f:
                out.append(f.read())


class Head:

    """
    By default writes the last 10 lines of a file to standard output,
    or an inputted number of lines with flag -n.
    """

    def _read_file(self, file, size_of_head):
        with open(file) as f:
            lines = f.readlines()
            for i in range(0, min(len(lines), size_of_head)):
                out.append(lines[i])

    def exec(self, args, out):
        no_of_args = len(args)
        if no_of_args != 1 and no_of_args != 3:
            raise ValueError("wrong number of command line arguments")
        elif no_of_args == 1:  # default case
            size_of_head = 10
            file = args[0]
        elif no_of_args == 3:  # when using -n [number] flag
            if args[0] != "-n":
                raise ValueError("wrong flags")
            size_of_head = int(args[1])
            file = args[2]

        self._read_file(file, size_of_head)


class Tail:

    """
    By default writes the last 10 lines of a file to standard output,
    or an inputted number of lines with flag -n.
    """

    def _read_file(self, file, size_of_tail):
        with open(file) as f:
            lines = f.readlines()
            no_of_lines = len(lines)
            display_length = min(no_of_lines, size_of_tail)
            for i in range(0, display_length):
                out.append(lines[no_of_lines - display_length + i])

    def exec(self, args, out):
        no_of_args = len(args)
        if no_of_args != 1 and no_of_args != 3:
            raise ValueError("wrong number of command line arguments")
        if no_of_args == 1:
            size_of_tail = 10
            file = args[0]
        if no_of_args == 3:
            if args[0] != "-n":
                raise ValueError("wrong flags")
            else:
                size_of_tail = int(args[1])
                file = args[2]

        self._read_file(out, file, size_of_tail)


class Grep:
    def exec(self, args, out):
        if len(args) < 2:
            raise ValueError("wrong number of command line arguments")
        pattern = args[0]
        files = args[1:]
        for file in files:
            with open(file) as f:
                lines = f.readlines()
                for line in lines:
                    if re.match(pattern, line):
                        if len(files) > 1:
                            out.append(f"{file}:{line}")
                        else:
                            out.append(line)


def eval(cmdline, out):
    raw_commands = []
    for m in re.finditer("([^\"';]+|\"[^\"]*\"|'[^']*')", cmdline):
        if m.group(0):
            raw_commands.append(m.group(0))
    for command in raw_commands:
        tokens = []
        for m in re.finditer("[^\\s\"']+|\"([^\"]*)\"|'([^']*)'", command):
            if m.group(1) or m.group(2):
                quoted = m.group(0)
                tokens.append(quoted[1:-1])
            else:
                globbing = glob(m.group(0))
                if globbing:
                    tokens.extend(globbing)
                else:
                    tokens.append(m.group(0))
        app = tokens[0]
        args = tokens[1:]
        if app == "pwd":
            application = Pwd()
        elif app == "cd":
            application = Cd()
        elif app == "echo":
            application = Echo()
        elif app == "ls":
            application = Ls()
        elif app == "cat":
            application = Cat()
        elif app == "head":
            application = Head()
        elif app == "tail":
            application = Tail()
        elif app == "grep":
            application = Grep()
        else:
            raise ValueError(f"unsupported application {app}")

        application.exec(args, out)


if __name__ == "__main__":
    args_num = len(sys.argv) - 1  # number of args excluding script name
    if args_num > 0:  # checks for correct args for non interactive mode
        if args_num != 2:
            raise ValueError("wrong number of command line arguments")
        if sys.argv[1] != "-c":
            raise ValueError(f"unexpected command line argument {sys.argv[1]}")
        out = deque()
        eval(sys.argv[2], out)
        while len(out) > 0:
            print(out.popleft(), end="")
    else:
        while True:
            print(os.getcwd() + "> ", end="")
            cmdline = input()
            out = deque()
            eval(cmdline, out)
            while len(out) > 0:
                print(out.popleft(), end="")
