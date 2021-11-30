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
        lines = []
        for a in args:
            with open(a) as f:
                lines.append(f.read())
        out.append("".join(lines))

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

    def _uniq_lines(self, out, lines, case_insensitive):
        """
        Print unique adjacent lines to stdout whilst maintaining insertion order.
        """
        #print(f"LINES TO TEST = {lines}, Case={case}")
        i = 0
        uniq_lines = []
        while i < len(lines):
            if case_insensitive and len(uniq_lines) > 0 and lines[i].lower() == uniq_lines[-1].lower(): # Check if current and previous lines are equal (case-insensitive)
                pass # If so, only add it once
            elif len(uniq_lines) > 0 and lines[i] == uniq_lines[-1]:  # Check if current and previous lines are equal 
                pass # If so, only add it once
            else:
                uniq_lines.append(lines[i])  # If not equal then just add current line
            i += 1
        out.append("".join(uniq_lines))
        
    def _read_file(self, out, file_name, case_insensitive):
        with open(file_name) as file:
            lines = file.readlines()
        file.close()
        self._uniq_lines(out, lines, case_insensitive)

    def exec(self, args, out, in_pipe):
        num_of_args = len(args)
        if in_pipe:
            lines = out.pop().splitlines(keepends=True)
            self._uniq_lines(out, lines, num_of_args == 1 and args[0] == '-i')
            return
        if num_of_args != 1 and num_of_args != 2:
            out.append("Wrong number of command line arguments")
            return
        case_insensitive = num_of_args == 2
        if not case_insensitive:
            file_name = args[0]
        else:
            if (args[0] != "-i"):  # Case insensitive flag.
                out.append("Wrong flags")
                return
            file_name = args[1]
        self._read_file(out, file_name, case_insensitive)

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


class Sort:
    """
    Sorts the contents of a file/stdin line by line and prints the result to stdout.

    sort [OPTIONS] [FILE]

    - `OPTIONS`:
        - `-r` sorts lines in reverse order
    - `FILE` is the name of the file. If not specified, uses stdin.
    """
    def _sort_contents(self, contents, out, reverse=False):
        if contents:
            contents.sort(reverse=reverse)
            # contents.remove("\n") # validate so only try to remove if new line is actually in the list
            out.append("".join(contents))

    def _read_file(self, file_name, out):
        try:
            with open(file_name) as f:
                return f.readlines()
        except FileNotFoundError:
            out.append(f"File Not Found: {file_name}")
            return None

    def _input_from_stdin(self, out):
        try:
            result = out.pop()
            if type(result) is list:
                return result
            elif type(result) is str:
                return result.splitlines(keepends=True)
            else:
                raise TypeError()
        except IndexError:
            out.append("No Input Specified - find")
            return None
        except TypeError:
            out.append("Unknown Stdin Input - find")
            return None

    def exec(self, args, out, in_pipe):
        num_of_args = len(args)
        if num_of_args == 0:
            contents_of_input = self._input_from_stdin(out)
            self._sort_contents(contents_of_input, out)
        elif args[0] == "-r":
            if num_of_args == 1:
                contents_of_input = self._input_from_stdin(out)
                self._sort_contents(contents_of_input, out, True)
            elif num_of_args == 2:
                file_name = args[1]
                contents_of_input = self._read_file(file_name, out)
                self._sort_contents(contents_of_input, out, True)
            else:
                out.append("Invalid Arguments - find")
        elif num_of_args == 1:
            file_name = args[0]
            contents_of_input = self._read_file(file_name, out)
            self._sort_contents(contents_of_input, out)
        else:
            out.append("Invalid Arguments - find")

class Cut:
    """
    Cuts out sections from each line of given file or stdin
    and prints result to stdout.
    USAGE:
        cut [OPTIONS] [FILE]
    ARGS:
        [OPTIONS]
            -b = specifies bytes to extract from EACH line
        [FILE] = file name, if not specified use stdin
    """
    
    def _get_section(self, no_of_bytes_param, line) -> str:
        """
        Returns the extracted section from given line.
        """
        result = ""
        for param in no_of_bytes_param:
            if len(param) == 1 and int(param) <= len(line): # Single byte arg. e.g. -b n
                if int(param) == 1:
                    result += line[0]
                else:
                    result += (line[int(param)])
            elif len(param) == 2:
                # -b -n (from first byte to nth byte) or -b n- (from nth byte to last byte) 
                if param[0] == '-': # Case -b -n
                    result += (line[:int(param[1])])
                elif param[1] == '-': # Case -b n-
                    result += (str(line[int(param[0])-1:]))
                    break
            elif len(param) == 3:
                # -b n-m (from nth byte to mth byte)
                result += (line[int(param[0])-1:int(param[2])])
        return result
    

    def exec(self, args, out, in_pipe):
        try:
            no_of_bytes_param = args[1].split(",")
            no_of_bytes_param.sort()
            file_name = args[2]
        except:
            out.append("Wrong number of arguments")
            return
        
        with open(file_name) as file:
            line = file.readline().strip()
            result = ""
            while line:
                result += self._get_section(no_of_bytes_param, line)
                line = file.readline().strip()
                result += "\n"
            out.append(result[:-1])


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
    "sort": Sort(),
    "cut": Cut(),
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
