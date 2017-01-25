import socket
import time
import json
import threading
import _thread
import sys

CLIENT_LOGGING = False
SERVER_LOGGING = False

HOST = ''
PORT = 10994

# frequency (seconds) to poll socket for received messages
# and push them into the queue
SOCKET_POLL_FREQ = 1 * 0.10

# frequency (seconds) to pop a message from the queue and act on it
QUEUE_POP_FREQ = 1 * 0.10


class SocketParent:
    # behavior modes
    CLIENT, SERVER = range(2)

    # message types
    CONTROL, BOARD, HELLO, MOVE, GAME_OVER, NO_MOVES = range(6)

    # control message types
    READY_TO_RECEIVE = 1  # range(1)

    def __init__(self, client_or_server):
        self.CON_TYPE = None
        self.message_queue = []
        self.connection = None

        if client_or_server == SocketParent.CLIENT:
            self.CON_TYPE = SocketParent.CLIENT
            self._init_client()
        elif client_or_server == SocketParent.SERVER:
            self.CON_TYPE = SocketParent.SERVER
            self._init_server()
        else:
            raise ValueError('Invalid value for client_or_server')

        # Start the thread for receiving messages into the message queue
        t = threading.Thread(target=self.receive_into_queue,
                             name='receive_board',
                             daemon=True)
        t.start()

        # Start the thread for popping message out of the message queue
        s = threading.Thread(target=self.pop_message_and_act_loop,
                                name='act_on_queue',
                                daemon=True)
        s.start()
    
    def _init_client(self):
        self._print_message('Attempting to connect to server....')
        while True:
            try:
                self.connection = socket.create_connection((HOST, PORT), timeout=None)
                self._print_message('Connection to server established.')
                break
            except BlockingIOError:
                time.sleep(SOCKET_POLL_FREQ)

    def _init_server(self):
        def listen_and_connect(soc):
            soc.settimeout(None)
            soc.listen(1)  # non-blocking
            self._print_message('Waiting for connection...')
            connection, address = soc.accept()  # blocking
            self._print_message('Connected to: {}:{}'.format(address[0], address[1]))
            return connection

        soc = socket.socket()
        try:
            soc.bind((HOST, PORT))
            self._print_message('Socket bound to {}:{}'.format(HOST, PORT))
        except:
            self._print_message('Couldn\'t bind to {}:{}'.format(HOST, PORT))
            self.connection.close()
            sys.exit()
        
        self.connection = listen_and_connect(soc)

    def receive_into_queue(self):
        while True:
            self.recv_json_into_queue(self.connection, self.message_queue)
            time.sleep(SOCKET_POLL_FREQ)
    
    def act_on_message(self, message):
        raise NotImplementedError
    
    def act_on_queue(self):
        """
        Pop from the queue, acting on each popped message,
        unti the queue is empty.
        """
        while len(self.message_queue) > 0:
            oldest_message = self.pop_from_queue(self.message_queue)
            if oldest_message is not None:
                self.act_on_message(oldest_message)
    
    def pop_message_and_act_loop(self):
        while True:
            self.act_on_queue()
    
    def _log(self, str_message):
        if self.CON_TYPE == SocketParent.CLIENT and CLIENT_LOGGING:
            self._print_message(str_message)
        elif self.CON_TYPE == SocketParent.SERVER and SERVER_LOGGING:
            self._print_message(str_message)
    
    def _print_message(self, str_message):
        if self.CON_TYPE == SocketParent.CLIENT:
            print('[Client] {}'.format(str_message))
            pass
        elif self.CON_TYPE == SocketParent.SERVER:
            print('[Server] {}'.format(str_message))
    
    def send_json(self, connection, json_message):
        # try:
        as_str = json.dumps(json_message)
        self.send_str(connection, as_str)
        # except:
            # self._print_message('Error converting this string to valid json: {}'.format(json_message))
    
    def send_str(self, connection, str_message):
        # newline reserved as message delimiter, enforce no newlines
        assert('\n' not in str_message)
        self._log('Sending str: {}'.format(str_message))
        as_bytes = bytearray(str_message + '\n', 'utf-8')
        self.send_bytes(connection, as_bytes)
    
    def send_bytes(self, connection, bytes_message):
        try:
            connection.sendall(bytes_message)
        except ConnectionResetError:
            self._print_message('Connection was reset.')
            self.connection.close()
            _thread.interrupt_main()
            sys.exit(1)
    
    def pop_from_queue(self, message_queue):
        if len(message_queue) == 0:
            return None
        else:
            return message_queue.pop(0)

    def recv_json_into_queue(self, connection, message_queue):
        """
        Given a socket connection and a queue,
        receive from the connection via recv_json()
        and push the result into the queue.
        """
        message_list = self.recv_json(connection)
        if message_list is not None:
            message_queue.extend(message_list)
            return message_list
        else:
            return None
    
    def recv_json(self, connection):
        """
        Given a socket connection, receive data from the connection,
        parse it from json into a dict, and return the dict.

        If there was no message to receive, returns None.
        Expects the incoming message to be valid json.

        This method is aware the string it receives from recv_str()
        may contain multiple messages delimited by newlines.  It will
        split on the delimiter and return a list of the discrete messages.
        """
        as_str = self.recv_str(connection)
        if as_str is None:
            return None
        else:
            as_str = as_str.split('\n')
            json_messages = []
            for s in [i for i in as_str if len(i) > 0]:
                try:
                    json_messages.append(json.loads(s))
                except json.JSONDecodeError:
                    self._print_message('Error decoding this json: {}'.format(s))
                    return None
            return json_messages

    def recv_str(self, connection):
        """
        Given a socket connection, receive from its buffer as a utf-8 string.
        If the resulting data is empty (i.e. string has length 0),
        returns None.  Otherwise returns a list of utf-8 strings.
        Does NOT split on newline, so if this buffer has more than one message waiting,
        this will return one string of multiple messages (delimited by newlines).
        """
        as_bytes = self.recv_bytes(connection)
        if as_bytes is None:
            return None

        as_str = str(as_bytes, 'utf-8')
        if len(as_str) > 0:
            return as_str
        else:
            return None
    
    def recv_bytes(self, connection):
        """
        Given a socket connection, receive up to 2048 bytes
        from its buffer and return that data as a bytes object.
        Returns an empty bytes object if there is no data to receive.
        """
        try:
            bytes_message = connection.recv(2048)
        except BlockingIOError:
            # Non-blocking socket couldn't immediately receive.
            return None
        except ConnectionResetError:
            self._print_message('Connection was reset.')
            self.connection.close()
            _thread.interrupt_main()

        return bytes_message