#!/usr/bin/env python3
from sys import argv
import time
from game.reversi import Reversi
from agents import random_agent, monte_carlo_agent, human_agent
from util import prop_parse, make_silent, info

prop_names = {
    # agent names. if user passes BlackAgent=human, becomes human_agent.Hu...
    'monte_carlo': monte_carlo_agent.MonteCarloAgent,
    'random': random_agent.RandomAgent,
    'human': human_agent.HumanAgent,
}


def main(**kwargs):

    input_args = prop_parse(argv)
    input_args.update(kwargs)

    if len(argv) <= 1 and len(kwargs) <= 1:
        print('necessary inputs:')
        print('  BlackAgent=, WhiteAgent=,')
        print('    choices: q_learning, monte_carlo, random, human')
        print('optional inputs:')
        print('  size=(board size), amount=(#games), silent=(True/False), sim_time=(seconds for monte carlo sim)')
        quit()

    for k, v in input_args.items():
        # convert 'human' to human_agent.HumanAgent, etc
        if v in prop_names:
            input_args[k] = prop_names[v]
        elif v == 'q_learning':
            from agents import q_learning_agent
            input_args[k] = q_learning_agent.QLearningAgent

    if any(val == monte_carlo_agent.MonteCarloAgent for val in input_args.values()) \
            and not input_args.get('sim_time', False):
        print('sim_time field required for monte_carlo agent.')
        print('quitting.')
        quit()

    amount = input_args.get('amount', 1)
    make_silent(input_args.get('silent', False))

    print('About to run {} games, black as {}, white as {}.'.format(
        amount, input_args['BlackAgent'].__name__, input_args['WhiteAgent'].__name__)
    )

    summary = []
    white_wins = 0
    black_wins = 0
    reversi = Reversi(**input_args)
    start = time.time()
    for t in range(1, amount + 1):
        info('starting game {} of {}'.format(t, amount))
        winner, white_score, black_score = reversi.play_game()
        if winner == WHITE:
            white_wins += 1
        elif winner == BLACK:
            black_wins += 1
        info('game {} complete.'.format(t))
        message = '{} wins! {}-{}'.format(
            color_name[winner], white_score, black_score)
        info(message)
        summary.append(message)

    seconds_spent = time.time() - start
    ms_per_game = (seconds_spent / amount) * 1000
    print('time: {0:.2f} minutes ({0:.2f}ms per game)'.format(
        seconds_spent / 60, ms_per_game))
    print('summary: {} games played'.format(len(summary)))
    for each in summary:
        info(each)
    wins = {'Black': black_wins / (black_wins + white_wins) *
            100, 'White': white_wins / (black_wins + white_wins) * 100}
    print('Black won {}%'.format(wins['Black']))
    print('White won {}%'.format(wins['White']))

    return wins

if __name__ == '__main__':
    main()
