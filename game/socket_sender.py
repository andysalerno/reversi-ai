import socket
import json
import sys
from util import BLACK, WHITE
from game.board import BLACK_PIECE, WHITE_PIECE

HOST = ''
PORT = 10994

EMPTY = '-'
INITIAL_STRING = 'initial_string'

class SocketSender:

    def __init__(self):
        self.soc = socket.socket()
        try:
            self.soc.bind((HOST, PORT))
            print('[Server] socket bound to {}:{}'.format(HOST, PORT))
        except:
            print('[Server] couldn\'t bind to {}:{}'.format(HOST, PORT))
            sys.exit()
        
        self.connection = self.listen_and_connect()

        # send an initial configuration string of metadata
        self.send_str(self.connection, json.dumps({
            'hello': 'test_config_string'
        }))
    
    def send_board(self, board):
        assert type(board).__name__ == 'Board'
        flat_board = self._serialize_board(board)
        try:
            message = json.dumps({
                'board': flat_board
            })
            self.send_str(self.connection, message)
        except:
            print('[Server] connection to GUI client failed.')
            quit()
    
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

    def listen_and_connect(self):
        self.soc.listen(1)  # non-blocking
        print('[Server] waiting for connection...')
        connection, address = self.soc.accept()  # blocking
        print('[Server] connected to: {}:{}'.format(address[0], address[1]))
        return connection
    
    @staticmethod
    def send_str(connection, str_message):
        as_bytes = bytearray(str_message, 'utf-8')
        print('[Server]: sending message: {}'.format(str_message))
        connection.sendall(as_bytes)