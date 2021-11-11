import logging

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand, TransferCommand
from dicewars.server.board import Board
from dicewars.ai.maxn import MaxN

class AI:
    def __init__(self, player_name, board, players_order, max_transfers):
        self.player_name = player_name
        self.logger = logging.getLogger('AI')

        self.search = MaxN(player_name, board, players_order, leaf_heuristic)


    def ai_turn(self, board: Board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        return self.search.simulate(board, 4)


def leaf_heuristic(board: Board, player_name):
    return sum(area.get_dice() for area in board.get_player_areas(player_name))

        