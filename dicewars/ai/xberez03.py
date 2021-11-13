import logging
from typing import List, Tuple

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand, TransferCommand
from dicewars.ai.utils import probability_of_successful_attack
from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from dicewars.ai.maxn import MaxN
from dicewars.ai.aliases import Name

class AI:
    def __init__(self, player_name, board, players_order, max_transfers):
        self.player_name = player_name
        self.logger = logging.getLogger('AI')

        self.search = MaxN(player_name, players_order, leaf_heuristic, attack_heuristic)


    def ai_turn(self, board: Board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        logging.info(f"Move: {nb_moves_this_turn}")
        
        if nb_moves_this_turn == 0:
            command = self.search.simulate(board, 1)
        else:
            command = self.search.command(board)
        return command



def leaf_heuristic(board: Board, player_name: Name) -> int:
    return board.get_player_dice(player_name)

def attack_heuristic(board: Board, player_name: Name,  attack: Tuple[Area, Area]) -> bool:
    from_area: Area = attack[0]
    to_area: Area = attack[1]   
    #is_probable: bool = probability_of_successful_attack(board, from_area.get_name(), to_area.get_name()) > 0.5 or from_area.get_dice() >= 8
    is_probable: bool = from_area.get_dice() > to_area.get_dice() or (from_area.get_dice() == to_area.get_dice() and from_area.get_dice() >= 4)
    is_relevant: bool = from_area.get_owner_name() == player_name or from_area.get_owner_name() == player_name
    return is_probable and is_relevant
        