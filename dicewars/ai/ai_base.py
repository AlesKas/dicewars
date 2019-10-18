import json
from json.decoder import JSONDecodeError
import logging
import signal


class TimeoutError(Exception):
    pass


def TimeoutHandler(signum, handler):
    raise TimeoutError('')


TIME_LIMIT = 1.0  # in seconds, for every decision


class GenericAI(object):
    """Basic AI agent implementation
    """
    def __init__(self, game):
        """
        Parameters
        ----------
        game : Game

        Attributes
        ----------
        board : Board
        waitingForResponse : bool
           Indicates whether agent is waiting for a response from the server
        """
        self.logger = logging.getLogger('AI')
        self.game = game
        self.board = game.board
        self.player_name = game.player_name
        self.waitingForResponse = False
        self.moves_this_turn = 0
        self.turns_finished = 0
        self.time_left_last_time = TIME_LIMIT

    def run(self):
        """Main AI agent loop
        """
        game = self.game
        signal.signal(signal.SIGALRM, TimeoutHandler)

        while True:
            message = game.input_queue.get(block=True, timeout=None)
            try:
                if not self.handle_server_message(message):
                    exit(0)
            except JSONDecodeError:
                self.logger.error("Invalid message from server.")
                exit(1)
            self.current_player_name = game.current_player.get_name()
            if self.current_player_name == self.player_name and not self.waitingForResponse:
                try:
                    signal.setitimer(signal.ITIMER_REAL, TIME_LIMIT, 0)
                    self.ai_turn()
                    self.time_left_last_time, _ = signal.setitimer(signal.ITIMER_REAL, 0.0, 0)
                except TimeoutError:
                    self.logger.warning("Forced 'end_turn' because of timeout")
                    self.send_message('end_turn')
                    self.time_left_last_time = -1.0

    def ai_turn(self):
        """Actual agent behaviour
        """
        return True

    def handle_server_message(self, msg):
        """Process message from the server

        Parameters
        ----------
        msg : str
            Message from the server
        """
        self.logger.debug("Received message type {0}.".format(msg["type"]))
        if msg['type'] == 'battle':
            atk_data = msg['result']['atk']
            def_data = msg['result']['def']
            attacker = self.game.board.get_area(str(atk_data['name']))
            attacker.set_dice(atk_data['dice'])
            atk_name = attacker.get_owner_name()

            defender = self.game.board.get_area(def_data['name'])
            defender.set_dice(def_data['dice'])
            def_name = defender.get_owner_name()

            if def_data['owner'] == atk_data['owner']:
                defender.set_owner(atk_data['owner'])
                self.game.players[atk_name].set_score(msg['score'][str(atk_name)])
                self.game.players[def_name].set_score(msg['score'][str(def_name)])

            self.waitingForResponse = False

        elif msg['type'] == 'end_turn':
            current_player = self.game.players[self.game.current_player_name]

            for area in msg['areas']:
                owner_name = msg['areas'][area]['owner']

                area_object = self.game.board.get_area(int(area))

                area_object.set_owner(owner_name)
                area_object.set_dice(msg['areas'][area]['dice'])

            current_player.deactivate()
            self.game.current_player_name = msg['current_player']
            self.game.current_player = self.game.players[msg['current_player']]
            self.game.players[self.game.current_player_name].activate()
            self.waitingForResponse = False

        elif msg['type'] == 'game_end':
            self.logger.info("Player {} has won".format(msg['winner']))
            self.game.socket.close()
            return False

        return True

    def send_message(self, type, attacker=None, defender=None):
        """Send message to the server

        Parameters
        ----------
        type : str
        attacker : int
        defender : int
        """
        if type == 'close':
            msg = {'type': 'close'}
        elif type == 'battle':
            msg = {
                'type': 'battle',
                'atk': attacker,
                'def': defender
            }
            self.logger.debug("Sending battle message {}->{}".format(attacker, defender))
            self.moves_this_turn += 1
        elif type == 'end_turn':
            msg = {'type': 'end_turn'}
            self.logger.debug("Sending end_turn message.")
            self.moves_this_turn = 0
            self.turns_finished += 1

        self.waitingForResponse = True

        try:
            self.game.socket.send(str.encode(json.dumps(msg)))
        except BrokenPipeError:
            self.logger.error("Connection to server broken.")
            exit(1)
