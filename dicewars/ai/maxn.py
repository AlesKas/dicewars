import logging
from typing import List, Optional, Tuple

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand, TransferCommand
from dicewars.ai.utils import possible_attacks, probability_of_successful_attack
from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from dicewars.ai.aliases import Name, Command
from dicewars.ai.move import Move
from dicewars.ai.simulator import Simulator


class MaxN:
    def __init__(self, player_name: Name, players_order: List[Name], max_transfers: int, leaf_heuristic, transfer_heuristic, attack_heuristic):
        self.player_name = player_name
        self.players_order = players_order
        self.max_transfers = max_transfers
        self.leaf_heuristic = leaf_heuristic
        self.transfer_heuristic = transfer_heuristic
        self.attack_heuristic = attack_heuristic
        self.moves_root: Optional[Move] = None
        self.simulator = Simulator(player_name, players_order)


    def simulate(self, board: Board, max_depth: int) -> Command:
        reserves = [0 for _ in self.players_order]
        self.moves_root = self.maximize(board, self.player_name, reserves, list(), 0, max_depth)
        return self.moves_root.command
        
    def command(self, board: Board) -> Command:
        if self.moves_root:
            child = self.moves_root.get_child(board, self.player_name)
            self.moves_root = child
            return child.command
        else:
            return EndTurnCommand()

    def maximize(self, board: Board, current_player: Name, reserves: List[int], trasfers_done: List[Tuple[Area, Area]], transfers: int,  depth: int) -> Move:
        scores = [-1 for _ in self.players_order]
        moves = set()
        
        if depth <= 0:
            scores = [self.leaf_heuristic(board, player, self.simulator.calculate_end_turn_gain(board, current_player, reserves)) for player in self.players_order]
            return Move.other(EndTurnCommand(), scores=scores)
            
        next_move = self.simulate_end_turn(board, current_player, reserves, trasfers_done, transfers, depth)
        command = EndTurnCommand()
        move = Move.other(command, scores=next_move.scores)
        moves.add(move)
        

        reasonable_transfers = self.get_reasonable_trasfers(board, current_player, trasfers_done, transfers)
        reasonable_attacks = self.get_reasonable_attacks(board, current_player)

        for source, target in reasonable_transfers + reasonable_attacks:
            if target.get_owner_name() == current_player:
                next_move = self.simulate_transfer(board, source, target, current_player, reserves, trasfers_done, transfers, depth)
                command = TransferCommand(source.get_name(), target.get_name())
                move = Move.other(command, next=next_move)
                moves.add(move)
            else:
                success_move, failure_move = self.simulate_attack(board, source, target, current_player, reserves, trasfers_done, transfers, depth)
                save_moves = (current_player == self.player_name)
                move = Move.attack(source, target, self.order_of_player(current_player), success_move, failure_move, save_moves)
                moves.add(move)
            
        return self.get_best_move(moves, current_player)
            
    def simulate_attack(self, board: Board, source: Area, target: Area, current_player: Name, reserves: List[int], trasfers_done: List[Tuple[Area, Area]], transfers: int, depth: int) -> Tuple[Move, Move]:
        state = self.simulator.save_pre_move_state(source, target)

        self.simulator.successful_attack(source, target, current_player)
        successful_move = self.maximize(board, current_player, reserves, list(), transfers, depth)

        self.simulator.restore_pre_move_state(source, target, state)

        self.simulator.failed_attack(source, target)
        failed_move = self.maximize(board, current_player, reserves, list(), transfers, depth)

        self.simulator.restore_pre_move_state(source, target, state)

        return (successful_move, failed_move)

    
    def simulate_transfer(self, board: Board, source: Area, target: Area, current_player: Name, reserves: List[int], trasfers_done: List[Tuple[Area, Area]], transfers: int, depth: int) -> Move:
        state = self.simulator.save_pre_move_state(source, target)
        self.simulator.transfer(source, target)
        move = self.maximize(board, current_player, reserves, trasfers_done + [(source, target)], transfers + 1, depth)
        self.simulator.restore_pre_move_state(source, target, state)
        return move


    def simulate_end_turn(self, board: Board, current_player: Name, reserves: List[int], trasfers_done: List[Tuple[Area, Area]], transfers: int, depth: int) -> Move:
        state = self.simulator.save_player_areas_state(board, current_player)

        next_player = self.next_player(current_player)
        if next_player == self.player_name:
            depth -= 1
        if current_player == self.player_name:
            self.simulator.end_turn_pessimistic(board, current_player, reserves)
        else:
            self.simulator.end_turn_optimistic(board, current_player, reserves)
        next_move = self.maximize(board, next_player, reserves, list(), 0, depth) 
        
        self.simulator.restore_player_areas_state(board, current_player, state)
        return next_move
    
    def get_reasonable_attacks(self, board: Board, current_player: Name) -> List[Tuple[Area, Area]]:
        return [attack for attack in possible_attacks(board, current_player) if self.attack_heuristic(board, self.player_name, attack)]

    def get_reasonable_trasfers(self, board: Board, current_player: Name, transfers_done: List[Tuple[Area, Area]], transfers: int) -> List[Tuple[Area, Area]]:
        if transfers >= self.max_transfers:
            return list()

        transfers = list()
        for area in board.get_player_areas(current_player):
            if area.get_dice() > 1:
                neighbours = [board.get_area(name) for name in area.get_adjacent_areas_names()]
                area_transfers = [(area, neighbour) for neighbour in neighbours if neighbour.get_owner_name() == current_player and neighbour.get_dice() < 8]
                transfers.extend(area_transfers)
        return [transfer for transfer in transfers if self.transfer_heuristic(board, transfer, transfers_done)]

    def get_best_move(self, moves: List[Move], current_player) -> Move:
        return max(moves, key=lambda move: move.scores[self.order_of_player(current_player)])

    def next_player(self, current_player: Name) -> Name:
        current_order = self.order_of_player(current_player)
        return (self.players_order + self.players_order)[current_order + 1]

    def player_score(self, scores: List[int], player: Name) -> int:
        return scores[self.order_of_player(player)]

    def order_of_player(self, player: Name) -> int:
        return self.players_order.index(player)
