from gui.socket_parent import SocketParent
from util import color_name


class SocketReceiver(SocketParent):

    def __init__(self):
        super(SocketReceiver, self).__init__(SocketParent.CLIENT)
        self.board = None
        self.winner = None
        self.no_moves = None
        self.spectate_only = True  # if True, don't bother sending clicks to gameserver

        # CONNECTION PROTOCOL
        # 1. First message is "ready to receive" from gui to game server
        self.send_ready_to_recv(self.connection)

        # 2. Next the "hello" message is sent from game server to gui
        # (this is handled in the receive thread loop)

    def get_board(self):
        return self.board

    def get_winner(self):
        ret = self.winner
        self.winner = None
        return ret

    def get_no_moves(self):
        ret = self.no_moves
        self.no_moves = None
        return ret

    def act_on_message(self, message):
        if message['type'] == SocketParent.BOARD:
            self._log('Acting on message BOARD.')
            self.board = message['board']
        elif message['type'] == SocketParent.HELLO:
            self._log('Acting on message HELLO.')
            self.spectate_only = message['spectate_only'] == True
        elif message['type'] == SocketParent.GAME_OVER:
            self._log('Acting on message GAME_OVER.')
            win_enum = message['winner']
            self.winner = color_name[win_enum]
        elif message['type'] == SocketParent.NO_MOVES:
            # send over the color of the player with no moves
            self.no_moves = message['color']
        else:
            raise ValueError(
                'Unexpected message type: {}'.format(message['type']))

    def send_move(self, move):
        if not self.spectate_only:
            self.send_json(self.connection, {
                'type': SocketParent.MOVE,
                'move': '{},{}'.format(move[0], move[1])
            })
            self._log('Sent move: {}'.format(move))
        else:
            self._log('Spectator only mode; click not sent.')

    def send_ready_to_recv(self, connection):
        """
        Tell the sender that we've flushed our buffer and we're ready
        to receive again.
        """
        self.send_json(connection, {
            'type': SocketParent.CONTROL,
            'message': SocketParent.READY_TO_RECEIVE,
        })
