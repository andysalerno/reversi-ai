import sys
from reversi_window import ReversiWindow
from PyQt5 import QtWidgets, QtCore, QtGui
from socket_reciver import SocketReceiver

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = ReversiWindow(SocketReceiver())
    window.show()
    app.setQuitOnLastWindowClosed(True)
    app.exec_()

if __name__ == '__main__':
    main()