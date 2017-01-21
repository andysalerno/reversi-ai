import socket
from util import BLACK, WHITE
from game.board import BLACK_PIECE, WHITE_PIECE

HOST = ''
PORT = 10994

EMPTY = '-'

class SocketSender:

    def __init__(self):
        print('Attempting to connect to {}:{}...'.format(HOST, PORT))
        self.soc = socket.create_connection((HOST, PORT))
        print('Connected to GUI.')
    
    def send_board(self, board):
        assert type(board).__name__ == 'Board'
        serialized = self._serialize_board(board)
        self.soc.sendall(bytearray(serialized, 'utf-8'))
    
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