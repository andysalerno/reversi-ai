from PyQt5 import QtWidgets, QtCore, QtGui
import start_gui
import run_game
from multiprocessing import Process

def main():
    # ask user for difficulty
    q_app = QtWidgets.QApplication([])
    q_widget = QtWidgets.QWidget()
    dialog = QtWidgets.QMessageBox(q_widget)
    dialog.addButton('Easy', QtWidgets.QMessageBox.ActionRole)
    dialog.addButton('Medium', QtWidgets.QMessageBox.ActionRole)
    dialog.addButton('Hard', QtWidgets.QMessageBox.ActionRole)
    dialog.addButton('Impossible', QtWidgets.QMessageBox.ActionRole)
    dialog.setText('Choose difficulty:')
    ret = dialog.exec_()

    easy, medium, hard, impossible = range(4)
    sim_time = None
    if ret == easy:
        sim_time = 1
    elif ret == medium:
        sim_time = 3
    elif ret == hard:
        sim_time = 5
    elif ret == impossible:
        sim_time = 8

    gui_process = Process(target=start_gui.main)

    gui_process.start()
    run_game.main(BlackAgent='human', WhiteAgent='monte_carlo', sim_time=sim_time, gui=True)

if __name__ == '__main__':
    main()