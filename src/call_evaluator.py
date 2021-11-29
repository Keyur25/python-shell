from glob import glob
from lark.visitors import Visitor_Recursive
from commands import Call, Pipe
from parser import Parser
from lark import Tree, Token
from applications import execute_application
from command_evaluator import extract_raw_commands



class CommandSubstituitionVisitor(Visitor_Recursive):
    def __init__(self, out):
        self.out = out

    def backquoted(self, tree):
        evaluate_command_substituition(tree.children[0], self.out)
        tree.children[0] = self.out.pop()


class QuotedVisitor(Visitor_Recursive):
    def __init__(self):
        self.extracted_quotes = ""

    def double_quoted(self, tree):
        self.extracted_quotes += tree.children[0]

    def single_quoted(self, tree):
        self.extracted_quotes += tree.children[0]

    def backquoted(self, tree):
        self.extracted_quotes += tree.children[0]


class RedirectionVisitor(Visitor_Recursive):
    def __init__(self):
        self.io_type = None
        self.file_name = ""

    def _quoted(self, tree):
        quoted_visitor = QuotedVisitor()
        quoted_visitor.visit_topdown(tree)
        self.file_name += quoted_visitor.extracted_quotes

    def argument(self, tree):
        for child in tree.children:
            if type(child) is Token:
                self.file_name += str(child)
            if type(child) is Tree:
                if child.data == "quoted":
                    self._quoted(child)

    def redirection(self, tree):
        self.io_type = str(tree.children[0])


class CallTreeVisitor(Visitor_Recursive):
    def __init__(self):
        self.application = None
        self.args = []
        self.file_output = None

    def _redirection(self, tree):
        redirection_visitor = RedirectionVisitor()
        redirection_visitor.visit_topdown(tree)
        if redirection_visitor.io_type == ">":
            self.file_output = redirection_visitor.file_name
        else:
            self.args.append(redirection_visitor.file_name)

    def _globbing(self, arg, unquoted_asterisk):
        if unquoted_asterisk:
            globbing = glob(arg)
            if globbing:
                self.args.append(" ".join(globbing))
                return
        self.args.append(arg)
        
        
    def _argument(self, tree):
        unquoted_asterisk = False
        arg = ""
        for child in tree.children:
            if type(child) is Token:
                arg += str(child)
                unquoted_asterisk = "*" in str(child)    
            if type(child) is Tree:
                if child.data == "quoted":
                    quoted_visitor = QuotedVisitor()
                    quoted_visitor.visit_topdown(tree)
                    arg += quoted_visitor.extracted_quotes
        self._globbing(arg, unquoted_asterisk)
                

    def atom(self, tree):
        for child in tree.children:
            if child.data == "redirection":
                self._redirection(child)
            if child.data == "argument":
                self._argument(child)

    def call(self, tree):
        for child in tree.children:
            if child.data == "argument":
                self.application = str(child.children[0])
            if child.data == "redirection":
                self._redirection(child)


def evaluate_command_substituition(command, out):
    parser = Parser()
    command_tree = parser.command_level_parse(command)
    if not command_tree:
        out.append(f"Unrecognized Input: {command}")
        return
    raw_commands = extract_raw_commands(command_tree)
    evaluate_raw_commands(raw_commands, out)


def evaluate_call(call: Call, out, in_pipe=False):
    parser = Parser()
    call_tree = parser.call_level_parse(call.raw_command)

    if not call_tree:
        if call.raw_command:
            out.append(f"Unrecognized Command: {call.raw_command}")
        return
    # print(call_tree.pretty())
    command_substituition_visitor = CommandSubstituitionVisitor(out)
    command_substituition_visitor.visit(call_tree)
    # print(call_tree.pretty())
    call_tree_visitor = CallTreeVisitor()
    call_tree_visitor.visit_topdown(call_tree)

    call.application = call_tree_visitor.application
    call.args = call_tree_visitor.args
    call.file_output = call_tree_visitor.file_output

    execute_application(call, out, in_pipe)


def evaluate_pipe(pipe: Pipe, out):
    first_call = True
    for call in pipe:
        if first_call:
            evaluate_call(call, out)
            first_call = False
        else:
            evaluate_call(call, out, True)


def evaluate_raw_commands(raw_commands, out):
    for raw_command in raw_commands:
        command_type = type(raw_command)
        if command_type is Call:
            evaluate_call(raw_command, out)
        elif command_type is Pipe:
            evaluate_pipe(raw_command, out)
