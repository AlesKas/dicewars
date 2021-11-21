import logging
from typing import List, Tuple, Set
from dicewars.ai.utils import probability_of_holding_area, save_state

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand, TransferCommand
from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from dicewars.ai.maxn import MaxN
from dicewars.ai.aliases import Name

class AI:
    def __init__(self, player_name, board, players_order, max_transfers):
        self.player_name = player_name
        self.logger = logging.getLogger('AI')

        self.search = MaxN(player_name, players_order, 1, leaf_heuristic, transfer_heuristic, attack_heuristic)
        with open('debug.save', 'wb') as f:
                save_state(f, board, self.player_name, self.search.players_order)


    def ai_turn(self, board: Board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        logging.info(f"Move: {nb_moves_this_turn + nb_transfers_this_turn}")
        #return EndTurnCommand()
        if nb_moves_this_turn + nb_transfers_this_turn == 0:
            with open('debug.save', 'wb') as f:
                save_state(f, board, self.player_name, self.search.players_order)
            command = self.search.simulate(board, 1)
        else:
            command = self.search.command(board)
        return command



def leaf_heuristic(board: Board, player_name: Name, end_turn_gain: int) -> float:
    #return end_turn_gain
    border = board.get_player_border(player_name)
    return calculate_ring_value(board, player_name, border)*end_turn_gain

    
def calculate_ring_value(board: Board, player_name, ring: List[Area], already_counted: Set[int]=set(), multiplier: float=1.0) -> float:
    inland_devaluation_constant = 0.8
    if not ring:
        return 0.0

    already_counted.update({area.get_name() for area in ring})
    new_ring = set()
    ring_sum = 0
    for area in ring:
        adjacents = {board.get_area(adjacent) for adjacent in area.get_adjacent_areas_names() if adjacent not in already_counted}
        owned_adjacents = {area for area in adjacents if area.get_owner_name() == player_name}
        new_ring.update(owned_adjacents)
        hold_probability = probability_of_holding_area(board, area.get_name(), area.get_dice(), area.get_owner_name())
        ring_sum += area.get_dice() * (1.0 + (hold_probability if hold_probability >= 1.0 else 0))

    return ring_sum*multiplier + calculate_ring_value(board, player_name, new_ring, already_counted, multiplier*inland_devaluation_constant) 



def transfer_heuristic(board: Board, transfer: Tuple[Area, Area], transfers_done: List[Tuple[Area, Area]]) -> bool:
    #return True
    back_transfer = (transfer[1], transfer[0])
    if transfers_done:
        out =  back_transfer not in transfers_done and transfer != transfers_done[-1]
        if not out:
            pass#logging.debug(f"{back_transfer} not in {transfers_done} and {transfer} != {transfers_done[-1]}")
        return out
    else:
        return True


def attack_heuristic(board: Board, player_name: Name,  attack: Tuple[Area, Area]) -> bool:
    from_area: Area = attack[0]
    to_area: Area = attack[1]   
    #is_probable: bool = probability_of_successful_attack(board, from_area.get_name(), to_area.get_name()) > 0.5 or from_area.get_dice() >= 8
    is_probable: bool = from_area.get_dice() > to_area.get_dice() or (from_area.get_dice() == to_area.get_dice() and from_area.get_dice() >= 4)
    is_relevant: bool = from_area.get_owner_name() == player_name or to_area.get_owner_name() == player_name
    return is_probable and is_relevant
        