from .xberez03_NN import AI as NEW_AI
from dicewars.client.game.board import Board
from typing import List
from dicewars.ai.aliases import Name
import random

class AI(NEW_AI):

    def leaf_heuristic(self, board: Board, current_player: Name, players_order: List[Name], end_turn_gain: int):
        h = [0 for _ in players_order]
        for index, player in enumerate(players_order):

            h[index] = board.get_player_dice(player)
            h[index] += len(board.get_player_areas(player) * 4)

            players_regions = board.get_players_regions(player)
            players_regions_sizes = []
            for region in players_regions:
                region_size = len(region)
                players_regions_sizes.append(region_size)

            h[index] += (max(players_regions_sizes) * 8)

        return h
        