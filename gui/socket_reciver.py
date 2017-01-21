import socket
import json
import threading
import sys
import time

HOST = ''
PORT = 10994

class SocketReceiver:

    def __init__(self):
        self.board = None

        print('[Client] Attempting to connect to {}:{}...'.format(HOST, PORT))
        self.connection = socket.create_connection((HOST, PORT), timeout=10)
        print('[Client] Connected.')

        # part of protocol, first string will contain config info
        # like board size, whether there is a human player, etc
        self.config_string = self.receive_json(self.connection)
        print(self.config_string)
        print('[Client] got config string: {}'.format(self.config_string))

        t = threading.Thread(target=self.socket_receive_board,
                             name='receive_board', daemon=True)
        t.start()


    def get_board(self):
        return self.board

    def socket_receive_board(self):
        while True:
            try:
                print('[Client] waiting for message...')
                board_str = self.receive_json(self.connection)['board']
                if len(board_str) > 0:
                    self.board = board_str
                    print('[Client] message received.'.format(board_str))
            except:
                pass
            time.sleep(0.10)

    def send_move(self, move):
        pass
    
    @staticmethod
    def receive_str(connection):
        raw_bytes = connection.recv(2056)
        return str(raw_bytes, 'utf-8')
    
    def receive_json(self, connection):
        str_message = self.receive_str(connection)
        return json.loads(str_message)

