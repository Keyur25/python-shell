""" OS Module used to get paths """
from os import getcwd, listdir, path
import readline

APPLICATIONS = {
    "pwd": "",
    "cd": "",
    "echo": "",
    "ls": "",
    "cat": "",
    "head": "-n",
    "tail": "-n",
    "grep": "",
    "clear": "",
    "exit": "",
    "uniq": "-i",
    "find": "",
    "sort": "-r",
    "cut": "-b",
}


class Completer:  # Custom completer
    """
    Auto completer class
    """

    def __init__(self, options):
        self.options = sorted(options)  # List of items to check against
        self.matches = None  # List of matched strings (if duplicate)

    def set_options(self, opt):
        """
        Sets the list of items to filter against
        """
        self.options = sorted(opt)

    def completes(self, text, state):
        """
        Referenced from: https://bit.ly/3ICwH1b
        By users: @Shaw Chin and @chiffa
        """
        if state == 0:  # on first trigger, build possible matches
            if text:  # cache matches (entries that start with entered text)
                self.matches = [o for o in self.options
                                if o and o.startswith(text)]
            else:  # no text entered, all matches possible
                self.matches = self.options[:]
        # return match indexed by state
        try:
            return self.matches[state]
        except IndexError:
            return None

    def set_options_to_files_and_folders(self, ls_dir):
        """
        Sets the options to all the files and folders
        that do not start with . and __
        """
        opts = []
        for file in listdir(ls_dir):
            if not file.startswith(".") and not file.startswith("__"):
                opts.append(file)
        self.set_options(opts)

    def autocomplete_application(self, text, state):
        self.options = APPLICATIONS.keys()
        return self.completes(text, state)

    def autocomplete_flag(self, current_text, text, state):
        params = APPLICATIONS.get(current_text[-2])
        self.options = [params]
        res = self.completes(text, state)
        if res:
            return res[1:]

    def autocomplete_files_and_folders(self, current_text, text, state):
        ls_dir = getcwd()
        if "/" in current_text[-1]:
            ls_dir += "/" + current_text[-1][: current_text[-1].rindex("/")]
        self.set_options_to_files_and_folders(ls_dir)
        res = self.completes(text, state)
        # If autocomplete text is path add a '/' to distinguish
        if res is not None and path.isdir(ls_dir + "/" + res + "/"):
            return res + "/"
        return res

    def check(self, text, state, current=None):
        """
        Main function to check what the type of the current text is
        in the order: application, flag, directory.
        Then returns filtered result and prints to terminal
        """

        if current is None:
            current = readline.get_line_buffer()
        current_text = current.split(" ")
        if len(current_text) == 1 or current_text[-2] in ["|", ";", "`"]:
            return self.autocomplete_application(text, state)
        elif current_text[-1] == "-":  # It is a flag argument
            return self.autocomplete_flag(current_text, text, state)
        else:
            return self.autocomplete_files_and_folders(current_text,
                                                       text, state)


# Initialise the options to applications domain at first run.

def autocomplete():
    completer = Completer(APPLICATIONS.keys())
    readline.set_completer(completer.check)
    readline.parse_and_bind("tab: complete")
    readline.redisplay()
