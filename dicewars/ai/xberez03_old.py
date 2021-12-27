from .xberez03_NN import AI
from dicewars.client.game.board import Board
from typing import List
from dicewars.ai.aliases import Name

__all__ = ['AI']

def leaf_heuristic(board: Board, players_order: List[Name], end_turn_gain: int):
    h = [-1 for _ in players_order]
    for player in players_order:
        h[player] = board.get_player_dice(player)
        regions = board.get_players_regions(player)
        regions_sizes = []
        for region in regions:
            region_size = len(region)
            h[player] += region_size
            regions_sizes.append(region_size)
    h[player] += max(regions_sizes)
    return h