import random
import sys
from argparse import ArgumentParser
import time
from signal import signal, SIGCHLD

from scripts.utils import run_ai_only_game, BoardDefinition

parser = ArgumentParser(prog='Dice_Wars')
parser.add_argument('-p', '--port', help="Server port", type=int, default=5005)
parser.add_argument('-a', '--address', help="Server address", default='127.0.0.1')

procs = []


def signal_handler(signum, frame):
    """Handler for SIGCHLD signal that terminates server and clients
    """
    for p in procs:
        try:
            p.kill()
        except ProcessLookupError:
            pass

SITING_AIs = [
    #'dt.rand',
    #'dt.sdc',
    #'dt.ste',
    #'dt.stei',
    #'dt.wpm_d',
    #'dt.wpm_s',
    #'dt.wpm_c',
    #'kb.sdc_post_at',
    #'kb.sdc_post_dt',
    #'kb.sdc_pre_at',
    #'kb.stei_adt',
    #'kb.stei_at',
    #'kb.stei_dt',
    #'kb.xlogin42',
    #'kb.xlogin00',
    'xberez03_old',
    'xberez03_2',
    'xberez03_3',
    'xberez03_4',
    #'xberez03_NN',
]

UNIVERSAL_SEED = random.randint(1, 10 ** 10)
NB_BOARDS = 50

def playing_4_ais():
    PLAYING_AIs = []
    while len(PLAYING_AIs) != 4:
        ai = SITING_AIs[random.randint(0, 3)]
        if ai not in PLAYING_AIs:
            PLAYING_AIs.append(ai)
    return PLAYING_AIs


def board_definitions():
    while True:
        random.seed(int(time.time()))
        yield BoardDefinition(random.randint(1, 10 ** 10), UNIVERSAL_SEED, UNIVERSAL_SEED)


def main():
    args = parser.parse_args()

    signal(SIGCHLD, signal_handler)

    boards_played = 0
    try:
        for board_definition in board_definitions():
            if boards_played == NB_BOARDS:
                break
            boards_played += 1
            players = playing_4_ais()
            run_ai_only_game(
                args.port, args.address, procs, players,
                board_definition,
                fixed=UNIVERSAL_SEED,
                client_seed=UNIVERSAL_SEED,
                debug=True, logdir='../logs',
            )
            print(f'Game played {players}.', file=sys.stderr)

    except (Exception, KeyboardInterrupt) as e:
        sys.stderr.write("Breaking the tournament because of {}\n".format(repr(e)))
        for p in procs:
            p.kill()
        raise


if __name__ == '__main__':
    main()