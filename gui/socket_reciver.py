import socket
import sys
import time

HOST = ''
PORT = 10994

TIMEOUT = 1 * 60


class SocketReceiver:

    def __init__(self):
        self.soc = socket.socket()

        try:
            self.soc.bind((HOST, PORT))
            print('socket connected to {}:{}'.format(HOST, PORT))
        except:
            print('couldn\'t bind to {}:{}'.format(HOST, PORT))
            sys.exit()


        self.connection = self.establish_connection()

    def receive_board(self):
        message = self.connection.recv(2056)
        return str(message, 'utf-8')

    def send_move(self, move):
        pass

    def _get_one_message(self):
        pass

    def establish_connection(self):
        self.soc.listen(1)
        print('Waiting for connection...')
        connection, address = self.soc.accept()
        print('connected to: {}:{}'.format(address[0], address[1]))
        return connection
