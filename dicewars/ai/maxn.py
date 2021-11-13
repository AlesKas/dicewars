import logging
from typing import List, Tuple

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand, TransferCommand
from dicewars.ai.utils import possible_attacks, probability_of_successful_attack, save_state
from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from dicewars.ai.name import Name

class MaxN:
    def __init__(self, player_name: Name, players_order: List[Name], heuristic):
        self.player_name = player_name
        self.players_order = players_order
        self.heuristic = heuristic


    def simulate(self, board: Board, max_depth: int):
        _, command = self.maximize(board, self.player_name, max_depth)
        return command

    def maximize(self, board: Board, current_player: Name, max_depth: int, current_depth=0):
        values = [-1 for _ in self.players_order]
        command = EndTurnCommand()
        
        if current_depth > max_depth:
            return ([self.heuristic(board, player) for player in self.players_order], EndTurnCommand())

        reasonable_attacks = self.get_reasonable_attacks(board, current_player)
        if reasonable_attacks:
            for source, target in reasonable_attacks:
                new_values = self.simulate_turn(board, source, target, current_player, max_depth, current_depth)
                
                if self.player_value(values, current_player) < self.player_value(new_values, current_player):
                    values = new_values
                    command = BattleCommand(source.get_name(), target.get_name())
        else:
            next_player = self.next_player(current_player)
            if next_player == self.player_name:
                current_depth += 1
            new_values, _ = self.maximize(board, self.next_player(current_player), max_depth, current_depth)
            if self.player_value(values, current_player) < self.player_value(new_values, current_player):
                values = new_values
                command = EndTurnCommand()

        return (values, command)
            
    
    def simulate_turn(self, board: Board, source: Area, target: Area, current_player: Name, max_depth: int, new_depth: int) -> List[int]:
        source_state = self.save_area_state(source)
        target_state = self.save_area_state(target)
        
        self.simulate_successful_attack(source, target, current_player)
        values, _ = self.maximize(board, current_player, max_depth, new_depth)

        self.load_area_state(source, source_state)
        self.load_area_state(target, target_state)
        return values
    

    def get_reasonable_attacks(self, board: Board, current_player: Name):
        return [attack for attack in possible_attacks(board, current_player) if self.is_attack_reasonable(board, attack)]
    
    def is_attack_reasonable(self, board: Board, attack: Tuple[Area, Area]) -> bool:
        from_area: Area = attack[0]
        to_area: Area = attack[1]   
        is_probable: bool = probability_of_successful_attack(board, from_area.get_name(), to_area.get_name()) > 0.5 or from_area.get_dice() >= 8
        is_relevant: bool = from_area.get_owner_name() == self.player_name or from_area.get_owner_name() == self.player_name
        return is_probable and is_relevant

    
    def simulate_successful_attack(self, source: Area, target: Area, current_player: Name):
        target.set_dice(source.get_dice() - 1)
        target.set_owner(current_player)
        source.set_dice(1)

    def save_area_state(self, area: Area) -> Tuple[Name, int]:
        return (area.get_owner_name(), area.get_dice())

    def load_area_state(self, area: Area, state: Tuple[Name, int]):
        area.set_owner(state[0])
        area.set_dice(state[1])


    def next_player(self, current_player: Name) -> Name:
        current_order = self.order_of_player(current_player)
        return (self.players_order + self.players_order)[current_order + 1]

    def player_value(self, values: List[int], player: Name) -> int:
        return values[self.order_of_player(player)]

    def order_of_player(self, player: Name) -> int:
        return self.players_order.index(player)    
