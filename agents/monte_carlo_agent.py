import random
import time
import math
import copy
from agents.agent import Agent
from util import *


class MonteCarloAgent(Agent):

    def __init__(self, reversi, color, **kwargs):
        self.color = color
        self.reversi = reversi
        self.sim_time = kwargs.get('sim_time', 5)

        # map states to nodes for quick lookup
        self.state_node = {}

    def reset(self):
        pass

    def observe_win(self, winner):
        pass

    def get_action(self, game_state, legal_moves):
        """
        Interface from class Agent.  Given a game state
        and a set of legal moves, pick a legal move and return it.
        This will be called by the Reversi game object. Does not mutate
        the game state argument.
        """
        if not legal_moves:
            return None

        # make a deep copy to keep the promise that we won't mutate
        game_state = copy.deepcopy(game_state)
        move = self.monte_carlo_search(game_state)
        return move

    def monte_carlo_search(self, game_state):
        """
        Given a game state, return the best action decided by
        using Monte Carlo Tree Search with an Upper Confidence Bound.
        """

        root = None
        if game_state in self.state_node:
            # This isn't strictly necessary for Monte Carlo to work,
            # but if we've seen this state before we can get better/faster results by
            # reusing existing information.
            root = self.state_node[game_state]
        else:
            amnt_children = len(self.reversi.legal_moves(game_state))
            if self.reversi.winner(game_state) is False and amnt_children == 0:
                # if the game isn't over but a player must pass his move,
                # (i.e. no other moves are available) then this node will have
                # one child, which is the 'passing move' Node where control changes over
                # to the other player but the board doesn't change.
                amnt_children = 1
            root = Node(game_state, None, amnt_children)

        # even if this is a "recycled" node we've already used,
        # remove its parent as it is now considered our root level node
        root.parent = None

        sim_count = 0
        now = time.time()
        while time.time() - now < self.sim_time and root.moves_unfinished > 0:
            # pick move to simulate with UCB
            picked_node = self.tree_policy(root)

            # run the simulation and get the result
            result = self.simulate(picked_node.game_state)

            # back prop the result of this move up the tree
            self.back_prop(picked_node, result)
            sim_count += 1

        # the following is purely for printing information
        results = {}
        for child in root.children:
            wins, plays = child.get_wins_plays()
            position = child.move
            results[position] = (wins, plays)

        for position in sorted(results, key=lambda x: results[x][1]):
            info('{}: ({}/{})'.format(position,
                                      results[position][0], results[position][1]))
        info('{} simulations performed.'.format(sim_count))

        return self.best_action(root)

    @staticmethod
    def best_action(node):
        """
        Returns the best action from this game state node.
        In Monte Carlo Tree Search we pick the one that was
        visited the most.  We can break ties by picking
        the state that won the most.
        """
        most_plays = -float('inf')
        best_wins = -float('inf')
        best_actions = []
        for child in node.children:
            wins, plays = child.get_wins_plays()
            if plays > most_plays:
                most_plays = plays
                best_actions = [child.move]
                best_wins = wins
            elif plays == most_plays:
                # break ties with wins
                if wins > best_wins:
                    best_wins = wins
                    best_actions = [child.move]
                elif wins == best_wins:
                    best_actions.append(child.move)

        return random.choice(best_actions)

    @staticmethod
    def back_prop(node, delta):
        """
        Given a node and a delta value for wins,
        propagate that information up the tree to the root.
        """
        while node is not None:
            node.plays += 1
            node.wins += delta
            node = node.parent

    def tree_policy(self, root):
        """
        Given a root node, determine which child to visit
        using Upper Confidence Bound.
        """
        cur_node = root

        while True:
            # legal moves represent potential children of root node
            legal_moves = self.reversi.legal_moves(cur_node.game_state)
            if not legal_moves:
                if self.reversi.winner(cur_node.game_state) is not False:
                    # inform parent nodes that this path was fully explored
                    # (i.e. the root node was a leaf node)
                    cur_node.propagate_completion()
                    return cur_node
                else:
                    # no moves, but game not over, so turn passes to other player
                    next_state = self.reversi.next_state(
                        cur_node.game_state, None)
                    pass_node = Node(next_state, None, 1)
                    cur_node.add_child(pass_node)
                    self.state_node[next_state] = pass_node
                    cur_node = pass_node
                    continue

            elif len(cur_node.children) < len(legal_moves):
                # there are children (moves) that have not been tried yet
                untried = [
                    move for move in legal_moves
                    if move not in cur_node.moves_tried
                ]

                assert len(untried) > 0
                move = random.choice(untried)
                state = self.reversi.next_state(cur_node.game_state, move)
                child = Node(state, move, len(legal_moves))
                cur_node.add_child(child)
                self.state_node[state] = child
                return child

            else:
                # every next state has been simulated at least once
                cur_node = self.best_child(cur_node)
                return self.tree_policy(cur_node)

        return cur_node

    def best_child(self, node):
        """
        UCB, used in the tree policy to determine
        which child of the input node is the best to
        simulate right now.
        """
        enemy_turn = (node.game_state[1] != self.color)
        C = 1  # 'exploration' value
        values = {}
        for child in node.children:
            wins, plays = child.get_wins_plays()
            if enemy_turn:
                # the enemy will play against us, not for us
                wins = plays - wins
            _, parent_plays = node.get_wins_plays()
            assert parent_plays > 0
            values[child] = (wins / plays) + C * \
                math.sqrt(2 * math.log(parent_plays) / plays)

        best_choice = max(values, key=values.get)
        return best_choice

    def simulate(self, game_state):
        """
        Starting from the given game state, simulate
        a random game to completion, and return the profit value
        (1 for a win, 0 for a loss)
        """
        WIN_PRIZE = 1
        LOSS_PRIZE = 0
        state = copy.deepcopy(game_state)
        while True:
            winner = self.reversi.winner(state)
            if winner is not False:
                if winner == self.color:
                    return WIN_PRIZE
                elif winner == opponent[self.color]:
                    return LOSS_PRIZE
                else:
                    raise ValueError

            moves = self.reversi.legal_moves(state)
            if not moves:
                # if no moves, turn passes to opponent
                state = (state[0], opponent[state[1]])
                moves = self.reversi.legal_moves(state)

            picked = random.choice(moves)
            state = self.reversi.apply_move(state, picked)


class Node:
    # note to self: if a move is fully expanded to completion it may not be simulated
    # any more times (since there is nothing left to simulate) but since the policy
    # picks the most-simulated node this may result in winning nodes not being picked
    # as the best move to play.

    def __init__(self, game_state, move, amount_children):
        self.game_state = game_state
        self.plays = 0
        self.wins = 0
        self.children = []
        self.parent = None
        self.moves_tried = set()  # which moves have we tried at least once
        self.moves_unfinished = amount_children  # amount of moves not fully searched to completion

        # the move that led to this child state
        self.move = move

    def propagate_completion(self):
        """
        If all children of this move have each been simulated to
        completion, tell the parent that it has one fewer child
        node to expand.
        """
        if self.moves_unfinished > 0:
            self.moves_unfinished -= 1

        if self.parent is not None:
            self.parent.propagate_completion()

    def add_child(self, node):
        self.children.append(node)
        self.moves_tried.add(node.move)
        node.parent = self

    def has_children(self):
        return len(self.children) > 0

    def get_wins_plays(self):
        return self.wins, self.plays

    def __hash__(self):
        return hash(self.game_state)

    def __repr__(self):
        return 'move: {} wins: {} plays: {}'.format(self.move, self.wins, self.plays)

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.game_state == other.game_state
