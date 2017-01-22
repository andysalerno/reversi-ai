from socket_parent import SocketParent
import socket
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
        super(SocketSender, self).__init__(SocketParent.SERVER)

        self.move = None  # set this when we receive a move from the gui
        self.accept_gui_moves = accept_gui_moves

    
    def act_on_message(self, message):
        print(str(message))
        assert 'type' in message.keys()

        if message['type'] == SocketParent.CONTROL and message['message'] == SocketParent.READY_TO_RECEIVE:
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
            print('[Server] connection to GUI client failed.')
            quit()
    
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