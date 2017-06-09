import math
import random

BLACK = 1.0
WHITE = 0.5
EMPTY = 0.0

color_name = {BLACK: 'Black', WHITE: 'White'}
opponent = {BLACK: WHITE, WHITE: BLACK}

silent = False


def make_silent(val):
    assert val is True or val is False
    global silent
    silent = val


def info(message):
    if not silent:
        if not message:
            print()
        else:
            print(message)


def to_offset(move, size):
    x, y = move
    return y * size + x


def is_in_bounds(x, y, size):
    return 0 <= x < size and 0 <= y < size


def best_move_val(q_vals, legal_moves):
    """Given a list of moves and a q_val array, return the move with the highest q_val and the q_val."""
    if not legal_moves:
        return None, None
    else:
        best_q = None
        best_move = None
        size = int(math.sqrt(len(q_vals[0])))
        for move in legal_moves:
            offset = to_offset(move, size)
            val = q_vals[0][offset]
            # info('{}: {}'.format(move, val))
            if best_q is None or val > best_q:
                best_q = val
                best_move = [move]
            elif best_q == val:
                best_move.append(move)

        return random.choice(best_move), best_q
