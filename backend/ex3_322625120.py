import itertools
import math
import time
from copy import deepcopy

IDS = ["322625120"]
from simulator import Simulator
import random

CAPACITY = 2


class Agent:
    def __init__(self, initial_state, player_number):
        self.ids = IDS
        self.player_number = player_number
        self.my_ships = []
        self.simulator = Simulator(initial_state)
        for ship_name, ship in initial_state['pirate_ships'].items():
            if ship['player'] == player_number:
                self.my_ships.append(ship_name)
        self.secondAgent=UCTAgent(initial_state,player_number)

    def act(self, state):
        return self.secondAgent.act(state)

class UCTNode:
    """
    A class for a single node. not mandatory to use but may help you.
    """

    def __init__(self, parent=None, action=None):
        """
                Initialize a new node with optional parent and action leading to this node.

                :param action: The action that leads to this node (None for the root node).
                :param parent: The parent of this node in the tree.
                """
        self.action = action  # The action taken to reach this node
        self.parent = parent  # The parent node in the tree
        self.children = []  # Child nodes

        self.visits = 0  # Number of visits to this node
        self.reward = 0.0  # Total reward from this node
        # self.state = state  # Store the state at this node

    def is_leaf(self):
        return len(self.children) == 0

    def add_child(self, child_node):
        """
        Add a child node to this node.

        :param child_node: The child node to be added.
        """
        self.children.append(child_node)

    def expand(self, actions):
        for action in actions:
            new_child = UCTNode(parent=self, action=action)
            self.add_child(new_child)

    def update(self, reward):
        self.visits += 1
        self.reward += reward
        # self.avg_result = self.total_result / self.num_visits

    def ucb1(self):
        """
        Calculate the UCB1 value for this node.

        :param total_visits: The total number of visits in the tree (used for normalization).
        :return: The UCB1 value of this node.
        """
        if self.visits == 0:
            return float('inf')  # to ensure unvisited nodes are prioritized
        return (self.reward / self.visits) + math.sqrt(2*math.log(self.parent.visits) / self.visits)

    def get_action(self):
        return self.action

    def select_child(self, sim, player_num):
        children = []
        for child in self.children:
            treasure_is_taken = False
            for atomic_action in child.get_action():
                if atomic_action[0] == 'collect' or atomic_action[0] == 'deposit':
                    if atomic_action[2] not in sim.get_state()['treasures']:
                        treasure_is_taken = True
                        break
            if not treasure_is_taken and check_if_action_legal(sim, child.action, player_num):
                children.append(child)
        max_child = None
        max_uct_value = float('-inf')
        for child in children:
            uct_value = child.ucb1()
            if uct_value > max_uct_value:
                max_child = child
                max_uct_value = uct_value
        return max_child


class UCTTree:
    """
    A class for a Tree. not mandatory to use but may help you.
    """

    def __init__(self, root_node):
        """
        Initialize the UCT tree with a root node.

        :param root_node: The root node of the tree, typically representing the current game state.
        """
        self.root = root_node
        self.current_node = self.root


