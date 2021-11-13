import logging
from typing import List, Optional, Tuple

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand, TransferCommand
from dicewars.ai.utils import possible_attacks, probability_of_successful_attack
from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from dicewars.ai.aliases import Name, Command
from dicewars.ai.move import Move


class MaxN:
    def __init__(self, player_name: Name, players_order: List[Name], leaf_heuristic, attack_heuristic):
        self.player_name = player_name
        self.players_order = players_order
        self.leaf_heuristic = leaf_heuristic
        self.attack_heuristic = attack_heuristic
        self.moves_root: Optional[Move] = None


    def simulate(self, board: Board, max_depth) -> Command:
        self.moves_root = self.maximize(board, self.player_name, max_depth)
        return self.moves_root.command
        
    def command(self, board: Board) -> Command:
        if self.moves_root:
            child = self.moves_root.get_child(board, self.player_name)
            self.moves_root = child
            return child.command
        else:
            return EndTurnCommand()

    def maximize(self, board: Board, current_player: Name, depth) -> Move:
        scores = [-1 for _ in self.players_order]
        moves = set()
        
        if depth <= 0:
            scores = [self.leaf_heuristic(board, player) for player in self.players_order]
            return Move.other(EndTurnCommand(), scores=scores)
            
        reasonable_attacks = self.get_reasonable_attacks(board, current_player)
        if reasonable_attacks:
            for source, target in reasonable_attacks:
                success_move, failure_move = self.simulate_attack(board, source, target, current_player, depth)
                
                save_moves = (current_player == self.player_name)
                move = Move.attack(source, target, self.order_of_player(current_player), success_move, failure_move, save_moves)
                moves.add(move)
        else:
            next_player = self.next_player(current_player)
            if next_player == self.player_name:
                 depth -= 1
            
            next_move = self.maximize(board, next_player, depth)
            command = EndTurnCommand()

            move = Move.other(command, scores=next_move.scores)
            moves.add(move)

        return self.get_best_move(moves, current_player)
            
    
    def simulate_attack(self, board: Board, source: Area, target: Area, current_player: Name, depth: int) -> Move:
        source_state = self.save_area_state(source)
        target_state = self.save_area_state(target)
        
        self.simulate_successful_attack(source, target, current_player)
        successful_move = self.maximize(board, current_player, depth)

        self.load_area_state(source, source_state)
        self.load_area_state(target, target_state)

        self.simulate_failed_attack(source, target)
        failed_move = self.maximize(board, current_player, depth)

        self.load_area_state(source, source_state)
        self.load_area_state(target, target_state)

        return (successful_move, failed_move)
    

    def get_reasonable_attacks(self, board: Board, current_player: Name) -> List[Tuple[Area, Area]]:
        return [attack for attack in possible_attacks(board, current_player) if self.attack_heuristic(board, self.player_name, attack)]

    
    def simulate_successful_attack(self, source: Area, target: Area, current_player: Name):
        source_dice = source.get_dice()
        source.set_dice(1)
        target.set_dice(source_dice - 1)
        target.set_owner(current_player)

    def simulate_failed_attack(self, source: Area, target: Area):
        source_dice = source.get_dice()
        source.set_dice(1)
        if source_dice == 8:
            dice_loss = 2
        elif source_dice >= 4:
            dice_loss = 1
        else:
            dice_loss = 0
        target.set_dice(max(target.get_dice() - dice_loss, 1))

    def save_area_state(self, area: Area) -> Tuple[Name, int]:
        return (area.get_owner_name(), area.get_dice())

    def load_area_state(self, area: Area, state: Tuple[Name, int]):
        area.set_owner(state[0])
        area.set_dice(state[1])

    def get_best_move(self, moves: set[Move], current_player) -> Move:
        return max(moves, key=lambda move: move.scores[self.order_of_player(current_player)])
        

    def next_player(self, current_player: Name) -> Name:
        current_order = self.order_of_player(current_player)
        return (self.players_order + self.players_order)[current_order + 1]

    def player_value(self, values: List[int], player: Name) -> int:
        return values[self.order_of_player(player)]

    def order_of_player(self, player: Name) -> int:
        return self.players_order.index(player)    
