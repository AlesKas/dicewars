from .xberez03_NN import AI as NEW_AI
from dicewars.client.game.board import Board
from typing import List
from dicewars.ai.aliases import Name
import random

class AI(NEW_AI):

    def leaf_heuristic(self, board: Board, current_player: Name, players_order: List[Name], end_turn_gain: int):
        h = [8 for _ in players_order]
        for index, player in enumerate(players_order):
            if player == current_player:
                h[index] = 0
            else:
                for area in board.get_player_border(player):
                    for neighbor_area in area.get_adjacent_areas_names():
                        if current_player == board.get_area(neighbor_area).get_owner_name():
                            h[index] += 1
            h[index] -= (board.get_player_dice(player) / 8)
            h[index] -= (len(board.get_player_areas(player)) / 4)
        return h