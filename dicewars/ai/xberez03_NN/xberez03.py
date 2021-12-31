import logging
from pickle import NONE
from typing import List, Tuple, Set
from dicewars.ai.utils import probability_of_holding_area, probability_of_successful_attack, save_state
import json
from dicewars.client.ai_driver import BattleCommand, EndTurnCommand, TransferCommand
from dicewars.client.game.board import Board
from dicewars.client.game.area import Area
from dicewars.ai.maxn import MaxN
from dicewars.ai.aliases import Name

from NN_scripts.model import DCNN
import torch
import torch.nn.functional as F
import os
import sys

MAX_DEPTH = 6

class AI:
    def __init__(self, player_name, board, players_order, max_transfers):
        self.player_name = player_name
        self.logger = logging.getLogger('AI')
        self.areas = {
            "inner" : {

            },
            "outer" : {

            }
        }
        self.search = MaxN(player_name, players_order, 1, self.leaf_heuristic, self.transfer_heuristic, self.attack_heuristic)
        with open('debug.save', 'wb') as f:
                save_state(f, board, self.player_name, self.search.players_order)

    # Construct dict of areas, that are inside our territory, 
    # or have border with enemy, areas inside our territory 
    # can provide dices to areas that are on bordes
    def _construct_areas(self, board : Board):
        for area in board.get_player_border(self.player_name):
            self.areas["outer"][area.get_name()] = {
                "dices" : area.get_dice(),
                "canAttact" : area.can_attack(),
                "probabilityOfHold" : probability_of_holding_area(board, area.get_name(), area.get_dice(), self.player_name)
            }
        for area in board.get_player_areas(self.player_name):
            if area.get_name() not in self.areas["outer"].keys():
                self.areas["inner"][area.get_name()] = {
                    "dices" : area.get_dice()
                }

        #logging.info(json.dumps(self.areas, indent=4))

    # Generate path from inner node to outer node
    def _generate_path(self, board: Board, from_name: int, to_name: int) -> list:
        from_area : Area = board.get_area(from_name)
        to_area : Area = board.get_area(to_name)
        player_area_names = []
        for area in board.get_player_areas(self.player_name):
            player_area_names.append(area.get_name())
        if from_area.get_name() not in player_area_names or to_area.get_name() not in player_area_names:
            return None
        for depth in range(0, MAX_DEPTH):
            path = [from_area.get_name()]
            if self._iterate(board, from_area.get_name(), to_area.get_name(), depth, path, player_area_names):
                path.append(to_area.get_name())
                break
        return path

    # Some recursive algorthytm I invented, iterative D/B FS, finds optimal path 
    # from given area to given area, ave maria if this works correctly
    def _iterate(self,board: Board, start: int, destination: int, depth: int, visited: list, player_areas : list) -> bool:
        if depth == 0:
            # Skip returning areas that are in outer areas, so we dont move dices that 
            # are necessary for defending territory
            return destination in board.get_area(start).get_adjacent_areas_names()
        for area in board.get_area(start).get_adjacent_areas_names():
            if area in player_areas:
                if area in self.areas["outer"].keys():
                    visited.append(area)
                    return True
                visited.append(area)
                if self._iterate(board, area, destination, depth-1, visited, player_areas):
                    return True
                else:
                    visited.pop()

    # Compute outer area with lowest probability of hold, and
    # inner area with highest count of dices, so inner area can provide dices to outer area
    # Can be improved by taking into account distance between two areas
    def transfer_heuristic2(self, playerAreas : dict, declinedPaths = []) -> Tuple[int, int]:
        outerAreas : dict = playerAreas["outer"]
        innerAreas : dict = playerAreas["inner"]
        probability_of_hold = 1
        num_of_dices = 0
        lowest_outer_area = None
        highest_inner_area = None
        for areaName, value in outerAreas.items():
            if value["probabilityOfHold"] <= probability_of_hold:
                probability_of_hold = value["probabilityOfHold"]
                lowest_outer_area = areaName
        
        for areaName, value in innerAreas.items():
            if value["dices"] > num_of_dices:
                num_of_dices = value["dices"]
                highest_inner_area = areaName

        if num_of_dices == 1:
            logging.info("I only have inner areas with 1 dices, cannot move.")
            return None
        if highest_inner_area is None:
            logging.info("I have no inner area, cannot move dies.")
            return None

        return (highest_inner_area, lowest_outer_area)


    def ai_turn(self, board: Board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        # If we have just 1s left, we should end turn
        self._construct_areas(board)
        self._best_move = self.transfer_heuristic2(self.areas)
        if time_left >= 2:
            with open('debug.save', 'wb') as f:
                save_state(f, board, self.player_name, self.search.players_order)
            if nb_transfers_this_turn <= 5:
                if self._best_move is not None:
                    move_path = self._generate_path(board, self._best_move[0], self._best_move[1])
                    if move_path is not None:
                        return TransferCommand(move_path[0], move_path[1])               
            if nb_moves_this_turn == 0:
                command = self.search.simulate(board, 2)
            else:
                command = self.search.command(board)
            return command
        else:
            return EndTurnCommand()



    def leaf_heuristic(self, board: Board, current_player: Name, players_order: List[Name], end_turn_gain: int):
        from dicewars.ai.xberez03_NN.utils import game_configuration
        prediction = [-1 for _ in players_order]
        game = game_configuration(
            board=board,
            biggest_regions={
                i: len(
                    self.largest_region(
                        player_name=i,
                        board=board
                    )
                ) for i in players_order
            }
        )
        
        model = self.load_model()
        prediction = self.valid(model, game)
        prediction = prediction.tolist()

        return prediction

        
    def calculate_ring_value(self, board: Board, player_name, ring: List[Area], already_counted: Set[int]=set(), multiplier: float=1.0) -> float:
        inland_devaluation_constant = 0.8
        if not ring:
            return 0.0

        already_counted.update({area.get_name() for area in ring})
        new_ring = set()
        ring_sum = 0
        for area in ring:
            adjacents = {board.get_area(adjacent) for adjacent in area.get_adjacent_areas_names() if adjacent not in already_counted}
            owned_adjacents = {area for area in adjacents if area.get_owner_name() == player_name}
            new_ring.update(owned_adjacents)
            hold_probability = probability_of_holding_area(board, area.get_name(), area.get_dice(), area.get_owner_name())
            ring_sum += area.get_dice() * (1.0 + (hold_probability if hold_probability >= 1.0 else 0))

        return ring_sum*multiplier + self.calculate_ring_value(board, player_name, new_ring, already_counted, multiplier*inland_devaluation_constant) 


    def transfer_heuristic(self, board: Board, transfer: Tuple[Area, Area], transfers_done: List[Tuple[Area, Area]]) -> bool:
        #return True
        back_transfer = (transfer[1], transfer[0])
        if transfers_done:
            out =  back_transfer not in transfers_done and transfer != transfers_done[-1]
            if not out:
                pass#logging.debug(f"{back_transfer} not in {transfers_done} and {transfer} != {transfers_done[-1]}")
            return out
        else:
            return True

    def attack_heuristic(self, board: Board, player_name: Name,  attack: Tuple[Area, Area]) -> bool:
        from_area: Area = attack[0]
        to_area: Area = attack[1]
        if from_area.get_dice() == 8 and to_area.get_dice() == 8:
            is_probable = True
        else:
            is_probable = probability_of_successful_attack(board, from_area.get_name(), to_area.get_name()) > 0.6
        #is_probable: bool = probability_of_successful_attack(board, from_area.get_name(), to_area.get_name()) > 0.5 or from_area.get_dice() >= 8
        #is_probable: bool = from_area.get_dice() > to_area.get_dice() or (from_area.get_dice() == to_area.get_dice() and from_area.get_dice() >= 4)
        is_relevant: bool = from_area.get_owner_name() == player_name or to_area.get_owner_name() == player_name
        return is_probable and is_relevant


    def largest_region(self, player_name: int, board: Board) -> List[int]:
        players_regions = board.get_players_regions(player_name)
        max_region_size = max(len(r) for r in players_regions)

        return [r for r in players_regions if len(r) == max_region_size][0]

    def valid(self, model, data):
        data = torch.unsqueeze(torch.from_numpy(data), 0)
        data = torch.unsqueeze(data, 0).float()
        with torch.no_grad():
            model.eval()
            pred = model(data)
            vector = F.softmax(pred, dim=2)
        return torch.squeeze(torch.squeeze(vector, 0), 0)

    def load_model(self):
            model = DCNN(633, 4)
            checkpoint = torch.load(os.path.join(os.path.dirname(__file__), 'model.pt'))
            state_dict = checkpoint['state_dict']
            unParalled_state_dict = {}
            for key in state_dict.keys():
                unParalled_state_dict[key.replace("module.", "")] = state_dict[key]
            model.load_state_dict(unParalled_state_dict)
            return model
