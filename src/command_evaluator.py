from lark import Tree
from lark.visitors import Visitor_Recursive
from commands import Call, Pipe


class QuotedExtractor(Visitor_Recursive):
    def __init__(self):
        self.extracted_quotes = ""

    # why can't all of these just do self.extracted_quotes += quote + tree.children[0] + quote

    def double_quoted(self, tree):
        if len(tree.children) > 0:
            self.extracted_quotes += '"' + tree.children[0] + '"'
        else:
            self.extracted_quotes += '""'

    def single_quoted(self, tree):
        if len(tree.children) > 0:
            self.extracted_quotes += "'" + tree.children[0] + "'"
        else:
            self.extracted_quotes += "''"

    def backquoted(self, tree):
        if len(tree.children) > 0:
            self.extracted_quotes += "`" + tree.children[0] + "`"
        else:
            self.extracted_quotes += "``"


# Visitor_Recursive is slightly faster than Visitor
class CommandTreeVisitor(Visitor_Recursive):
    def __init__(self):
        self.raw_commands = []

    def pipe(self, tree):
        lhs = self.raw_commands.pop(-2)
        rhs = self.raw_commands.pop(-1)
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


def extract_raw_commands(command_tree):
    command_tree_visitor = CommandTreeVisitor()
    command_tree_visitor.visit(command_tree)
    return command_tree_visitor.raw_commands