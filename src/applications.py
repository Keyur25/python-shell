import os
import re
import sys
from os import listdir, path
import glob

class Pwd:

    """Prints current working directory"""

    def exec(self, args, out, in_pipe):
        out.append(os.getcwd())


class Cd:

    """Change current working directory to args[0]"""

    def exec(self, args, out, in_pipe):
        if len(args) == 0 or len(args) > 1:
            raise ValueError("wrong number of command line arguments")
        os.chdir(args[0])


class Echo:

    """Prints the argument passed into echo"""

    def exec(self, args, out, in_pipe):
        out.append(" ".join(args) + "\n")


class Ls:

    """List the files in current directory"""

    def exec(self, args, out, in_pipe):
        if len(args) == 0:
            ls_dir = os.getcwd()
        elif len(args) > 1:
            raise ValueError("wrong number of command line arguments")
        else:
            ls_dir = args[0]
        for f in listdir(ls_dir):
            if not f.startswith("."):
                if path.isdir(
                    f
                ):  # If f is a directory/folder colour it and then print it out
                    out.append(f + "\n")
                else:  # f is a file
                    out.append(f + "\n")


class Cat:

    """Print the contents of a file specified by args line by line"""

    def exec(self, args, out, in_pipe):
        for a in args:
            with open(a) as f:
                out.append(f.read())


class Head:

    """
    By default writes the last 10 lines of a file to standard output,
    or an inputted number of lines with flag -n.
    """

    def _read_file(self, file, size_of_head, out):
        with open(file) as f:
            lines = f.readlines()
            for i in range(0, min(len(lines), size_of_head)):
                out.append(lines[i])

    def exec(self, args, out, in_pipe):
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

        self._read_file(file, size_of_head, out)


class Tail:

    """
    By default writes the last 10 lines of a file to standard output,
    or an inputted number of lines with flag -n.
    """

    def _read_file(self, out, file, size_of_tail):
        with open(file) as f:
            lines = f.readlines()
            no_of_lines = len(lines)
            display_length = min(no_of_lines, size_of_tail)
            for i in range(0, display_length):
                out.append(lines[no_of_lines - display_length + i])

    def exec(self, args, out, in_pipe):
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


class Clear:
    def exec(self, args, out, in_pipe):
        # Windows users -> cls
        # Mac/Linux users -> clear
        os.system("cls||clear")


class Exit:
    def exec(self, args, out, in_pipe):
        sys.exit(0)


class Uniq:
    """
    Detects and deletes adjacent duplicate lines from an input file/stdin
    and prints the result to stdout.
    USAGE:
        uniq [OPTIONS] [FILE]
    ARGS:
        [OPTIONS]
            -i = flag ignores case (case insensitive)
        [FILE] = file name, if not specified use stdin
    """

    def _uniq_lines(self, lines, case):
        """
        Return array of unique adjacent lines whilst maintaining insertion order.
        """
        if case:
            # Casefold = returns string where all characters are lowercase
            # Dictionary ensures order is maintained.
            return set({line.casefold(): line for line in lines}.values())
        uniq_lines = []
        i = 0
        while i < len(lines):
            if (i + 1) < len(lines) and lines[i] == lines[
                i + 1
            ]:  # Check if two adjacent lines are equal
                uniq_lines.append(lines[i])  # If so, only add it once
                i += 2
            else:
                uniq_lines.append(lines[i])  # If not equal then just add current line
                i += 1
        return uniq_lines

    def _read_file(self, out, file_name, case):
        with open(file_name) as f:
            lines = f.readlines()
            uniq_lines = self._uniq_lines(lines, case)
            for line in uniq_lines:
                out.append(line)

    def exec(self, args, out, in_pipe):
        num_of_args = len(args)
        if num_of_args != 1 and num_of_args != 2:
            raise ValueError("Wrong number of command line arguments")
        if num_of_args == 1:
            file_name = args[0]
            case = False
        if num_of_args == 2:
            if (
                args[0] != "<" and args[0] != "-i"
            ):  # This takes input from stdin, may be cause problems in future
                raise ValueError("Wrong flags")
            if args[0] == "-i":
                case = True
            if args[0] == "<":
                case = False
            file_name = args[1]
        self._read_file(out, file_name, case)


class Grep:
    def exec(self, args, out, in_pipe):
        if len(args) < 1:
            raise ValueError("wrong number of command line arguments")
        elif len(args) == 1 and in_pipe:
            pattern = args[0]
            lines = out.pop().split("\n")
            # print("LINES: ", lines)
            for line in lines:
                # print("LINE: ", line)
                if re.match(pattern, line):
                    out.append(line)
        else:
            pattern = args[0]
            files = args[1:]
            for file in files:
                with open(file) as f:
                    lines = f.readlines()
                    for line in lines:
                        # print(pattern, line)
                        # print(re.match(pattern, line))
                        if re.match(pattern, line):
                            if len(files) > 1:
                                out.append(f"{file}:{line}")
                            else:
                                out.append(line)

class Find:

    """
    Finds all files with the given pattern in the given directory
    as command line arguments. If no directory is given, we use the 
    current directory.
    """

    def exec(self, args, out, in_pipe):
        num_of_args = len(args)
        if num_of_args == 2:
            if args[0] != "-name":
                out.append("first argument must be '-name'")
                return
            else:
                path = "./"
                pattern = args[1]
        elif num_of_args == 3:
            if args[1] != "-name":
                out.append("second arguement must be '-name'")
                return
            else:
                path = args[0]
                pattern = args[2]
        else:
            out.append("incorrect command line arguements")
            return

        file_names = glob.iglob(path + "/**/" + pattern, recursive=True)

        for file_name in file_names:
            out.append(file_name + "\n")
            


APPLICATIONS = {
    "pwd": Pwd(),
    "cd": Cd(),
    "echo": Echo(),
    "ls": Ls(),
    "cat": Cat(),
    "head": Head(),
    "tail": Tail(),
    "grep": Grep(),
    "clear": Clear(),
    "exit": Exit(),
    "uniq": Uniq(),
    "find": Find(),
}


def save_result_to_file(file_name, result):
    f = open(file_name, "w+")
    f.write(result)
    f.close()


def execute_application(call, out, in_pipe):
    app = call.application
    args = call.args
    try:
        application = APPLICATIONS[app]
    except KeyError:
        out.append(f"Unsupported Application: {app}")
        return
    application.exec(args, out, in_pipe)
    if call.file_output:
        save_result_to_file(call.file_output, out.pop())
