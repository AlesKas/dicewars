import os
import numpy as np
import sys
from os import makedirs
from typing import Dict, Tuple, Iterable, Optional

from dicewars.server.area import Area
from dicewars.server.board import Board
from dicewars.server.player import Player

MAX_AREA_COUNT = 34
MAX_PLAYER_COUNT = 4


LOG_DIR = os.path.join(os.path.dirname(__file__), '../../data')


def game_configuration(
        board: Board,
        players: Optional[Dict[int, Player]] = None,
        biggest_regions: Optional[Dict[int, int]] = None,):
    
    assert players or biggest_regions, 'Given biggest regions directly or by players'
    assert not biggest_regions or len(biggest_regions) == MAX_PLAYER_COUNT, 'Exact count of biggest regions'

    areas: Dict[int, Area] = board.areas
    players = players or dict()

    board_state = []
    data = np.empty((MAX_AREA_COUNT * (MAX_AREA_COUNT + 1)) + 4, dtype=int)

    for column_area_id in range(1, MAX_AREA_COUNT):
        column_area = areas.get(column_area_id)

        neighbors = column_area.get_adjacent_areas_names() if column_area else {}

        board_state.extend([
            int((col_id + 1) in neighbors)
            for col_id in range(column_area_id, MAX_AREA_COUNT)
        ])

    board_state.extend([
        area.owner_name if (area := areas.get(area_id + 1)) else 0
        for area_id in range(MAX_AREA_COUNT)
    ])

    board_state.extend([
        area.dice if (area := areas.get(area_id + 1)) else 0
        for area_id in range(MAX_AREA_COUNT)
    ])

    if biggest_regions:
        board_state.extend([
            biggest_regions.get(player_id) or 0
            for player_id in range(MAX_PLAYER_COUNT)
        ])
    else:
        board_state.extend([
            p.get_largest_region(board) if (p := players.get(player_id + 1)) else 0
            for player_id in range(MAX_PLAYER_COUNT)
        ])

    data = np.array(board_state)

    return data


def save_game_configurations(winner_index, configurations):
    
    winner_dir = os.path.join(LOG_DIR, f'{winner_index}')
    makedirs(winner_dir, exist_ok=True)
    data = np.asarray(configurations)
    conf_hash = str(hash(data.tostring()))
    conf_file = os.path.join(winner_dir, conf_hash)
    np.save(f"{conf_file}.npy", data)