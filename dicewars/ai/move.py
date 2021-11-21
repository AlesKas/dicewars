import logging
from typing import List, Optional

from dicewars.ai.utils import attack_succcess_probability
from dicewars.client.ai_driver import BattleCommand
from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from dicewars.ai.aliases import Command, Name

class Move:
    def __init__(self, command: Command, scores: Optional[List[float]]=None, children: List['Move']=list(), target_name: Optional[int]=None):
        self.command = command
        self.scores = scores if scores else next.scores
        self.children = children
        self.target_name = target_name

    @classmethod
    def other(cls, command, scores: Optional[List[float]]=None, next: Optional['Move']=None):
        return cls(command, scores if scores else next.scores, [next] if next else list(), None)

    @classmethod
    def attack(cls, source: Area, target: Area, player_order: int, success: 'Move', failure: 'Move', save_moves: bool):
        success_probability = attack_succcess_probability(source.get_dice(), target.get_dice())
        failure_probability = 1 - success_probability
        order = player_order
        success_score = success.scores[order]*success_probability
        fail_score = failure.scores[order]*failure_probability
        if success_score > fail_score:
            scores = [score*success_probability for score in success.scores]
        else:
            scores = [score*failure_probability for score in success.scores]
        command = BattleCommand(source.get_name(), target.get_name())
        children = [success, failure] if save_moves else list()
        return cls(command, scores, children, target.get_name())

    

    def __str__(self, level=0):
        ret = "\t"*level+repr(self)+"\n"
        for move in self.children:
            ret += move.__str__(level+1)
        return ret


    def __repr__(self):
        return f"{self.command} = {self.scores}"

    def get_child(self, board: Board, player: Name) -> Optional['Move']:
        if not self.children:
            return None
        if self.target_name:
            if board.get_area(self.target_name).get_owner_name() == player:
                return self.children[0]
            else:
                return self.children[1]
        else:
            return self.children[0]
