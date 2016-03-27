#!/usr/bin/env python3
from agents.q_learning_agent import QLearningAgent
from game.reversi import Reversi
from util import *

import sys

def main():
    amount = 20000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
            amount = int(sys.argv[1])

    reversi = Reversi(4)
    test = QLearningAgent(reversi, BLACK, remake_model=True)
    test.train(amount)

if __name__ == "__main__":
    main()
