from abc import ABCMeta, abstractmethod
from typing import Optional, Deque


class Command(metaclass=ABCMeta):
    """Abstract class method for Commands Call, Pipe, and Seq"""

    @classmethod
    def __subclasshook__(cls, subclass):
        return hasattr(subclass, "eval") and callable(subclass.exec)

    @abstractmethod
    def eval(self, out: Deque, in_pipe: Optional[bool] = False) -> None:
        raise NotImplementedError
