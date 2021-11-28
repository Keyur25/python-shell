from lark import Lark, UnexpectedCharacters, Tree
from lark.visitors import Visitor_Recursive
from pathlib import Path

class Call:
    def __init__(self, raw_command):
        self.raw_command = raw_command

class Pipe:
    def __init__(self, call1, call2): # list of Call's
        self.calls = [call1, call2]

class Parser:
    def __init__(self):
        self.command_level_parser = Lark(self._get_command_level_grammar(), start="command")
        self.call_command_parser = Lark(self._get_call_command_grammar(), start="call")

    def _get_command_level_grammar(self):
        file = open(str(Path(__file__).parent.absolute()) + "/grammars/command_level_grammar.lark", "r")
        grammar = file.read()
        file.close()
        return grammar

    def _get_call_command_grammar(self):
        file = open(str(Path(__file__).parent.absolute()) + "/grammars/call_level_grammar.lark", "r")
        grammar = file.read()
        file.close()
        return grammar

    def command_level_parse(self, input):
        try:
            return self.command_level_parser.parse(input)
        except UnexpectedCharacters:
            return False

    def call_level_parse(self, input):
        try:
            return self.call_command_parser.parse(input)
        except UnexpectedCharacters:
            return False

class QuotedExtractor(Visitor_Recursive):
    def __init__(self):
        self.extracted_quotes = ""
    
    def double_quoted(self, tree):
        if len(tree.children) > 0:
            self.extracted_quotes += ('"' + tree.children[0] + '"')
        else:
            self.extracted_quotes += ('""')
    
    def single_quoted(self, tree):
        if len(tree.children) > 0:
            self.extracted_quotes += ("'" + tree.children[0] + "'")
        else:
            self.extracted_quotes += ("''")

    def backquoted(self, tree):
        if len(tree.children) > 0:
            self.extracted_quotes += ("`" + tree.children[0] + "`")
        else:
            self.extracted_quotes += ("``")

# Visitor_Recursive is slightly faster than Visitor
class CommandTreeVisitor(Visitor_Recursive):
    def __init__(self):
        self.raw_commands = []

    def pipe(self, tree):
        lhs = self.raw_commands.pop(-2)
        rhs = self.raw_commands.pop(-1)
        if type(lhs) is Pipe: # checks for multiple pipes in a row
            lhs.calls.append(rhs)
            self.raw_commands.append(lhs)
        else:
            self.raw_commands.append(Pipe(lhs, rhs))

    def call(self, tree):
        args = ""
        for arg in tree.children:
            if type(arg) == Tree:
                quoted_extractor = QuotedExtractor()
                quoted_extractor.visit(arg)
                args += quoted_extractor.extracted_quotes
            else:
                args += arg
        self.raw_commands.append(Call((args).strip()))

def print_raw_commands(raw_commands):
    output = []
    for raw_command in raw_commands:
        if type(raw_command) is Call:
            output.append(raw_command.raw_command)
        elif type(raw_command) is Pipe:
            pipes = ["|", []]
            for call in raw_command.calls:
                pipes[1].append(call.raw_command)
            output.append(pipes)
        else:
            output.append("Raw Command Not Recognised!")
    print(f"OUTPUT: {output}\n\n")

if __name__ == "__main__":
    cmd = "echo 'hello world' | grep test '...' 'dfgdf' | cat file.txt ; wc -l `find -name '*.java'`"
    parser = Parser()
    command_level_tree = parser.command_level_parse(cmd)
    print(f"\n\nINPUT: {cmd}")
    if(command_level_tree):
        command_tree_visitor = CommandTreeVisitor()
        command_tree_visitor.visit(command_level_tree)
        raw_commands = command_tree_visitor.raw_commands
        print_raw_commands(raw_commands)
    else:
        print("Incorrect Command Level Input!")