class UCTAgent:
    def __init__(self, initial_state, player_number):
        self.ids = IDS
        self.player_number = player_number
        self.my_ships = []
        self.simulator = Simulator(initial_state)
        self.turns_to_go = self.simulator.turns_to_go / 2
        for ship_name, ship in initial_state['pirate_ships'].items():
            if ship['player'] == player_number:
                self.my_ships.append(ship_name)



    def selection(self, tree, simulator):
        """
            Perform the selection phase of the UCT algorithm.


            :param    tree: The UCT tree representing the game state.
            :param    simulator: The simulator object representing the current game state.
            """
        node = tree.root
        while node.children:
            node = node.select_child(simulator, self.player_number)
            tree.current_node = node
            simulator.act(tree.current_node.get_action(), self.player_number)
            random_action = random.choice(get_actions(simulator.get_state(), simulator, 3-self.player_number))
            simulator.act(random_action, 3-self.player_number)
            state=simulator.get_state()
            value=self.evaluate_state(state)

    def expansion(self, tree, simulator):
        """
           Expand the UCT tree by adding new child nodes.

           :param    tree : The UCT tree representing the game state.
           :param    simulator : The simulator object representing the current game state.
           """
        state = simulator.get_state()
        new_actions = get_actions(state, simulator, self.player_number)
        tree.current_node.expand(new_actions)

    def simulation(self, simulator, player_num, turns_to_go):
        """
            Simulates the game for a certain number of turns.


            :param    simulator : The simulator object representing the current game state.
            :param    player_num : The player number for which to simulate the turns.
            :param    turns_to_go : The number of turns remaining for the simulation.

            :return: The score difference between the player and the opponent after simulation.
            """
        if turns_to_go == 0:
            score = simulator.get_score()
            if player_num == 1:
                return score['player 1'] - score['player 2']
            else:
                return score['player 2'] - score['player 1']
        temp_state=deepcopy(simulator.get_state())
        value=self.evaluate_state(temp_state)
        while turns_to_go > 0 :
            state = simulator.state
            actions = get_actions(state, simulator, player_num)
            if not actions:
                break
            action = random.choice(actions)
            while not check_if_action_legal(simulator, action, player_num):
                actions.remove(action)
                if not actions:
                    break
                action = random.choice(actions)
            if check_if_action_legal(simulator, action, player_num):
                simulator.act(action, player_num)
            temp_state=simulator.get_state()
            value = self.evaluate_state(temp_state)
            # Switch players and decrement the turn count
            player_num = 3 - player_num
            turns_to_go -= 0.5
        final_scores = simulator.get_score()
        if player_num == 1:
            return final_scores['player 1'] - final_scores['player 2']
        else:
            return final_scores['player 2'] - final_scores['player 1']

    def backpropagation(self, tree, simulation_result):
        """
            Update the tree based on the simulation result.

            :param tree: The tree from which to start backpropagation.
            :param simulation_result: The result of the simulation to backpropagate.
            """
        node = tree.current_node
        leaf_flag=False
        if node.is_leaf():
            leaf_flag=True
        while node:
            node.update(simulation_result)
            node = node.parent

    def act(self, state):
        """
            Perform the UCT search to find the best action to take from the current state.

            :param state: The current state of the game.
            :return: The best action to take.
            """
        root_node = UCTNode()
        tree = UCTTree(root_node)
        start_time = time.time()
        while time.time() - start_time < 4.5:
            simulator = Simulator(state)
            self.selection(tree, simulator)
            if simulator.turns_to_go:
                self.expansion(tree, simulator)
            score = self.simulation(simulator, self.player_number, self.turns_to_go)
            self.backpropagation(tree, score)
        self.turns_to_go -= 1

        best_action = max(tree.root.children, key=lambda child: child.ucb1()).action

        return best_action

    def evaluate_state(self, temp_state):
        score = 0  # Placeholder for the heuristic score

        # Example: Calculate score based on the number of treasures collected
        for treasure_info in temp_state['treasures'].values():
            if type(treasure_info['location']) is str:
                if treasure_info['location']in self.my_ships:
                    score += 1  # Increase score for each treasure collected by the player

        return score


def get_actions(state, simulator, player):
    """
        Calculate the UCB1 value for this node.

        :param state: The current state of the game.
        :param simulator: simulator for the game
        :param player: the player number
        :return: legal_actions - a list containing all possible actions from a given state.
        """
    map = state['map']
    treasures = state['treasures']
    legal_actions = []
    actions = {}
    # simulator.set_state(state)  #  ??????
    for pirate_ship, details in state['pirate_ships'].items():
        if details['player'] == player:
            current_location = details['location']
            capacity = details['capacity']
            plunder_actions = add_plunder_actions(state, current_location, pirate_ship, player)
            sail_actions = add_sail_actions(pirate_ship,current_location, map)
            deposit_treasure_actions = add_deposit_actions(current_location,pirate_ship, state, capacity)
            collect_treasure_actions = add_collect_actions(current_location, treasures, pirate_ship, capacity)
            actions[pirate_ship] = [('wait', pirate_ship)] + sail_actions + \
                                   collect_treasure_actions + deposit_treasure_actions + plunder_actions
    all_actions_combinations = list(itertools.product(*actions.values()))

    for action in all_actions_combinations:
        if _is_action_mutex(action) and check_if_action_legal(simulator, action, player):
            legal_actions.append(action)

    return legal_actions

def add_sail_actions(pirate_ship, current_location,map):
    actions = []
    x, y = current_location
    num_rows, num_cols = len(map), len(map[0])
    directions = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}

    for (dx, dy) in directions.values():
        new_x, new_y = x + dx, y + dy
        # Check if new position is within map bounds and not 'I'
        if 0 <= new_x < num_rows and 0 <= new_y < num_cols and map[new_x][new_y] != 'I':
            actions.append(("sail", pirate_ship, (new_x, new_y)))
    return actions




def add_collect_actions(current_location, treasures, pirate_ship, capacity):
    actions = []
    if capacity == 0:
        return actions  # Ship is full, no place for more treasures
    for treasure, details in treasures.items():
        if type(details['location']) is tuple:
            treasure_location = details['location']
            if distance(treasure_location, current_location) == 1:
                actions.append(("collect", pirate_ship, treasure))

    return actions

