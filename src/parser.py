from lark import Lark, tree, UnexpectedCharacters, Tree
from lark.visitors import Visitor_Recursive


class Parser:
    def __init__(self):
        self.command_level_parser = Lark(
            self._get_command_level_grammar(), start="command"
        )
        self.call_command_parser = Lark(self._get_call_command_grammar(), start="call")

    def _get_command_level_grammar(self):
        file = open("src/grammars/command_level_grammar.lark", "r")
        grammar = file.read()
        file.close()
        return grammar

    def _get_call_command_grammar(self):
        file = open("src/grammars/command_level_grammar.lark", "r")
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


# Can also used Visitor_Recursive
# Slightly faster than the non-recursive one
class CommandTreeVisitor(Visitor_Recursive):
    def __init__(self):
        self.res = []

    def pipe(self, tree):
        # print(f"List at pipe: {self.res}")
        self.res.append(["|", (self.res.pop(-2), self.res.pop(-1))])

    def call(self, tree):
        args = ""
        for arg in tree.children:
            if type(arg) == Tree:
                for subtree in arg.children:
                    if subtree.data == "single_quoted":
                        if len(subtree.children) > 0:
                            args += "'" + subtree.children[0] + "'"
                        else:
                            args += "''"
                    elif subtree.data == "double_quoted":
                        if len(subtree.children) > 0:
                            args += '"' + subtree.children[0] + '"'
                        else:
                            args += '""'
            else:
                args += arg

        # print(f"List before call append: {self.res}")
        self.res.append((args).strip())


if __name__ == "__main__":
    # Initialise grammar
    cmd = "cat dir1/file1.txt dir1/file2.txt | grep '...'"
    parser = Parser()
    command_level_tree = parser.command_level_parse(cmd)

    if command_level_tree:
        t = CommandTreeVisitor()
        t.visit(command_level_tree)
    else:
        print("Incorrect command level input")
    print(f"\n\n  INPUT: {cmd}")
    print(f" OUTPUT: {t.res}\n\n")
