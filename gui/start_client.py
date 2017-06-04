import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from gui.reversi_window import ReversiWindow
from gui.socket_receiver import SocketReceiver


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = ReversiWindow(SocketReceiver())
    window.show()
    app.setQuitOnLastWindowClosed(True)
    app.exec_()
