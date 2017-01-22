import socket
import time
import json
import threading

CLIENT_LOGGING = True
SERVER_LOGGING = True

HOST = ''
PORT = 10994

CLIENT_TIMEOUT = 20

# frequency (seconds) to poll socket for received messages
RECEIVE_DELAY = 1 * 0.10

class SocketParent:
    # behavior modes
    CLIENT, SERVER = range(2)

    # message types
    CONTROL, BOARD, HELLO, MOVE = range(4)

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

        s = threading.Thread(target=self.pop_message_and_act_loop,
                                name='act_on_queue',
                                daemon=True)
        s.start()
    
    def _init_client(self):
        try:
            self.connection = socket.create_connection((HOST, PORT), timeout=CLIENT_TIMEOUT)
        except:
            self._print_message('Could not establish connection, likely due to timeout.')
            quit()

    def receive_into_queue(self):
        while True:
            self.recv_json_into_queue(self.connection, self.message_queue)
            time.sleep(RECEIVE_DELAY)
    
    def act_on_message(self, message):
        raise NotImplementedError
    
    def pop_message_and_act(self):
        oldest_message = self.pop_from_queue(self.message_queue)
        if oldest_message is not None:
            self.act_on_message(oldest_message)
    
    def pop_message_and_act_loop(self):
        while True:
            self.pop_message_and_act()
            time.sleep(0.1)
    
    def _init_server(self):
        def listen_and_connect(soc):
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
            sys.exit()
        
        self.connection = listen_and_connect(soc)
    
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
        SocketParent.send_bytes(connection, as_bytes)
    
    @staticmethod
    def send_bytes(connection, bytes_message):
        connection.sendall(bytes_message)
    
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
        as_str = SocketParent.recv_str(connection)
        if as_str is None:
            return None
        else:
            as_str = as_str.split('\n')
            json_messages = []
            for s in [i for i in as_str if len(i) > 0]:
                print(s)
                try:
                    json_messages.append(json.loads(s))
                except json.JSONDecodeError:
                    self._print_message('Error decoding this json: {}'.format(s))
                    return None
            return json_messages

    @staticmethod
    def recv_str(connection):
        """
        Given a socket connection, receive from its buffer as a utf-8 string.
        If the resulting data is empty (i.e. string has length 0),
        returns None.  Otherwise returns a list of utf-8 strings.
        Does NOT split on newline, so if this buffer has more than one message waiting,
        this will return one string of multiple messages (delimited by newlines).
        """
        as_bytes = SocketParent.recv_bytes(connection)
        as_str = str(as_bytes, 'utf-8')
        if len(as_str) > 0:
            return as_str
        else:
            return None
    
    @staticmethod
    def recv_bytes(connection):
        """
        Given a socket connection, receive up to 2048 bytes
        from its buffer and return that data as a bytes object.
        Returns an empty bytes object if there is no data to receive.
        """
        bytes_message = connection.recv(2048)
        return bytes_message