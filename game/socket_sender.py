from socket_parent import SocketParent
import socket
import time
import json
import sys
from util import BLACK, WHITE
from game.board import BLACK_PIECE, WHITE_PIECE

HOST = ''
PORT = 10994

EMPTY = '-'
INITIAL_STRING = 'initial_string'

class SocketSender(SocketParent):

    def __init__(self, accept_gui_moves):
        self.move = None  # set this when we receive a move from the gui
        self.accept_gui_moves = accept_gui_moves
        self.ready_to_play = False  # not until we receive READY_TO_RECEIVE from gui
        super(SocketSender, self).__init__(SocketParent.SERVER)
    
    def wait_for_gui(self):
        """
        Blocks until ready message is received from gui.
        """
        self._print_message('Waiting to hear from gui...')
        while not self.ready_to_play:
            time.sleep(0.1)
    
    def act_on_message(self, message):
        assert 'type' in message.keys()

        if message['type'] == SocketParent.CONTROL and message['message'] == SocketParent.READY_TO_RECEIVE:
            self.ready_to_play = True
            self._log('Ready message received.')

            # Reply to ready message with hello message
            self.send_json(self.connection, {
                'type': SocketParent.HELLO,
                'spectate_only': not self.accept_gui_moves
            })
        
        elif message['type'] == SocketParent.MOVE:
            move = message['move']
            self._log('Move message received: {}'.format(move))

            x, y = move.split(',')
            self.move = (int(x), int(y))
    
    def send_board(self, board):
        assert type(board).__name__ == 'Board'
        flat_board = self._serialize_board(board)
        try:
            self.send_json(self.connection,
            {
                'type': SocketParent.BOARD,
                'board': flat_board
            })
        except:
            self._print_message('Connection to GUI client failed.')
            quit()
    
    def send_game_over(self, winner):
        self.send_json(self.connection, {
            'type': SocketParent.GAME_OVER,
            'winner': winner
        })
    
    def send_turn_skipped(self, color):
        self.send_json(self.connection, {
            'type': SocketParent.NO_MOVES,
            'color': color
        })
    
    def pop_move(self):
        ret = self.move
        self.move = None  # acts like a queue of length 1, popping move to None

        return ret
    
    @staticmethod
    def _serialize_board(board):
        assert type(board).__name__ == 'Board'
        as_str = ''
        board_size = board.size
        for h in range(board_size - 1, -1, -1):
            for w in range(board_size):
                piece_num = board.board[h][w]
                if piece_num == BLACK:
                    as_str +=  BLACK_PIECE
                elif piece_num == WHITE:
                    as_str += WHITE_PIECE
                else:
                    as_str += EMPTY
        return as_str