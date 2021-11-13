import logging
from typing import List, Optional

from dicewars.ai.aliases import Command

class Move:
    def __init__(self, command: Command, scores: Optional[List[int]]=None, next: Optional['Move']=None):
        self.command = command
        self.scores = scores if scores else next.scores
        self.next = next

    def __str__(self):
        ret = repr(self) + " -> " + self.next.__str__()
        return ret

    def __repr__(self):
        return f"{self.command} = {self.scores}"