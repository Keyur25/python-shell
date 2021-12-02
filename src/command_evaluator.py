from lark import Tree
from lark.lexer import Token
from lark.visitors import Visitor_Recursive
from commands import Call, Pipe, Seq
from parser import Parser

class CommandTreeVisitor(Visitor_Recursive):
    def __init__(self):
        self.raw_commands = []

    def pipe(self, tree):
        lhs = self.raw_commands.pop(-2)
        rhs = self.raw_commands.pop(-1)
        self.raw_commands.append(Pipe(lhs, rhs))
    
    def _extract_quoted_content(self, node, quote: str):
        if len(node.children) > 0:
            return quote + node.children[0] + quote
        else:
            return  quote+quote

    def _double_quoted(self, tree):
        double_quoted_args = '"'
        for child in tree.children:
            if(type(child) is Token):
                double_quoted_args+=str(child)
            else: # backquoted
                double_quoted_args += self._extract_quoted_content(child, "`")
        return double_quoted_args + '"'


    def _quoted(self, tree):
        quoted_args = ""
        for child in tree.children:
            if(child.data == "double_quoted"):
                quoted_args += self._double_quoted(child)
            elif(child.data == "single_quoted"):
                quoted_args += self._extract_quoted_content(child, "'")
            elif(child.data == "backquoted"):
                quoted_args += self._extract_quoted_content(child, "`")
        return quoted_args
                
    def call(self, tree):
        args = ""
        for child in tree.children:
            if (type(child) == Tree) and child.data == "quoted":
                args += self._quoted(child)
            else:
                args += str(child)
        self.raw_commands.append(Call((args).strip()))

def extract_raw_commands(command_tree):
    command_tree_visitor = CommandTreeVisitor()
    command_tree_visitor.visit(command_tree)
    return command_tree_visitor.raw_commands

def eval_command_substituition(command, out):
    parser = Parser()
    command_tree = parser.command_level_parse(command)
    if not command_tree:
        out.append(f"Unrecognized Input: {command}")
        return
    raw_commands = extract_raw_commands(command_tree)
    seq = Seq(raw_commands)
    seq.eval(out)
    return len(raw_commands)