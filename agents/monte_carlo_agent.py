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
        self.tree_manager = TreeManager(self.reversi)

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

        root = self.tree_manager.get_node(game_state)

        # even if this is a "recycled" node we've already used,
        # remove its parent as it is now considered our root level node
        root.parent = None

        sim_count = 0
        now = time.time()
        while time.time() - now < self.sim_time:
            # pick move to simulate with UCT
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
            wins, plays = results[position][0], results[position][1]
            info('{}: ({}/{}) ({:.2f})'.format(position,
                                               wins, plays, wins / plays))
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
        # legal moves represent potential children of root node
        legal_moves = root.legal_moves
        if len(legal_moves) == 0:
            # no legal moves + game is over = we are at a final leaf node
            # that cannot possibly have any children; game over
            #root.amount_children_unexpanded = 0

            # if this makes ALL the parent's children expanded,
            # prop that information up the tree
            # child = root
            # parent = root.parent
            # while parent is not None and child.amount_children_unexpanded == 0:
            #     parent.amount_children_unexpanded = max(
            #         0, parent.amount_children_unexpanded - 1)
            #     new_parent = parent.parent
            #    child = parent
            #    parent = new_parent

            return root
        elif legal_moves == [None]:
            #  if player must pass turn
            next_state = self.reversi.next_state(root.game_state, None)
            pass_node = self.tree_manager.add_node(next_state, None, root)
            # return self.tree_policy(pass_node)
            return pass_node

        elif len(root.children) < len(legal_moves):
            # we have not yet tried all the children for this node
            untried = [
                move for move in legal_moves
                if move not in root.moves_tried
            ]

            assert len(untried) > 0

            # we have no information about these nodes at all, so pick randomly
            move = random.choice(untried)
            next_state = self.reversi.next_state(root.game_state, move)
            root.moves_tried.add(move)
            return self.tree_manager.add_node(next_state, move, root)

        else:
            # we have tried every child node at least once, so traverse tree
            # with UCT
            return self.tree_policy(self.best_child(root))

    def best_child(self, node):
        """
        UCT, used in the tree policy to determine
        which child of the input node is the best to
        simulate right now.
        """
        enemy_turn = (node.game_state[1] != self.color)
        C = 1  # 'exploration' value
        values = {}
        _, parent_plays = node.get_wins_plays()
        for child in node.children:
            wins, plays = child.get_wins_plays()
            if enemy_turn:
                # the enemy will play against us, not for us
                wins = plays - wins
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
                black_count, white_count = state[0].get_stone_counts()
                if black_count == white_count:
                    # we don't want to tie, we want to win!
                    return LOSS_PRIZE
                elif winner == self.color:
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


class TreeManager:

    def __init__(self, reversi):
        self.state_node = {}
        self.reversi = reversi

    def add_node(self, game_state, move, parent=None):
        legal_moves = self.reversi.legal_moves(game_state)
        is_game_over = self.reversi.winner(game_state) is not False
        if len(legal_moves) == 0 and not is_game_over:
            legal_moves = [None]  # it can only make one move: pass turn
        n = Node(game_state, move, legal_moves)
        n.parent = parent
        if parent is not None:
            parent.add_child(n)
        self.state_node[game_state] = n
        return n

    def get_node(self, game_state):
        """
        Get the existing Node for this game_state.
        Creates one if it does not yet exist.
        """
        if game_state in self.state_node:
            return self.state_node[game_state]
        else:
            return self.add_node(game_state, None)


class Node:

    def __init__(self, game_state, move, legal_moves):
        self.game_state = game_state

        self.plays = 0
        self.wins = 0

        self.children = []  # child Nodes
        self.parent = None

        self.move = move  # move that led from parent to this child
        self.legal_moves = legal_moves
        self.moves_tried = set()

        # how many children have NOT been fully expanded (had their subtrees
        # completely searched)?
        self.amount_children_unexpanded = len(self.legal_moves)

    def add_child(self, child_node):
        self.children.append(child_node)
        child_node.parent = self

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
