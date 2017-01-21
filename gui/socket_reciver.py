import socket
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

        t = threading.Thread(target=self.socket_receive_board,
                             name='receive_board', daemon=True)
        t.start()


    def get_board(self):
        return self.board

    def socket_receive_board(self):
        while True:
            try:
                print('[Client] waiting for message...')
                raw_message = self.connection.recv(2056)
                str_message = str(raw_message, 'utf-8')
                if len(str_message) > 0:
                    self.board = str_message
                    print('[Client] message received.'.format(self.board))
            except:
                pass
            time.sleep(0.10)

    def send_move(self, move):
        pass
