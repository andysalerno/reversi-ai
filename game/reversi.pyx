from copy import deepcopy
import time
from game.board import Board, BLACK, WHITE, EMPTY
from agents.random_agent import RandomAgent
from util import *
from game.socket_sender import SocketSender

# time in ms to wait between polling move queue for moves from gui
MOVE_QUEUE_POLL = 0.10


class Reversi:
    """This class enforces the rules of the game of Reversi."""

    def __init__(self, **kwargs):
        self.size = kwargs.get('size', 8)
        self.gui_enabled = kwargs.get('gui', False)
        self.human_uses_gui = False
        self.socket_sender = None
        self.board = Board(self.size)

        WhiteAgent = kwargs.get('WhiteAgent', RandomAgent)
        BlackAgent = kwargs.get('BlackAgent', RandomAgent)
        self.white_agent = WhiteAgent(self, WHITE, **kwargs)
        self.black_agent = BlackAgent(self, BLACK, **kwargs)

        make_silent(kwargs.get('silent', False))

        if self.gui_enabled:
            self.human_uses_gui = type(self.white_agent).__name__ == 'HumanAgent' or type(
                self.black_agent).__name__ == 'HumanAgent'
            self.socket_sender = SocketSender(self.human_uses_gui)
            self.socket_sender.wait_for_gui()

        self.reset()

    def reset(self):
        """Reset the game to initial positions."""
        self.board.init_starting_position()
        self.game_state = (self.board, BLACK)
        self.legal_cache = CacheDict()

        self.white_agent.reset()
        self.black_agent.reset()

    def play_game(self):
        board_history = []
        state = self.get_state()
        self.print_board(state)
        info('')
        while self.winner(state[0]) is False:
            board_history.append(deepcopy(state[0].get_board()))
            if self.gui_enabled:
                self.socket_sender.send_board(state[0])
            color = state[1]
            picked = self.agent_pick_move(state)
            state = self.next_state(state, picked)
            self.print_board(state)
            if not picked:
                info('{} had no moves and passed their turn.'.format(
                    color_name[color]))
            else:
                info('{} plays at {}'.format(color_name[color], str(picked)))
            info('')

        board_history.append(deepcopy(state[0].get_board()))

        # Game Over
        self.white_agent.observe_win(state)
        self.black_agent.observe_win(state)

        self.print_board(state)
        # figure out who won
        black_count, white_count = state[0].get_stone_counts()
        winner = BLACK if black_count > white_count else WHITE
        info('{} wins.'.format(color_name[winner]))

        if self.gui_enabled:
            self.socket_sender.send_board(state[0])
            self.socket_sender.send_game_over(winner)

        self.reset()
        return winner, white_count, black_count, board_history

    @staticmethod
    def print_board(state):
        board = state[0]
        info(board)

    def agent_pick_move(self, state):
        color = state[1]
        legal_moves = self.legal_moves(state)
        picked = None
        if color == WHITE:
            if self.gui_enabled and type(self.white_agent).__name__ == 'HumanAgent':
                print('Waiting for human to select move in gui...')
                picked = self.gui_pick_move(legal_moves)
            else:
                picked = self.white_agent.get_action(state, legal_moves)
        elif color == BLACK:
            if self.gui_enabled and type(self.black_agent).__name__ == 'HumanAgent':
                print('Waiting for human to select move in gui...')
                picked = self.gui_pick_move(legal_moves)
            else:
                picked = self.black_agent.get_action(state, legal_moves)
        else:
            raise ValueError

        if picked is None:
            assert len(legal_moves) == 0
            if self.human_uses_gui:
                self.socket_sender.send_turn_skipped(color)
                # someone had to skip a turn and a human is playing,
                # so show them a helpful dialog message to let them know.
            return None
        elif picked not in legal_moves:
            info(str(picked) + ' is not a legal move! Game over.')
            quit()

        return picked

    def gui_pick_move(self, legal_moves):
        if len(legal_moves) == 0:
            return None

        picked = None
        while picked is None or picked not in legal_moves:
            picked = self.socket_sender.pop_move()
            time.sleep(MOVE_QUEUE_POLL)

        return picked

    def legal_moves(self, game_state, force_cache=False):
        # Note: this is a very naive and inefficient way to find
        # all available moves by brute force.  I am sure there is a
        # more clever way to do this.  If you want better performance
        # from agents, this would probably be the first area to improve.
        if force_cache:
            return self.legal_cache.get(game_state)

        board = game_state[0]
        if board.is_full():
            return []

        cached = self.legal_cache.get(game_state)
        if cached is not None:
            return cached

        cdef size_t board_size
        board_size = board.get_size()
        moves = []  # list of x,y positions valid for color

        cdef size_t y, x
        for y in range(board_size):
            for x in range(board_size):
                if self.is_valid_move(game_state, x, y):
                    moves.append((x, y))

        self.legal_cache.update(game_state, moves)
        return moves

    @staticmethod
    def is_valid_move(game_state, int x, int y):
        board, color = game_state
        piece = board.board[y][x]
        if piece != EMPTY:
            return False

        enemy = opponent[color]

        # now check in all directions, including diagonal
        cdef int distance, yp, xp
        cdef int dy, dx
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dy == 0 and dx == 0:
                    continue

                # there needs to be >= 1 opponent piece
                # in this given direction, followed by 1 of player's piece
                distance = 1
                yp = (distance * dy) + y
                xp = (distance * dx) + x

                while is_in_bounds(xp, yp, board.size) and board.board[yp][xp] == enemy:
                    distance += 1
                    yp = (distance * dy) + y
                    xp = (distance * dx) + x

                if distance > 1 and is_in_bounds(xp, yp, board.size) and board.board[yp][xp] == color:
                    return True
        return False

    def next_state(self, game_state, move):
        """Given a game_state and a position for a new piece, return a new game_state
        reflecting the change.  Does not modify the input game_state."""
        return self.apply_move(deepcopy(game_state), move)

    @staticmethod
    def apply_move(game_state, move):
        """Given a game_state (which includes info about whose turn it is) and an x,y
        position to place a piece, transform it into the game_state that follows this play."""

        # if move is None, then the player simply passed their turn
        if move is None:
            pass_state = (game_state[0], opponent[game_state[1]])
            return pass_state

        cdef int x, y
        x, y = move
        color = game_state[1]
        board = game_state[0]
        board.place_stone_at(color, x, y)

        # now flip all the stones in every direction
        enemy_color = BLACK
        if color == BLACK:
            enemy_color = WHITE

        # now check in all directions, including diagonal
        cdef int dy, dx, yp, xp
        cdef size_t distance
        to_flip = []
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dy == 0 and dx == 0:
                    continue

                # there needs to be >= 1 opponent piece
                # in this given direction, followed by 1 of player's piece
                distance = 1
                yp = (distance * dy) + y
                xp = (distance * dx) + x

                flip_candidates = []
                while is_in_bounds(xp, yp, board.size) and board.board[yp][xp] == enemy_color:
                    flip_candidates.append((xp, yp))
                    distance += 1
                    yp = (distance * dy) + y
                    xp = (distance * dx) + x

                if distance > 1 and is_in_bounds(xp, yp, board.size) and board.board[yp][xp] == color:
                    to_flip.extend(flip_candidates)

        for each in to_flip:
            board.flip_stone(each[0], each[1])

        game_state = (board, opponent[color])
        return game_state

    def winner(self, board):
        """Given a game_state, return the color of the winner if there is one,
        otherwise return False to indicate the game isn't won yet.
        Note that legal_moves() is a slow operation, so this method
        tries to call it as few times as possible."""
        black_count, white_count = board.get_stone_counts()

        # a full board means no more moves can be made, game over.
        if board.is_full():
            if black_count >= white_count:
                return BLACK
            else:
                return WHITE

        # a non-full board can still be game-over if neither player can move.
        black_legal = self.legal_moves((board, BLACK))
        if black_legal:
            return False

        white_legal = self.legal_moves((board, WHITE))
        if white_legal:
            return False

        # neither black nor white has valid moves
        if black_count >= white_count:
            return BLACK
        else:
            return WHITE

    def get_board(self):
        """Return the board from the current game_state."""
        return self.game_state[0]

    def get_state(self):
        """Returns a tuple representing the board state."""
        return self.game_state
