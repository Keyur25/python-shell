from commands import Call, Pipe, Seq
import unittest
from collections import deque
class TestCommands(unittest.TestCase):

    def setUp(self):
        self.out = deque()

    def test_call(self):
        call = Call("echo foo")
        call.eval(self.out)
        self.assertEquals(call.application, "echo")
        self.assertEquals(len(call.args), 1)
        self.assertEquals(call.args[0], "foo")
        self.assertEquals(self.out.pop().strip(), "foo")
    
    def test_invalid_call(self):
        call = Call("echo AAA >> file.txt")
        call.eval(self.out)
        self.assertEquals(self.out.pop(), "Unrecognized Command: echo AAA >> file.txt")
    
    def test_empty_call(self):
        call = Call("")
        call.eval(self.out)
        self.assertEquals(len(self.out), 0)

    def test_empty_application(self):
        call = Call("'' foo")
        call.eval(self.out)
        self.assertEquals(len(self.out), 0)
        self.assertEquals(call.application, "")

    def test_pipe(self):
        pipe = Pipe(Call("echo abc"), Call("cut -b 1"))
        pipe.eval(self.out)
        self.assertEquals(len(self.out), 1)
        self.assertEquals(self.out.pop().strip(), "a")
    
    def test_nested_pipe(self):
        pipe = Pipe(Pipe(Call("echo abc"), Call("cut -b -1,2-")), Call("cut -b 1"))
        pipe.eval(self.out)
        self.assertEquals(len(self.out), 1)
        self.assertEquals(self.out.pop().strip(), "a") 

    def test_seq(self):
        seq = Seq([Call("echo foo"), Call("echo bar")])
        seq.eval(self.out)
        self.assertEquals(len(self.out), 2)
        self.assertEquals(self.out.pop().strip(), "bar")
        self.assertEquals(self.out.pop().strip(), "foo")