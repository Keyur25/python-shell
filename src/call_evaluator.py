from glob import glob
from lark.visitors import Visitor_Recursive
from lark import Tree, Token
from parser import Parser

class CommandSubstituitionVisitor(Visitor_Recursive):
    def __init__(self, out):
        self.out = out
    
    def _eval_command_substituition(self, command, out):
        """
        Evaluates command substitution and returns the number of outputs
        to be taken from out. e.g.

        `echo foo` -> 1
        `echo foo; echo bar' -> 2
        """
        from commands import Seq
        from command_evaluator import extract_raw_commands
        
        parser = Parser()
        command_tree = parser.command_level_parse(command)
        if not command_tree:
            out.append(f"Unrecognized Input: {command}")
            return
        raw_commands = extract_raw_commands(command_tree)
        seq = Seq(raw_commands)
        seq.eval(out)
        return len(raw_commands)

    def backquoted(self, tree):
        """
        If the call contains a backquote, we evaluate and replace the backquoted
        argument with the results in out
        """
        no_of_outputs = self._eval_command_substituition(tree.children[0], self.out)
        res = []
        for _ in range(no_of_outputs): #get correct no. of outputs from out
            res.append(self.out.pop().replace("\n", " ").strip())
        res.reverse()
        tree.children[0] = " ".join(res) # replace backquoted command with outputs


class QuotedVisitor(Visitor_Recursive):
    def __init__(self):
        self.extracted_quotes = ""

    def double_quoted(self, tree):
        if(len(tree.children) > 0):
            self.extracted_quotes += tree.children[0]

    def single_quoted(self, tree):
        if(len(tree.children) > 0):
            self.extracted_quotes += tree.children[0]

    def backquoted(self, tree):
        if(len(tree.children) > 0):
            self.extracted_quotes += tree.children[0]


class RedirectionVisitor(Visitor_Recursive):
    def __init__(self):
        self.io_type = None
        self.file_name = ""

    def _extract_quoted_content(self, node):
        if len(node.children) > 0:
            return node.children[0]
        else:
            return  ""

    def _double_quoted(self, tree):
        for child in tree.children:
            if(type(child) is Token):
                self.file_name+=str(child)
            else: # backquoted
                self.file_name += self._extract_quoted_content(child)


    def _quoted(self, tree):
        for child in tree.children:
            if(child.data == "double_quoted"):
                self._double_quoted(child)
            elif(child.data == "single_quoted" or child.data == "backquoted"):
                self._extract_quoted_content(child)

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
    
    def _extract_quoted_content(self, node):
        if len(node.children) > 0:
            return node.children[0]
        else:
            return  ""

    def _double_quoted(self, tree):
        double_quoted_args = ""
        for child in tree.children:
            if(type(child) is Token):
                double_quoted_args+=str(child)
            else: # backquoted
                double_quoted_args += self._extract_quoted_content(child)
        return double_quoted_args

    def _quoted(self, tree):
        quoted_args = ""
        for child in tree.children:
            if(child.data == "double_quoted"):
                quoted_args += self._double_quoted(child)
            elif(child.data == "single_quoted" or child.data == "backquoted"):
                quoted_args += self._extract_quoted_content(child)
        return quoted_args

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
                    arg += self._quoted(child)
        self._globbing(arg, unquoted_asterisk)
                
    def atom(self, tree):
        for child in tree.children:
            if child.data == "redirection":
                self._redirection(child)
            if child.data == "argument":
                self._argument(child)

    def _application(self, tree):
        if(type(tree.children[0]) is Token):
            self.application = str(tree.children[0])
        else: # extact application from quoted
            application = ""
            for child in tree.children:
                if type(child) is Token:
                    arg += str(child) 
                if type(child) is Tree:
                    if child.data == "quoted":
                        arg += self._quoted(child)
            self.application = application


    def call(self, tree):
        for child in tree.children:
            if child.data == "argument":
                self._application(child)
            if child.data == "redirection":
                self._redirection(child)
                