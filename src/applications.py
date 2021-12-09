import os
import re
import sys
import glob
from os import listdir
from application_interface import Application


class ApplicationExcecutionError(Exception):

    """raised when an application cannot be executed"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class Pwd(Application):

    """outputs current working directory"""

    def exec(self, args, out, in_pipe):
        if args:
            raise ApplicationExcecutionError("Pwd Takes No Arguments")
        out.append(os.getcwd() + "\n")


class Cd(Application):

    """change the current working directory to the first argument"""

    def exec(self, args, out, in_pipe):
        if len(args) != 1:
            raise ApplicationExcecutionError("Invalid Arguments")
        os.chdir(args[0])


class Ls(Application):

    """lists the contents of a directory"""

    def _get_directory(self, args):
        if len(args) == 0:
            return os.getcwd()
        elif len(args) == 1:
            return args[0]
        else:
            raise ApplicationExcecutionError("Invalid Arguments")

    def exec(self, args, out, in_pipe):
        ls_dir = self._get_directory(args)
        contents = []
        for f in listdir(ls_dir):
            if not f.startswith("."):  # if f is hidden then we do not want to list it
                contents.append(f)
        out.append("\n".join(contents) + "\n")


class Cat(Application):

    """concatenates the content of given files"""

    def exec(self, args, out, in_pipe):
        if not args:
            if not in_pipe:
                raise ApplicationExcecutionError("Invalid Arguments")
            args = out.pop().split(" ")  # get input from stdin
        lines = []
        for a in args:
            with open(a.strip()) as f:
                lines.append(f.read())
        out.append("".join(lines))


class Echo(Application):

    """prints its arguments separated by spaces"""

    def exec(self, args, out, in_pipe):
        out.append(" ".join(args) + "\n")


class Head(Application):

    """prints the first n (10 if n is not specified) lines of a given file or stdin"""

    def _read_first_n_lines_from_file(self, file, n, out):
        with open(file) as f:
            lines = f.readlines()
            content = []
            for i in range(0, min(len(lines), n)):
                content.append(lines[i])
            out.append("".join(content))

    def exec(self, args, out, in_pipe):
        no_of_args = len(args)
        if no_of_args == 0 and in_pipe:  # get input from stdin
            self._read_first_n_lines_from_file(out.pop(), 10, out)
        elif no_of_args == 1:  # default case
            self._read_first_n_lines_from_file(args[0], 10, out)
        elif (
            no_of_args == 3
            and args[0] == "-n"
            and args[1].isnumeric()
            and int(args[1]) >= 0
        ):
            self._read_first_n_lines_from_file(args[2], int(args[1]), out)
        else:
            raise ApplicationExcecutionError("Invalid Arguments")


class Tail(Application):

    """prints the last n (10 if n is not specified) lines of a given file or stdin"""

    def _read_last_n_lines_from_file(self, file, n, out):
        with open(file) as f:
            lines = f.readlines()
            no_of_lines = len(lines)
            display_length = min(no_of_lines, n)
            content = []
            for i in range(0, display_length):
                content.append(lines[no_of_lines - display_length + i])
            out.append("".join(content))

    def exec(self, args, out, in_pipe):
        no_of_args = len(args)
        if no_of_args == 0 and in_pipe:  # get input from stdin
            self._read_last_n_lines_from_file(out.pop(), 10, out)
        elif no_of_args == 1:  # default case
            self._read_last_n_lines_from_file(args[0], 10, out)
        elif (
            no_of_args == 3
            and args[0] == "-n"
            and args[1].isnumeric()
            and int(args[1]) >= 0
        ):
            self._read_last_n_lines_from_file(args[2], int(args[1]), out)
        else:
            raise ApplicationExcecutionError("Invalid Arguments")


class Grep(Application):

    """searches for lines containing a match to the specified pattern"""

    def _find_matches_from_stdin(self, pattern, lines, out):
        contents = []
        for line in lines:
            if re.match(pattern, line):
                contents.append(line)
        out.append("\n".join(contents))

    def _find_matches_from_files(self, pattern, files, out):
        multiple_files = len(files) > 1
        contents = []
        for file in files:
            with open(file) as f:
                lines = f.readlines()
                self._grep(pattern, multiple_files, contents, file, lines)
        out.append("\n".join(contents))

    def _grep(self, pattern, multiple_files, contents, file, lines):
        for line in lines:
            line = line.replace("\n", "")
            if re.match(pattern, line):
                if multiple_files:
                    contents.append(f"{file}:{line}")
                else:
                    contents.append(line)

    def exec(self, args, out, in_pipe):
        if len(args) < 1:
            raise ApplicationExcecutionError("Invalid Arguments")
        elif len(args) == 1:
            if not in_pipe:
                raise ApplicationExcecutionError("Invalid Arguments")
            self._find_matches_from_stdin(args[0], out.pop().split("\n"), out)
        else:
            self._find_matches_from_files(args[0], args[1:], out)


class Cut(Application):
    """
    Cuts out sections from each line of a given file or stdin and prints the result to stdout.

    cut OPTIONS [FILE]

    - `OPTION` specifies the bytes to extract from each line:
        - `-b 1,2,3` extracts 1st, 2nd and 3rd bytes.
        - `-b 1-3,5-7` extracts the bytes from 1st to 3rd and from 5th to 7th.
        - `-b -3,5-` extracts the bytes from the beginning of line to 3rd, and from 5th to the end of line.
    - `FILE` is the name of the file. If not specified, uses stdin.
    """

    def _get_section(self, no_of_bytes_param, line):
        """
        Returns the extracted section from given line.
        """
        result = ""
        for param in no_of_bytes_param:
            param_section = [p for p in re.split("(-)", param) if p != '']
            if len(param_section) == 1 and int(param_section[0]) <= len(
                line
            ):  # Single byte arg. e.g. -b n
                result += self._single_param(line, param_section[0])
            elif len(param_section) == 2:
                # -b -n (from first byte to nth byte) or -b n- (from nth byte to last byte)
                if param_section[0] == "-":  # Case -b -n
                    result += line[: int(param_section[1])]
                elif param_section[1] == "-":  # Case -b n-
                    result += str(line[int(param_section[0]) - 1 :])
                    break
            elif len(param_section) == 3 and param_section[1] == "-":
                # -b n-m (from nth byte to mth byte)
                result += line[int(param_section[0]) - 1 : int(param_section[2])]
        return result

    def _single_param(self, line, param):
        if int(param) == 1:
            return line[0]
        return line[int(param)]

    def _calculate(self, no_of_bytes_param, lines):
        """
        Returns the result to print to stdout.
        """
        result = ""
        for line in lines:
            result += self._get_section(no_of_bytes_param, line.strip()) + "\n"
        return result[:-1]
    
    def exec(self, args, out, in_pipe):
        no_of_bytes_param = args[1].split(",")
        no_of_bytes_param.sort(key=lambda x : int(x.split('-')[0]) if x.split('-')[0] != '' else -ord(x[0]))
        if len(args) == 2:
            if not in_pipe:
                raise ApplicationExcecutionError("Invalid Arguments")
            args = out.pop()  # get input from stdin
            lines = args.splitlines(keepends=False)
        else:
            file_name = args[2]
            with open(file_name) as file:
                lines = file.readlines()
        out.append(self._calculate(no_of_bytes_param, lines))


class Find(Application):

    """
    Finds all files with the given pattern in the given directory
    as command line arguments. If no directory is given, we use the
    current directory.
    """

    def _get_path_and_pattern(self, args):
        num_of_args = len(args)
        if num_of_args == 2 and args[0] == "-name":
            return "./", args[1]
        elif num_of_args == 3 and args[1] == "-name":
            return args[0], args[2]
        else:
            raise ApplicationExcecutionError("Invalid Arguments")

    def exec(self, args, out, in_pipe):
        path, pattern = self._get_path_and_pattern(args)
        file_names = "\n".join(glob.iglob(path + "/**/" + pattern, recursive=True))
        out.append(file_names)


class Uniq(Application):

    """
    Detects and deletes adjacent duplicate lines from an input file/stdin
    and prints the result to stdout.

    uniq [OPTIONS] [FILE]

    - `OPTIONS`:
        - `-i` ignores case when doing comparison (case insensitive)
    - `FILE` is the name of the file. If not specified, uses stdin.
    """

    def _prev_and_current_line_equal(self, case_insensitive, line, uniq_lines):
        if case_insensitive:
            return len(uniq_lines) > 0 and line.lower() == uniq_lines[-1].lower()
        else:
            return len(uniq_lines) > 0 and line == uniq_lines[-1]

    def _uniq_lines(self, out, lines, case_insensitive):
        uniq_lines = []
        for line in lines:
            if not self._prev_and_current_line_equal(
                case_insensitive, line, uniq_lines
            ):
                uniq_lines.append(line)
        out.append("".join(uniq_lines))

    def _read_file(self, file_name):
        with open(file_name) as file:
            lines = file.readlines()
        return lines

    def _correct_no_of_args(self, num_of_args, in_pipe):
        if not in_pipe:
            return num_of_args == 1 or num_of_args == 2
        else:
            return num_of_args == 0 or num_of_args == 1

    def _correct_flags(self, no_of_args, args, in_pipe):
        if not in_pipe:
            if no_of_args == 2:
                return args[0] == "-i"
        else:
            if no_of_args == 1:
                return args[0] == "-i"
        return True

    def exec(self, args, out, in_pipe):
        num_of_args = len(args)
        case_insensitive = False
        if not self._correct_no_of_args(
            num_of_args, in_pipe
        ) or not self._correct_flags(num_of_args, args, in_pipe):
            raise ApplicationExcecutionError("Invalid Arguments")
        if len(args) > 0:
            case_insensitive = args[0] == "-i"
        if in_pipe:
            lines = out.pop().splitlines(keepends=True)
        else:
            lines = self._read_file(args[-1])
        self._uniq_lines(out, lines, case_insensitive)


class Sort(Application):
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
            out.append("".join(contents))

    def _read_file(self, file_name):
        with open(file_name) as f:
            return f.readlines()

    def _input_from_stdin(self, out):
        result = out.pop()
        if type(result) is list:
            return result
        elif type(result) is str:
            return result.splitlines(keepends=True)
        else:
            raise ApplicationExcecutionError("Unkown Type Of Stdin")

    def _reverse_options(self, args, out, num_of_args):
        if num_of_args == 1:
            contents_of_input = self._input_from_stdin(out)
        elif num_of_args == 2:
            contents_of_input = self._read_file(args[1])
        else:
            raise ApplicationExcecutionError("Invalid Arguments")
        self._sort_contents(contents_of_input, out, True)

    def exec(self, args, out, in_pipe):
        num_of_args = len(args)
        if num_of_args == 0 and in_pipe:
            contents_of_input = self._input_from_stdin(out)
            self._sort_contents(contents_of_input, out)
        elif num_of_args > 0 and args[0] == "-r":
            self._reverse_options(args, out, num_of_args)
        elif num_of_args == 1:
            file_name = args[0]
            contents_of_input = self._read_file(file_name)
            self._sort_contents(contents_of_input, out)
        else:
            raise ApplicationExcecutionError("Invalid Arguments")


class Clear(Application):

    """brings the command line to the top of the shell"""

    def exec(self, args, out, in_pipe):
        # Windows users -> cls
        # Mac/Linux users -> clear
        os.system("cls||clear")


class Exit(Application):

    """quits the shell"""

    def exec(self, args, out, in_pipe):
        sys.exit(0)


class UnsafeDecorator:
    def __init__(self, application, call):
        self.application = application
        self.call = call

    def exec(self, args, out, in_pipe):
        try:
            self.application.exec(args, out, in_pipe)
        except OSError:
            out.append(f"OS Error: {self.call.raw_command}\n")
        except ApplicationExcecutionError as e:
            out.append(f"{e.message}: {self.call.raw_command}\n")
        except IndexError:
            out.append(f"Index Error: {self.call.raw_command}\n")


def save_result_to_file(file_name, result):
    f = open(file_name, "w+")
    f.write(result)
    f.close()


def application_factory(app):
    application = {
        "pwd": Pwd,
        "cd": Cd,
        "ls": Ls,
        "cat": Cat,
        "echo": Echo,
        "head": Head,
        "tail": Tail,
        "grep": Grep,
        "cut": Cut,
        "find": Find,
        "uniq": Uniq,
        "sort": Sort,
        "clear": Clear,
        "exit": Exit,
    }
    return application[app]()


def execute_application(call, out, in_pipe):
    app = call.application
    args = call.args
    if app[0] == "_":
        try:
            app = application_factory(app[1:])
        except KeyError:
            out.append(f"Unsupported Application: {app[1:]}\n")
            return
        application = UnsafeDecorator(app, call)
    else:
        application = application_factory(app)
    application.exec(args, out, in_pipe)
    if call.file_output:
        save_result_to_file(call.file_output, out.pop())
