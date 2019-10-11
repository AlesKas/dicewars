import numpy

from .ai_base import GenericAI
from .utils import probability_of_successful_attack, sigmoid


class AI(GenericAI):
    """Agent using Win Probability Maximization (WPM) using logarithms of player dice

    This agent estimates win probability given the current state of the game.
    As a feature to describe the state, a vector of logarithms of players' scores
    is used. The agent choses such moves, that will have the highest improvement
    in the estimated probability.
    """
    def __init__(self, game):
        """
        Parameters
        ----------
        game : Game

        Attributes
        ----------
        players_order : list of int
            Names of players in the order they are playing, with the agent being first
        weights : dict of numpy.array
            Weights for estimating win probability
        largest_region: list of int
            Names of areas in the largest region
        """
        super(AI, self).__init__(game)
        self.players = len(self.game.players)
        self.largest_region = []

        self.players_order = game.players_order
        while self.player_name != self.players_order[0]:
            self.players_order.append(self.players_order.pop(0))

        self.weights = {
            2: numpy.array([3.06600354, -3.06600354]),
            3: numpy.array([1.16329046, -0.81105584, -0.80085993]),
            4: numpy.array([0.91252927, -0.55857427, -0.51781521, -0.57183507]),
            5: numpy.array([0.80138262, -0.43013021, -0.4388323, -0.48048114, -0.45301658]),
            6: numpy.array([0.74465716, -0.40179109, -0.39851363, -0.39515928, -0.43863283, -0.38371555]),
            7: numpy.array([0.72382109, -0.39171476, -0.39423241, -0.38390144, -0.38401564, -0.36980703, -0.36138501]),
            8: numpy.array([0.72340846, -0.35936507, -0.38758583, -0.35487285, -0.37616735, -0.37974499, -0.34989554, -0.37451491]),
        }[self.players]
        numpy.warnings.filterwarnings('ignore')

    def ai_turn(self):
        """AI agent's turn

        This agent estimates probability to win the game from the feature vector associated
        with the outcome of the move and chooses such that has highest improvement in the
        probability.
        """
        self.logger.debug("Looking for possible turns.")
        turns = self.possible_turns()
        if turns and turns[0][0] != 'end':
            turn = turns[0]
            area_name = turn[0]
            self.logger.debug("Possible turn: {}".format(turn))
            atk_area = self.board.get_area(turn[0])
            atk_power = atk_area.get_dice()

            if turn[2] >= -0.05 or atk_power == 8:
                self.send_message('battle', attacker=turn[0], defender=turn[1])
                self.waitingForResponse = True
                return True

        if turns and turns[0][0] == 'end':
            for i in range(1, len(turns)):
                area_name = turns[i][0]
                atk_area = self.board.get_area(area_name)
                atk_power = atk_area.get_dice()
                if atk_power == 8:
                    self.send_message('battle', attacker=area_name, defender=turns[i][1])
                    self.waitingForResponse = True
                    return True

        self.logger.debug("Don't want to attack anymore.")
        self.send_message('end_turn')
        self.waitingForResponse = True

        return True

    def possible_turns(self):
        """Get list of possible turns with the associated improvement
        in estimated win probability. The list is sorted in descending order
        with respect to the improvement.
        """
        turns = []
        name = self.player_name

        features = []
        for p in self.players_order:
            dice = numpy.log(self.game.board.get_player_dice(p))
            if numpy.isinf(dice):
                dice = 0
            features.append(dice)

        wp_start = numpy.log(sigmoid(numpy.dot(numpy.array(features), self.weights)))

        end_features = [d for d in features]
        end_features[0] = numpy.log(self.game.board.get_player_dice(name) + self.get_score_by_player(name))
        if numpy.isinf(end_features[0]):
            end_features[0] = 0
        wp_end = numpy.log(sigmoid(numpy.dot(numpy.array(end_features), self.weights)))
        improvement = wp_end - wp_start

        turns.append(['end', 0, improvement])

        for area in self.board.areas.values():
            # area belongs to the player and has strength to attack
            if area.get_owner_name() == name and area.get_dice() > 1:
                area_name = area.get_name()
                atk_power = area.get_dice()

                for adj in area.get_adjacent_areas():
                    adjacent_area = self.board.get_area(adj)

                    # adjacent area belongs to an opponent
                    opponent_name = adjacent_area.get_owner_name()
                    if opponent_name != name:
                        def_power = adjacent_area.get_dice()
                        # check whether the attack would expand the largest region
                        increase_score = False
                        if area_name in self.largest_region:
                            increase_score = True
                        else:
                            for n in adjacent_area.get_adjacent_areas():
                                if n in self.largest_region:
                                    increase_score = True
                                    break

                        a_dice = self.game.board.get_player_dice(name)
                        a_score = self.get_score_by_player(name)
                        if increase_score:
                            a_score += 1

                        atk_dice = {
                            "current": a_dice,
                            "win": a_dice + a_score,
                            "loss": a_dice + a_score - atk_power + 1,
                        }

                        d_dice = self.game.board.get_player_dice(opponent_name)
                        d_score = self.get_score_by_player(opponent_name)
                        def_dice = {
                            "loss": d_dice,
                            "win": d_dice - def_power,
                        }

                        atk_prob = probability_of_successful_attack(self.board, area_name, adj)
                        opponent_idx = self.players_order.index(opponent_name)
                        win_features = [d for d in features]
                        win_features[0] = numpy.log(atk_dice["win"])
                        if numpy.isinf(win_features[0]):
                            win_features[0] = 0
                        win_features[opponent_idx] = numpy.log(def_dice["win"])
                        if numpy.isinf(win_features[opponent_idx]):
                            win_features[opponent_idx] = 0

                        loss_features = [d for d in features]
                        loss_features[0] = numpy.log(atk_dice["loss"])
                        if numpy.isinf(loss_features[0]):
                            loss_features[0] = 0
                        loss_features[opponent_idx] = numpy.log(def_dice["loss"])
                        if numpy.isinf(loss_features[opponent_idx]):
                            loss_features[opponent_idx] = 0

                        wp_win = sigmoid(numpy.dot(numpy.array(win_features), self.weights))
                        wp_loss = sigmoid(numpy.dot(numpy.array(loss_features), self.weights))

                        wp_win = sigmoid(numpy.dot(numpy.array(win_features), self.weights))
                        wp_loss = sigmoid(numpy.dot(numpy.array(loss_features), self.weights))
                        total_prob = (wp_win * atk_prob) + (wp_loss * (1.0 - atk_prob))
                        wp_atk = numpy.log(total_prob)

                        improvement = wp_atk - wp_start
                        turns.append([area_name, adj, improvement])

        return sorted(turns, key=lambda turn: turn[2], reverse=True)

    def get_score_by_player(self, player_name, skip_area=None):
        """Get score of a player

        Parameters
        ----------
        player_name : int
        skip_area : int
            Name of an area to be excluded from the calculation

        Returns
        -------
        int
            score of the player
        """
        board = self.game.board
        score = 0
        areas_to_test = []
        player_areas = []

        # Find player areas and skip the area specified by skip_area
        for area in self.board.areas.values():
            if (area.get_owner_name() == player_name and area.get_name() != skip_area):
                areas_to_test.append(area.get_name())

        if not areas_to_test:
            return 0

        areas_in_current_region = [areas_to_test[0]]
        # Iterate over all areas belonging to the player
        while areas_to_test:
            areas_already_tested = []
            # Iterate over a single region
            while areas_in_current_region:
                current_area = areas_in_current_region[0]
                areas_in_current_region.remove(current_area)
                areas_already_tested.append(current_area)

                for area in board.get_area(current_area).get_adjacent_areas():
                    if (area not in areas_already_tested and
                        area not in areas_in_current_region and
                        area != skip_area):
                        if board.get_area(area).get_owner_name() == player_name:
                            areas_in_current_region.append(area)

            if len(areas_already_tested) > score:
                score = len(areas_already_tested)

            # Remove areas in the current region from the areas yet to be tested
            for area in areas_already_tested:
                if area in areas_to_test:
                    areas_to_test.remove(area)
                    player_areas.append(area)

            if areas_to_test:
                areas_in_current_region = [areas_to_test[0]]

        return score

    def get_largest_region(self):
        """Get size of the largest region, including the areas within

        Attributes
        ----------
        largest_region : list of int
            Names of areas in the largest region

        Returns
        -------
        int
            Number of areas in the largest region
        """
        self.largest_region = []
        largest_region_size = 0

        players_regions = get_players_regions(self.board, self.player_name)
        max_region_size = max(len(region) for region in players_regions)
        max_sized_regions = [region for region in players_regions if len(region) == max_region_size]

        for region in max_sized_regions:
            for area in region:
                self.largest_region.append(area)
        return largest_region_size


def get_players_regions(board, player_name):
    area_names_to_test = [area.get_name() for area in board.get_player_areas(player_name)]

    if not area_names_to_test:
        return 0

    regions = []
    while area_names_to_test:
        area_names_in_current_region = get_areas_region(board, area_names_to_test[0], area_names_to_test)
        regions.append(area_names_in_current_region)

        for area in area_names_in_current_region:
            area_names_to_test.remove(area)

    return regions


def get_areas_region(board, area_name, available_areas):
    current_region = [area_name]
    already_tested = []
    while current_region:
        current_area = current_region[0]
        current_region.remove(current_area)
        already_tested.append(current_area)

        for neighbour_name in board.get_area(current_area).get_adjacent_areas():
            if neighbour_name in already_tested:
                continue
            if neighbour_name in current_region:
                continue

            if neighbour_name in available_areas:
                current_region.append(neighbour_name)

    return current_region
