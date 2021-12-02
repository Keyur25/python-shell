import re
import sys
import os
from parser import Parser
from collections import deque
from glob import glob
from applications import *
from command_evaluator import extract_raw_commands
import autocomplete
from commands import Seq

def eval(cmdline, out):
    parser = Parser()
    command_tree = parser.command_level_parse(cmdline)
    if not command_tree:
        out.append(f"Unrecognized Input: {cmdline}")
        return
    raw_commands = extract_raw_commands(command_tree)
    seq = Seq(raw_commands)
    seq.eval(out)

if __name__ == "__main__":
    args_num = len(sys.argv) - 1  # number of args excluding script name
    if args_num > 0:  # checks for correct args for non interactive mode
        if args_num != 2:
            raise ValueError("wrong number of command line arguments")
        if sys.argv[1] != "-c":
            # -c = runs the file in interactive mode
            raise ValueError(f"unexpected command line argument {sys.argv[1]}")
        out = deque()
        eval(sys.argv[2], out)
        while len(out) > 0:
            print(out.popleft(), end="")
    else:
        while True:
            cmdline = input(os.getcwd() + "> ")
            out = deque()
            eval(cmdline, out)
            while len(out) > 0:
                print(out.popleft(), end="")