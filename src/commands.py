class Call:
    def __init__(self, raw_command):
        self.raw_command = raw_command
        self.application = None
        self.args = []
        self.file_output = None


class PipeIterator:
    def _calls(self, pipe):
        calls = []
        while type(pipe.lhs()) is Pipe:
            calls.append(pipe.rhs())
            pipe = pipe.lhs()
        calls.append(pipe.rhs())
        calls.append(pipe.lhs())
        calls.reverse()
        return calls

    def __init__(self, pipe):
        self.index = 0
        self.calls = self._calls(pipe)

    def __next__(self):
        if self.index >= len(self.calls):
            raise StopIteration
        index = self.index
        self.index += 1
        return self.calls[index]


class Pipe:
    def __init__(self, lhs, rhs):
        self.calls = (lhs, rhs)

    def lhs(self):
        return self.calls[0]

    def rhs(self):
        return self.calls[1]

    def __iter__(self):
        return PipeIterator(self)
