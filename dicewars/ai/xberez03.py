import logging

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand, TransferCommand
from dicewars.client.game.board import Board
from dicewars.ai.maxn import MaxN

class AI:
    def __init__(self, player_name, board, players_order, max_transfers):
        self.player_name = player_name
        self.logger = logging.getLogger('AI')

        self.search = MaxN(player_name, players_order, leaf_heuristic)


    def ai_turn(self, board: Board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        logging.info(f"Move: {nb_moves_this_turn}")
        if nb_moves_this_turn == 0:
            self.search.simulate(board, 2)

        return self.search.command()


def leaf_heuristic(board: Board, player_name):
    return board.get_player_dice(player_name)

        