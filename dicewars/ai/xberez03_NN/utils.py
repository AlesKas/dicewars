import numpy as np
from typing import Dict, Optional

from dicewars.server.area import Area
from dicewars.server.board import Board
from dicewars.server.player import Player

MAX_AREA_COUNT = 34
MAX_PLAYER_COUNT = 4

def game_configuration(
        board: Board,
        players: Optional[Dict[int, Player]] = None,
        biggest_regions: Optional[Dict[int, int]] = None,):
    
    assert players or biggest_regions
    assert not biggest_regions or len(biggest_regions) == MAX_PLAYER_COUNT

    areas: Dict[int, Area] = board.areas
    players = players or dict()

    board_state = []
    data = np.empty((MAX_AREA_COUNT * (MAX_AREA_COUNT + 1)) + 4, dtype=int)

    for column_area_id in range(1, MAX_AREA_COUNT):
        column_area = areas.get(column_area_id)

        neighbors = column_area.get_adjacent_areas_names() if column_area else {}

        for col_id in range(column_area_id, MAX_AREA_COUNT):
            if int(col_id + 1) in neighbors:
                board_state.append(int(1))
            else:
                board_state.append(int(0))

    for area_id in range(MAX_AREA_COUNT):
        area = areas.get(area_id + 1)
        if area is not None:
            board_state.append(area.owner_name)
        else:
            board_state.append(int(0))

    for area_id in range(MAX_AREA_COUNT):
        area = areas.get(area_id + 1)
        if area is not None:
            board_state.append(area.dice)
        else:
            board_state.append(int(0))

    if biggest_regions:
        board_state.extend([
            biggest_regions.get(player_id) or 0
            for player_id in range(MAX_PLAYER_COUNT)
        ])
    else:
        for player_id in range(MAX_PLAYER_COUNT):
            p = players.get(player_id + 1)
            if p is not None:
                board_state.append(p.get_largest_region(board))
            else:
                board_state.append(0)

    data = np.array(board_state)

    return data