from os import getcwd, listdir, path
import readline
APPLICATIONS = {
    "pwd":"",
    "cd":"",
    "echo":"",
    "ls":"",
    "cat":"",
    "head":"-n",
    "tail":"-n",
    "grep":"",
    "clear":"",
    "exit":"",
    "uniq":"-i",
    "find":"",
    "sort":"-r",
    "cut":"-b",
}

class Completer(object):  # Custom completer
    def __init__(self, options):
        self.options = sorted(options)
        self.matches = None

    def set_options(self, opt):
        self.options = sorted(opt)

    def completes(self, text, state):
        if state == 0:  # on first trigger, build possible matches
            if text:  # cache matches (entries that start with entered text)
                self.matches = [o for o in self.options if o and o.startswith(text)]
            else:  # no text entered, all matches possible
                self.matches = self.options[:]
        # return match indexed by state
        try:
            return self.matches[state]
        except IndexError:
            return None

    def check(self, text, state):
        current = readline.get_line_buffer()
        t = current.split(" ")
        if len(t) == 1:
            self.options = APPLICATIONS.keys()
            return self.completes(text, state)
        else:
            if t[-1] == '-':
                params = APPLICATIONS.get(t[-2])
                self.options = [params]
                return self.completes(text, state)[1:]
            else:
                opts = []
                ls_dir = getcwd()
                if '/' in t[-1]:
                    if t[-1][-1] == '/':
                        ls_dir += '/' + t[-1]
                    else:
                        ls_dir += '/' + t[-1][:t[-1].rindex('/')]
                
                for f in listdir(ls_dir):
                    if not f.startswith(".") and not f.startswith("__"):
                        opts.append(f)
                self.set_options(opts)
                ret = self.completes(text, state)
                if path.isdir(ls_dir + '/' + ret + '/'):
                    return ret + '/'
                return ret
        return None

completer = Completer(APPLICATIONS.keys())
readline.set_completer(completer.check)
readline.parse_and_bind('tab: complete')
readline.redisplay()
