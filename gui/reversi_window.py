from PyQt5 import QtWidgets, QtCore, QtGui

GREEN = QtGui.QColor(51, 204, 51)
BLACK = QtGui.QColor(0, 0, 0)
WHITE = QtGui.QColor(255, 255, 255)

POLL_QUEUE = 0.25 * 1000 


class ReversiWindow(QtWidgets.QWidget):

    def __init__(self, socket_receiver):
        super(ReversiWindow, self).__init__()
        self.socket_receiver = socket_receiver
        self.setAutoFillBackground(True)
        self.setMinimumSize(320, 240)
        self.board = None


        # timer for repainting/polling network
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.net_tick)
        timer.start(POLL_QUEUE)
    
    def net_tick(self):
        self.board = self.socket_receiver.get_board()
        self.repaint()

    def resizeEvent(self, resize_event):
        new_size = resize_event.size()
        new_height = new_size.height()
        new_width = int(new_height * 1) #  change ratio how you like
        self.resize(new_width, new_height)

    def paintEvent(self, q_paint_event):
        # board background color
        painter = QtGui.QPainter(self)
        bg_path = QtGui.QPainterPath()
        bg_path.addRect(0, 0, self.width(), self.height())
        painter.fillPath(bg_path, GREEN)

        # draw the board lines
        for i in range(8):
            x_pos = self.width() / 8 * i
            painter.drawLine(x_pos, 0, x_pos, self.height())

            y_pos = self.height() / 8 * i
            painter.drawLine(0, y_pos, self.width(), y_pos)

        if self.board is not None and len(self.board) >= 8 * 8:
            for h in range(8):
                for w in range(8):
                    pieces_path = QtGui.QPainterPath()
                    w_dist = self.width() / 8
                    h_dist = self.height() / 8

                    x_pos = w_dist * w
                    y_pos = h_dist * h

                    bounding_rect = QtCore.QRectF(x_pos, y_pos, w_dist, h_dist)

                    index = (h * 8) + w
                    piece = self.board[index]
                    if piece == 'O':
                        pieces_path.addEllipse(bounding_rect)
                        painter.fillPath(pieces_path, WHITE)
                    elif piece == 'X':
                        pieces_path.addEllipse(bounding_rect)
                        painter.fillPath(pieces_path, BLACK)

                
    