def add_deposit_actions(ship_location,ship,  state, capacity):
    actions = []
    if capacity < CAPACITY and state["base"] == ship_location:
        for treasure, details in state["treasures"].items():
            if details['location'] == ship:
                # print("deposited")
                actions.append(("deposit", ship, treasure))
    return actions

def distance(a, b):
    """The distance between two (x, y) points."""
    xA, yA = a
    xB, yB = b
    return math.hypot((xA - xB), (yA - yB))


def add_plunder_actions(state,ship_location,ship ,player):
    plunder_actions=[]
    for ship_name, ship_info in state["pirate_ships"].items():
        if (ship_info['player'] == 3 - player) and (ship_info['capacity'] < CAPACITY) and (ship_location == ship_info['location']):
            plunder_actions.append(("plunder", ship, ship_name))
    return plunder_actions

def _is_action_mutex(global_action):
    assert type(
        global_action) == tuple, "global action must be a tuple"
    # one action per ship
    if len(set([a[1] for a in global_action])) != len(global_action):
        return False
    # collect the same treasure
    collect_actions = [a for a in global_action if a[0] == 'collect']
    if len(collect_actions) > 1:
        treasures_to_collect = set([a[2] for a in collect_actions])
        if len(treasures_to_collect) != len(collect_actions):
            return False
    return True
def check_if_action_legal(simulator, action, player):
    def _is_move_action_legal(move_action, player):
        pirate_name = move_action[1]
        if pirate_name not in simulator.state['pirate_ships'].keys():
            return False
        if player != simulator.state['pirate_ships'][pirate_name]['player']:
            return False
        l1 = simulator.state['pirate_ships'][pirate_name]['location']
        l2 = move_action[2]
        if l2 not in simulator.neighbors(l1):
            return False
        return True

    def _is_collect_action_legal(collect_action, player):
        pirate_name = collect_action[1]
        treasure_name = collect_action[2]
        if player != simulator.state['pirate_ships'][pirate_name]['player']:
            return False
        # check adjacent position
        l1 = simulator.state['treasures'][treasure_name]['location']
        if simulator.state['pirate_ships'][pirate_name]['location'] not in simulator.neighbors(l1):
            return False
        # check ship capacity
        if simulator.state['pirate_ships'][pirate_name]['capacity'] <= 0:
            return False
        return True

    def _is_deposit_action_legal(deposit_action, player):
        pirate_name = deposit_action[1]
        treasure_name = deposit_action[2]
        # check same position
        if player != simulator.state['pirate_ships'][pirate_name]['player']:
            return False
        if simulator.state["pirate_ships"][pirate_name]["location"] != simulator.base_location:
            return False
        if simulator.state['treasures'][treasure_name]['location'] != pirate_name:
            return False
        ########################################################################################3
        if treasure_name not in simulator.state['treasures']:
            return False

        return True

    def _is_plunder_action_legal(plunder_action, player):
        pirate_1_name = plunder_action[1]
        pirate_2_name = plunder_action[2]
        if player != simulator.state["pirate_ships"][pirate_1_name]["player"]:
            return False
        if simulator.state["pirate_ships"][pirate_1_name]["location"] != simulator.state["pirate_ships"][pirate_2_name]["location"]:
            return False
        return True

    def _is_action_mutex(global_action):
        assert type(
            global_action) == tuple, "global action must be a tuple"
        # one action per ship
        if len(set([a[1] for a in global_action])) != len(global_action):
            return True
        # collect the same treasure
        collect_actions = [a for a in global_action if a[0] == 'collect']
        if len(collect_actions) > 1:
            treasures_to_collect = set([a[2] for a in collect_actions])
            if len(treasures_to_collect) != len(collect_actions):
                return True

        return False

    players_pirates = [pirate for pirate in simulator.state['pirate_ships'].keys() if simulator.state['pirate_ships'][pirate]['player'] == player]

    if len(action) != len(players_pirates):
        return False
    for atomic_action in action:
        # trying to act with a pirate that is not yours
        if atomic_action[1] not in players_pirates:
            return False
        # illegal sail action
        if atomic_action[0] == 'sail':
            if not _is_move_action_legal(atomic_action, player):
                return False
        # illegal collect action
        elif atomic_action[0] == 'collect':
            if not _is_collect_action_legal(atomic_action, player):
                return False
        # illegal deposit action
        elif atomic_action[0] == 'deposit':
            if not _is_deposit_action_legal(atomic_action, player):
                return False
        # illegal plunder action
        elif atomic_action[0] == "plunder":
            if not _is_plunder_action_legal(atomic_action, player):
                return False
        elif atomic_action[0] != 'wait':
            return False
    # check mutex action
    if _is_action_mutex(action):
        return False
    return True
