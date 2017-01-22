import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from gui import ReversiWindow
from gui import SocketReceiver

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = ReversiWindow(SocketReceiver())
    window.show()
    app.setQuitOnLastWindowClosed(True)
    app.exec_()