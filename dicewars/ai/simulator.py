
from math import floor
from typing import List, Tuple

from dicewars.ai.aliases import Name
from dicewars.client.game.area import Area
from dicewars.client.game.board import Board


class Simulator:
    def __init__(self, player_name: Name,  players_order: List[Name]):
        self.player_name = player_name
        self.players_order = players_order
    
    def successful_attack(self, source: Area, target: Area, current_player: Name):
        source_dice = source.get_dice()
        source.set_dice(1)
        target.set_dice(source_dice - 1)
        target.set_owner(current_player)

    def failed_attack(self, source: Area, target: Area):
        source_dice = source.get_dice()
        source.set_dice(1)
        if source_dice == 8:
            dice_loss = 2
        elif source_dice >= 4:
            dice_loss = 1
        else:
            dice_loss = 0
        target.set_dice(max(target.get_dice() - dice_loss, 1))

    def transfer(self, source: Area, target: Area):
        source_dice = source.get_dice()
        target_dice = target.get_dice()
        magnitude = min(8 - target_dice, source_dice - 1)
        source.set_dice(source_dice - magnitude)
        target.set_dice(target_dice + magnitude)

    def end_turn_optimistic(self, board: Board, player: Name, reserves: List[int]):
        gain = self.calculate_end_turn_gain(board, player, reserves)
        borders = board.get_player_border(player)
        relevant_borders = [area for area in borders if self.relevant_borders_filter(board, area)]
        gain = self.evenly_complete_areas(gain, relevant_borders)
        if gain > 0:
            gain = self.fill_weakest_areas(gain, board.get_player_areas(player))
        self.set_reserve(reserves, board, player, gain)

    def end_turn_pessimistic(self, board: Board, player: Name, reserves: List[int]):
        gain = self.calculate_end_turn_gain(board, player, reserves)
        areas = board.get_player_areas(player)
        borders = board.get_player_border(player)
        mainlands = [area for area in areas if area not in borders]
        gain = self.fill_weakest_areas(gain, mainlands)
        if gain > 0:
            gain = self.evenly_complete_areas(gain, borders)
        self.set_reserve(reserves, board, player, gain)

    def save_player_areas_state(self, board: Board, player: Name) -> List[int]:
        areas = board.get_player_areas(player)
        return [area.get_dice() for area in areas]

    def restore_player_areas_state(self, board: Board, player: Name, state: List[int]):
        areas = board.get_player_areas(player)
        for area, dice in zip(areas, state):
            area.set_dice(dice)

    def save_pre_move_state(self, source: Area, target: Area) -> Tuple[Tuple[Name, int], Tuple[Name, int]]:
        return (self.save_area_state(source), self.save_area_state(target))

    def restore_pre_move_state(self, source: Area, target: Area, state: Tuple[Tuple[Name, int], Tuple[Name, int]]):
        self.restore_area_state(source, state[0])
        self.restore_area_state(target, state[1])


    def evenly_complete_areas(self, gain: int, relevant_borders: List[Area]) -> int:
        sorted_relevant_borders = sorted(relevant_borders, key=lambda area: area.get_dice())
        relevant_borders_len = len(relevant_borders)
        for index, area in enumerate(sorted_relevant_borders):
            next_area_dice = (sorted_relevant_borders[index + 1].get_dice() if index < relevant_borders_len - 1 else 8)
            areas_count = index + 1
            headroom = next_area_dice - area.get_dice()
            allocation = min(headroom*areas_count, gain)
            per_area_alocation = floor(allocation/areas_count)
            rest_allocation = allocation%areas_count
            gain -= allocation
            for area in sorted_relevant_borders[0:areas_count]:
                area_dice = area.get_dice()
                area.set_dice(area_dice + per_area_alocation)
            for area in sorted_relevant_borders[index-(rest_allocation-1):areas_count]:
                area_dice = area.get_dice()
                area.set_dice(area_dice + 1)
            if gain <= 0:
                break
        return gain

    def fill_weakest_areas(self, gain: int, areas: List[Area]) -> int: 
        for area in sorted(areas, key=lambda area: area.get_dice()):
            area_dice = area.get_dice()
            headroom = 8 - area_dice
            allocation = min(headroom, gain)
            gain -= allocation
            area.set_dice(area_dice + allocation)
            if gain <= 0:
                break
        return gain
        
    def relevant_borders_filter(self, board: Board, area: Area) -> bool:
        neighbour_names = area.get_adjacent_areas_names()
        neighbours = [board.get_area(name) for name in neighbour_names]
        return any(area.get_owner_name() == self.player_name for area in neighbours)

    def calculate_end_turn_gain(self, board: Board, player: Name, reserves: List[int]) -> int:
        unbound_gain = self.get_end_turn_dice_gain(board, player) + self.get_reserve(reserves, player)
        return min(unbound_gain, 64)

    def set_reserve(self, reserves: List[int], board: Board, player: Name, value: int):
        order = self.order_of_player(player)
        areas_count = len(board.get_player_areas(player))
        reserves[order] = min(value, abs(24 - areas_count))

    def get_reserve(self, reserves: List[int], player: Name) -> int:
        order = self.order_of_player(player)
        return reserves[order]

    def get_end_turn_dice_gain(self, board: Board, player: Name) -> int:
        regions = board.get_players_regions(player)
        return max(len(region) for region in regions)

    def save_area_state(self, area: Area) -> Tuple[Name, int]:
        return (area.get_owner_name(), area.get_dice())

    def restore_area_state(self, area: Area, state: Tuple[Name, int]):
        area.set_owner(state[0])
        area.set_dice(state[1])

    def order_of_player(self, player: Name) -> int:
        return self.players_order.index(player)