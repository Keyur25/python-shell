from lark import Tree
from lark.lexer import Token
from lark.visitors import Visitor_Recursive
from commands import Call, Pipe, Seq
from parser import Parser

class CommandTreeVisitor(Visitor_Recursive):
    """
    Visits a command tree generated by the command grammar
    and extracts each raw command and what they are seperated by
    e.g.
    echo "foo"; echo bar | echo -> [Call, Pipe]
                                    where -> Call.raw_command = echo "foo"
                                             Pipe.lhs = echo bar
                                             Pipe.rhs = echo
    """

    def __init__(self):
        self.raw_commands = []

    def pipe(self, tree):
        lhs = self.raw_commands.pop(-2)
        rhs = self.raw_commands.pop(-1)
        self.raw_commands.append(Pipe(lhs, rhs))
    
    def _extract_quoted_content(self, node, quote: str):
        """
        extracts the content of a quote-node, aswell
        as what quote it is bound by.
        e.g. (Tree("double_quoted" [(Token, 'foo')])) -> "foo" 
        """
        if len(node.children) > 0:
            return quote + node.children[0] + quote
        else:
            return  quote+quote

    def _double_quoted(self, tree):
        """
        extracts the content of a double quoted node,
        aswell as nested backquotes.
        """
        double_quoted_args = '"'
        for child in tree.children:
            if(type(child) is Token):
                double_quoted_args+=str(child)
            else: # backquoted
                double_quoted_args += self._extract_quoted_content(child, "`")
        return double_quoted_args + '"'


    def _quoted(self, tree):
        """
        Extracts the contents of a qouted node, including
        what quotes the content is bound by.
        """
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
        """
        iterates over the children of a call node
        extracting the contents, including what is
        bound by quotes.
        """
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
    