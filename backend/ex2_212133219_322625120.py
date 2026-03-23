import itertools
import math
from copy import deepcopy
import numpy as np

ids = ["212133219", "322625120"]


def reward_function(state, action_combination, initial_state):
    reward = 0
    if action_combination == 'reset':
        return -2

    for atomic_action in action_combination:
        action_name = atomic_action[0]
        pirate_ship_name = atomic_action[1]
        ship_capacity = state["pirate_ships"][pirate_ship_name]["capacity"]
        if action_name == "deposit":
            reward += ((2 - ship_capacity) * 4)

    for pirate_ship_name, pirate_ship_info in state["pirate_ships"].items():
        reward += collision_with_marines_penalty(pirate_ship_info["location"], state["marine_ships"],
                                                 initial_state)
    return reward


def collision_with_marines_penalty(pirate_position, marines_info, initial_state):
    marine_locations = []
    for marine_name, marine_index in marines_info.items():
        marine_locations.append(initial_state["marine_ships"][marine_name]["path"][marine_index])
    if pirate_position in marine_locations:
        return -1
    return 0


def dict_to_tuple(d):
    if isinstance(d, dict):
        # Sort the dictionary by key to ensure consistent ordering, then recursively apply this function
        return tuple((key, dict_to_tuple(value)) for key, value in d.items())
    elif isinstance(d, list):
        # Convert lists to tuples
        return tuple(dict_to_tuple(element) for element in d)
    else:
        # No conversion needed for other types (int, str, tuple)
        return d


def tuple_to_dict(t):
    if isinstance(t, tuple) and all(isinstance(item, tuple) and len(item) == 2 for item in t):
        # Input is a tuple of key-value pairs (as produced by dict_to_tuple for dictionaries)
        return {key: tuple_to_dict(value) for key, value in t}
    elif isinstance(t, tuple):
        # Input is a tuple representing a list (as produced by dict_to_tuple for lists)
        return [tuple_to_dict(element) for element in t]
    else:
        # No conversion needed for other types (int, str, directly nested tuples from original)
        return t


def simplify_state(complete_state):
    new_treasures_dict = {}
    for treasure_name, treasure_info in complete_state["treasures"].items():
        new_treasures_dict[treasure_name] = treasure_info["location"]
    new_marines_dict = {}
    for marine_name, marine_info in complete_state["marine_ships"].items():
        new_marines_dict[marine_name] = marine_info["index"]

    simplified_state = {
        "pirate_ships": complete_state["pirate_ships"],
        "treasures": new_treasures_dict,
        "marine_ships": new_marines_dict
    }
    return simplified_state


def manhattan_distance(location1, location2):
    return abs(location1[0] - location2[0]) + abs(location1[1] - location2[1])


def get_all_states(initial):
    matrix = initial["map"]
    possible_locs = []
    n = len(matrix)
    m = len(matrix[0])
    for i in range(n):
        for j in range(m):
            if matrix[i][j] != 'I':
                possible_locs.append((i, j))

    # pirates
    pirates = []  # [('pirate_1',2)]
    for pirate_name, pirate_info in initial["pirate_ships"].items():
        pirates.append((pirate_name, pirate_info["capacity"]))
    possible_pirates_loc_and_capacity = []  # list in format [ [ ('pirate_1',2,(x1,y1)),('pirate_1',2,(x2,y2)) ] ]
    for pirate_tuples in pirates:
        list_per_pirate = []
        for capacity in range(pirate_tuples[1] + 1):
            for loc in possible_locs:
                list_per_pirate.append((pirate_tuples[0], capacity, loc))
        possible_pirates_loc_and_capacity.append(list_per_pirate)

    # treasures
    comb_treasures = []  # [ [ ('treasure_1',(x1,y1)), ('treasure_1',(x2,y2)) ] ]

    for treasure_name, treasure_info in initial["treasures"].items():
        list_per_treasure = []
        if treasure_info["prob_change_location"] > 0:
            for loc in treasure_info["possible_locations"]:
                list_per_treasure.append((treasure_name, loc))

        else:
            list_per_treasure.append((treasure_name, treasure_info["location"]))
        comb_treasures.append(list_per_treasure)

    # marine
    comb_marines = []  # [ [ ('marine1',(1,1)),('marine1',(2,2)) ] ]
    for marine_name, marine_info in initial["marine_ships"].items():
        list_per_marine = []
        for i in range(len(marine_info["path"])):
            list_per_marine.append((marine_name, i))
        comb_marines.append(list_per_marine)

    pirates_states = itertools.product(
        *possible_pirates_loc_and_capacity)
    treasures_states = itertools.product(*comb_treasures)
    marine_states = itertools.product(*comb_marines)

    all_states_list_of_tuple = list(itertools.product(pirates_states, treasures_states, marine_states))
    all_states = []
    # convert to dictionaries
    for all_states_list_of_tuple in all_states_list_of_tuple:
        pirates_tuple = all_states_list_of_tuple[0]
        treasures_tuple = all_states_list_of_tuple[1]
        marines_tuple = all_states_list_of_tuple[2]
        pirates_dict = {}
        treasures_dict = {}
        marines_dict = {}

        for pirate in pirates_tuple:
            pirate_dict_info = {
                "location": pirate[2],
                "capacity": pirate[1]
            }
            pirates_dict[pirate[0]] = pirate_dict_info

        for treasure in treasures_tuple:
            treasures_dict[treasure[0]] = treasure[1]
        for marine in marines_tuple:
            marines_dict[marine[0]] = marine[1]

        state = {
            "pirate_ships": pirates_dict,
            "treasures": treasures_dict,
            "marine_ships": marines_dict
        }
        all_states.append(state)
    return all_states


def get_possible_actions_combinations(state, initial_state, base_coordinates, initial_capacity_per_ship):
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # right, left, down, up

    possible_actions_dict = {}  # {'ship_1':[(sail,ship1,x,y), (wait,ship1)]}
    for pirate_ship_name, pirate_ship_info in state["pirate_ships"].items():
        actions_per_ship_list = []
        pirate_ship_loc = pirate_ship_info["location"]
        pirate_ship_capacity = pirate_ship_info["capacity"]

        # wait
        actions_per_ship_list.append(("wait", pirate_ship_name))
        possible_actions_dict[pirate_ship_name] = actions_per_ship_list

        # sail
        for direction in directions:
            next_location = (pirate_ship_loc[0] + direction[0], pirate_ship_loc[1] + direction[1])
            if is_valid_location(next_location, initial_state):
                actions_per_ship_list.append(("sail", pirate_ship_name, next_location))
        # collect
        adjacent_treasures = find_adjacent_treasures(pirate_ship_loc, state)

        for treasure in adjacent_treasures:
            if pirate_ship_capacity > 0:
                actions_per_ship_list.append(("collect", pirate_ship_name, treasure))

        # deposit
        if pirate_ship_capacity != initial_capacity_per_ship[pirate_ship_name] and pirate_ship_loc == base_coordinates:
            actions_per_ship_list.append(("deposit", pirate_ship_name))

    all_ships_actions = list(possible_actions_dict.values())

    combined_possible_actions_list = list(itertools.product(*all_ships_actions))
    combined_possible_actions_list.append("reset")
    # combined_possible_actions_list.append("terminate")

    return combined_possible_actions_list


def find_adjacent_treasures(current_location, current_state):
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # right, left, down, up
    treasures = current_state["treasures"]
    adjacent_treasures = []
    for direction in directions:
        next_location = (current_location[0] + direction[0], current_location[1] + direction[1])
        for treasure_name, treasure_loc in treasures.items():
            if treasure_loc == next_location:
                adjacent_treasures.append(treasure_name)
    return adjacent_treasures


def is_valid_location(location, initial_state):
    matrix = initial_state["map"]
    rows = len(matrix)
    cols = len(matrix[0])
    row, col = location
    return 0 <= row < rows and 0 <= col < cols and matrix[row][col] != 'I'


def get_possible_next_states(state, action_combination, initial_state):  # state in dictionary form

    new_pirate_ships_info = apply_action(state["pirate_ships"], action_combination,
                                         initial_state)
    # convert dictionary to list of tuples
    pirates_list_of_tuples = []
    for pirate_name, pirate_info in new_pirate_ships_info.items():
        pirates_list_of_tuples.append([(pirate_name, pirate_info["capacity"], pirate_info["location"])], )

    # treasures
    comb_treasures = []  # [ [ ('treasure_1',(x1,y1)), ('treasure_1',(x2,y2)) ] ]
    for treasure_name, treasure_info in initial_state["treasures"].items():
        list_per_treasure = []
        if treasure_info["prob_change_location"] > 0:
            for loc in treasure_info["possible_locations"]:
                list_per_treasure.append((treasure_name, loc))

        else:
            list_per_treasure.append((treasure_name, treasure_info["location"]))
        comb_treasures.append(list_per_treasure)

    # move marines
    comb_marines = []  # [ [ ('marine1',(1,1)),('marine1',(2,2)) ] ]
    for marine_name, marine_index in state["marine_ships"].items():
        list_per_marine = []
        len_path = len(initial_state["marine_ships"][marine_name]["path"])
        if marine_index == 0:
            list_per_marine.append((marine_name, marine_index))
            if len_path >= 2:
                list_per_marine.append((marine_name, marine_index + 1))
        elif marine_index == len_path - 1:
            list_per_marine.append((marine_name, marine_index))
            if len_path >= 2:
                list_per_marine.append((marine_name, marine_index - 1))
        else:
            list_per_marine.append((marine_name, marine_index))
            list_per_marine.append((marine_name, marine_index - 1))
            list_per_marine.append((marine_name, marine_index + 1))
        comb_marines.append(list_per_marine)

    # example: [ (['pirate_1', 2, (1, 2)], ['pirate_2', 2, (5, 6)]), (['pirate_1', 2, (1, 2)], ['pirate_2', 2, (7, 8)]),
    pirates_states = itertools.product(*pirates_list_of_tuples)
    treasures_states = itertools.product(*comb_treasures)
    marine_states = itertools.product(*comb_marines)

    all_possible_next_states = list(itertools.product(pirates_states, treasures_states, marine_states))
    all_possible_next_states_list = []
    for all_states_list_of_tuple in all_possible_next_states:
        pirates_tuple = all_states_list_of_tuple[0]
        treasures_tuple = all_states_list_of_tuple[1]
        marines_tuple = all_states_list_of_tuple[2]
        pirates_dict = {}
        treasures_dict = {}
        marines_dict = {}

        for treasure in treasures_tuple:
            treasures_dict[treasure[0]] = treasure[1]
        for marine in marines_tuple:
            marines_dict[marine[0]] = marine[1]

        for pirate in pirates_tuple:
            capacity = pirate[1]
            if collision_with_marines_penalty(pirate[2], marines_dict, initial_state) == -1:
                capacity = 2
            pirate_dict_info = {
                "location": pirate[2],
                "capacity": capacity
            }
            pirates_dict[pirate[0]] = pirate_dict_info
        # if pirate encounters a marine, capacity =2

        state = {
            "pirate_ships": pirates_dict,
            "treasures": treasures_dict,
            "marine_ships": marines_dict
        }
        all_possible_next_states_list.append(state)

    return all_possible_next_states_list  # returns list of dictionaries


def apply_action(pirates_info, action_combination, initial_state):
    new_pirates_info = deepcopy(pirates_info)
    if action_combination == "reset":  # or action_combination == "terminate":
        new_pirates_info = simplify_state(initial_state)["pirate_ships"]
        return new_pirates_info
    for i, action in enumerate(action_combination):
        pirate_ship_name = action[1]
        if action[0] == 'sail':
            new_pirates_info[pirate_ship_name]["location"] = action[2]
        if action[0] == 'collect':
            new_pirates_info[pirate_ship_name]['capacity'] -= 1
        elif action[0] == 'deposit':
            new_pirates_info[pirate_ship_name]['capacity'] = 2

    return new_pirates_info


def probability_function(state, action_combination, next_state, initial_state):
    """
    function that calculates P(s,a,s') , returns the probability of transitioning
    from state to next state by action combination
     """
    # check if action for state leads to next state : state+action=next_state
    # if action_combination == 'terminate':
    #     return 0
    if not check_pirates_loc(state, action_combination, next_state, initial_state) :
        return 0
    probability_treasure = 1
    for treasure_name, treasure_loc in state["treasures"].items():
        prob_change = initial_state["treasures"][treasure_name]["prob_change_location"]
        possible_locations_num = len(initial_state["treasures"][treasure_name]["possible_locations"])
        if possible_locations_num == 1:
            probability_treasure *= 1

        elif treasure_loc == next_state["treasures"][treasure_name]:  # if the treasure didn't move
            probability_treasure *= ((1 - prob_change) + (prob_change / possible_locations_num))
        else:
            probability_treasure *= (prob_change / (possible_locations_num))

    probability_marine = 1
    for marine_name, marine_index in state["marine_ships"].items():
        path_len = len(initial_state["marine_ships"][marine_name]["path"])
        if path_len == 1:
            probability_marine *= 1

        else:
            index_in_next_state = next_state["marine_ships"][marine_name]
            probability_marine *= (calculate_marine_probability(marine_index, index_in_next_state, path_len))

    total_probability = probability_treasure * probability_marine

    return total_probability


def calculate_marine_probability(current_index, next_index, path_length):
    # Calculate number of possible actions based on the marine's position
    if current_index == 0 or current_index == path_length - 1:
        # At the beginning or end of the path, can only move in one direction or stay
        possible_actions = 2
    else:
        # Anywhere else on the path, can move forward, backward, or stay
        possible_actions = 3

    # Check if the next state is a valid move or staying in place
    if next_index == current_index or next_index == current_index + 1 or next_index == current_index - 1:
        # The move is valid (stay, forward, or backward within path bounds)
        return 1 / possible_actions
    else:
        # The move is not valid (e.g., jumping positions without adjacency)
        return 0


def check_pirates_loc(state, action_combination, next_state, initial_state):
    if action_combination == "reset":
        for pirate_name, pirate_info in next_state["pirate_ships"].items():
            if pirate_info["location"] != initial_state["pirate_ships"][pirate_name]["location"]:
                return False
    else:
        for atomic_action in action_combination:
            action_name = atomic_action[0]
            ship_name = atomic_action[1]
            if action_name == "sail":
                loc = atomic_action[2]
                if next_state["pirate_ships"][ship_name]["location"] != loc:
                    return False
            if action_name == "wait":
                if next_state["pirate_ships"][ship_name]["location"] != state["pirate_ships"][ship_name]["location"]:
                    return False

            if action_name == "collect":
                if next_state["pirate_ships"][ship_name]["location"] != state["pirate_ships"][ship_name]["location"] or \
                        next_state["pirate_ships"][ship_name]["capacity"] + 1 != state["pirate_ships"][ship_name]["capacity"]:
                    return False

            if action_name == "deposit":
                if next_state["pirate_ships"][ship_name]["location"] != state["pirate_ships"][ship_name]["location"] or \
                        next_state["pirate_ships"][ship_name]["capacity"] != 2:
                    return False
            if collision_with_marines_penalty(state["pirate_ships"][ship_name]["location"], state["marine_ships"],
                                              initial_state) == -1 and state["pirate_ships"][ship_name]["capacity"] != 2:
                return False
        return True


def max1(value_actions):
    max_value = -math.inf
    max_action = None

    for value, action in value_actions:
        if value >= max_value:
            max_value = value
            max_action = action
    return max_value, max_action
def complete_act(initial, act):
    combined_act = ()
    action_name = act[0][0]

    for pirate_name, pirate_dict in initial["pirate_ships"].items():
        new_act = (action_name, pirate_name)
        if len(act[0]) > 2:
            new_act += (act[0][2],)
        combined_act += (new_act,)
    return combined_act

class OptimalPirateAgent:

    def __init__(self, initial):
        self.initial = initial
        self.num_pirates = len(initial["pirate_ships"])
        self.smaller_initial=deepcopy(initial)
        if self.num_pirates > 1:
            self.smaller_initial["pirate_ships"]={}
            for pirate_name, pirate_info in initial["pirate_ships"].items():
                self.smaller_initial["pirate_ships"] = {pirate_name: pirate_info}
                break
        self.simplified_initial = simplify_state(self.smaller_initial)
        self.rows = len(self.initial["map"])
        self.cols = len(self.initial["map"][0])
        self.map = initial["map"]

        self.base_coordinates = (0, 0)
        for i in range(self.rows):
            for j in range(self.cols):
                if self.map[i][j] == 'B':
                    self.base_coordinates = (i, j)

        self.treasures_info = initial["treasures"]
        self.num_treasures = len(self.treasures_info)

        self.marines_info = initial["marine_ships"]
        self.num_marines = len(self.marines_info)

        self.initial_capacity_per_ship = {}
        for pirate_ship, pirate_ship_info in self.smaller_initial["pirate_ships"].items():
            self.initial_capacity_per_ship[pirate_ship] = pirate_ship_info["capacity"]

        self.all_states = get_all_states(self.smaller_initial)  # list of  dictionaries
        self.optimal_values = {t: {dict_to_tuple(state): 0 for state in self.all_states} for t in
                               range(1, self.initial["turns to go"] + 1)}
        self.optimal_policies = {t: {dict_to_tuple(state): 0 for state in self.all_states} for t in
                                 range(1, self.initial["turns to go"] + 1)}

        self.actions_per_state = {}  # {state:[actions]}
        self.transition_model = {}  # P(s,a,s')
        self.next_states_per_state_and_action = {}  # {(state,action):[next_states]}
        self.initialize()
        self.value_iteration()

    def initialize(self):


        # defining actions per state:
        for state in self.all_states:
            state_tuple = dict_to_tuple(state)
            self.actions_per_state[state_tuple] = get_possible_actions_combinations(state, self.smaller_initial,
                                                                                    self.base_coordinates,
                                                                                    self.initial_capacity_per_ship)

        # defining next states per action and state:
        for state in self.all_states:
            state_tuple = dict_to_tuple(state)
            for action_combination in self.actions_per_state[state_tuple]:
                possible_next_states = get_possible_next_states(state, action_combination, self.smaller_initial)
                self.next_states_per_state_and_action[(state_tuple, action_combination)] = possible_next_states

        # define transition model
        for state in self.all_states:
            state_tuple = dict_to_tuple(state)
            for action_combination in self.actions_per_state[state_tuple]:
                for next_state in self.next_states_per_state_and_action[(state_tuple, action_combination)]:
                    next_state_tuple = dict_to_tuple(next_state)
                    probability = probability_function(state, action_combination, next_state, self.smaller_initial)
                    self.transition_model[(state_tuple, action_combination, next_state_tuple)] = probability

    def value_iteration(self):
        horizon = self.initial["turns to go"]
        for t in range(1, horizon + 1):

            new_values = self.optimal_values.copy()
            for state in self.all_states:
                value_actions = []
                state_tuple = dict_to_tuple(state)
                for action_combination in self.actions_per_state[state_tuple]:
                    action_value = reward_function(state, action_combination, self.smaller_initial)
                    if t > 1:
                        for next_state in self.next_states_per_state_and_action[(state_tuple, action_combination)]:
                            next_state_tuple = dict_to_tuple(next_state)
                            transition = self.transition_model[
                                (state_tuple, action_combination, next_state_tuple)]
                            v_for_next_state = self.optimal_values[t - 1][next_state_tuple]
                            sum = (transition * v_for_next_state)
                            action_value += sum

                    value_actions.append((action_value, action_combination))
                # Choose the action with the highest value
                max_value, best_action = max1(value_actions)
                new_values[t][state_tuple] = max_value

                if max_value<0:
                    self.optimal_policies[t][state_tuple] = "terminate"
                else:
                    self.optimal_policies[t][state_tuple] = best_action
            self.optimal_values = new_values

    def act(self, state):
        t = state["turns to go"]
        for pirate_name, pirate_info in state["pirate_ships"].items():
            state["pirate_ships"] = {}
            state["pirate_ships"] = {pirate_name: pirate_info}
            break
        simplified_state = simplify_state(state)
        state_tuple = dict_to_tuple(simplified_state)
        act = self.optimal_policies[t][state_tuple]
        if act=='terminate' or act=='reset':
            return act
        all_act=complete_act(self.initial,act)
        return all_act


class PirateAgent:
    def __init__(self, initial):
        self.initial = initial
        self.smaller_initial = self.convert_to_smaller_input(initial)
        self.optimalAgent = OptimalPirateAgent(self.smaller_initial)

    def act(self, state):
        smaller_state = self.convert_to_smaller_input(state)
        act = self.optimalAgent.act(smaller_state)
        if act == "terminate" or act == "reset":
            return act
        else:
            return complete_act(self.initial,act)

    def convert_to_smaller_input(self, state):
        smaller_state = deepcopy(state)

        rows = len(state["map"])
        cols = len(state["map"][0])
        map = state["map"]
        num_pirates = len(state["pirate_ships"])

        base_coordinates = (0, 0)
        for i in range(rows):
            for j in range(cols):
                if map[i][j] == 'B':
                    base_coordinates = (i, j)

        marine_len = math.inf
        for marine_name, marine_info in state["marine_ships"].items():
            if len(marine_info["path"]) < marine_len:
                marine_len = len(marine_info["path"])
                marine_with_shortest_path = marine_name
        if marine_len < math.inf:
            smaller_state["marine_ships"] = {
                marine_with_shortest_path: state["marine_ships"][marine_with_shortest_path]
            }
        if num_pirates > 1:
            for pirate_name, pirate_info in state["pirate_ships"].items():
                smaller_state["pirate_ships"] = {pirate_name: pirate_info}
                break
        treasures_and_furthest_loc = {}
        for treasure_name, treasure_info in state["treasures"].items():
            max_distance = -math.inf
            for loc in treasure_info["possible_locations"]:
                distance = manhattan_distance(loc, base_coordinates)
                if distance > max_distance:
                    max_distance = distance
            treasures_and_furthest_loc[treasure_name] = max_distance
        min_of_max = math.inf
        for treasure_name, treasure_distance in treasures_and_furthest_loc.items():
            if treasure_distance < min_of_max:
                min_of_max_treasure = treasure_name
                min_of_max = treasure_distance
        smaller_state["treasures"] = {
            min_of_max_treasure: state["treasures"][min_of_max_treasure]
        }
        return smaller_state




class InfinitePirateAgent:

    def __init__(self, initial, gamma):
        self.initial = initial
        self.gamma = gamma
        self.all_states = get_all_states(initial)
        self.num_states = len(self.all_states)
        self.rows = len(self.initial["map"])
        self.cols = len(self.initial["map"][0])
        self.map = initial["map"]
        self.base_coordinates = (0, 0)
        for i in range(self.rows):
            for j in range(self.cols):
                if self.map[i][j] == 'B':
                    self.base_coordinates = (i, j)

        self.initial_capacity_per_ship = {}
        for pirate_ship, pirate_ship_info in initial["pirate_ships"].items():
            self.initial_capacity_per_ship[pirate_ship] = pirate_ship_info["capacity"]

        self.actions_per_state = {}
        self.transition_probability = {}  # P(s,a,s')
        self.next_states_per_state = {}
        for state in self.all_states:
            state_tuple = dict_to_tuple(state)

            self.actions_per_state[state_tuple] = get_possible_actions_combinations(state, self.initial,
                                                                                    self.base_coordinates,
                                                                                    self.initial_capacity_per_ship)
            for action_combination in self.actions_per_state[state_tuple]:
                possible_next_states = get_possible_next_states(state,
                                                                action_combination,
                                                                self.initial)  # list of dictionaries
                self.next_states_per_state[(state_tuple, action_combination)]=possible_next_states
                for next_possible_state in possible_next_states:
                    next_possible_state_tuple = dict_to_tuple(next_possible_state)
                    probability=probability_function(state, action_combination, next_possible_state, self.initial)
                    self.transition_probability[(state_tuple, action_combination, next_possible_state_tuple)] = probability
        self.optimal_values, self.optimal_policies = self.policy_iteration()

    def act(self, state):
        simplified_state_tuple = dict_to_tuple(simplify_state(state))
        act = self.optimal_policies[simplified_state_tuple]
        act_tuple=()
        for a in act.keys():
            act_tuple+=(a)
        return act_tuple

    def value(self, state):
        simplified_state_tuple = dict_to_tuple(simplify_state(state))
        value = self.optimal_values[simplified_state_tuple]
        return value

    def get_old_action(self, state, policy):
        """
        Retrieve the action with the highest probability under the current policy for state s.

        Args:
            state: The current state.
            policy: Current policy dictionary mapping states to actions.

        Returns:
            The action favored by the current policy or None if no action is defined.
        """
        state_tuple = dict_to_tuple(state)
        if state_tuple in policy:
            # Directly return the action since the policy maps states to their best actions.
            return list(policy[state_tuple].keys())[0]  # Assumes each state maps to one best action
        else:
            # If no policy is defined for the state, return None or consider returning a default action
            return None

    def find_best_action_for_state(self, state, V, policy):
        """
        Find the best action for a given state based on the current value function.

        Args:
            state: The current state.
            policy: Current policy dictionary mapping states to action probabilities.
            V: The current value function.

        Returns:
            The action with the highest expected value under the current policy.
        """
        best_action = None
        max_value = float('-inf')
        state_tuple = dict_to_tuple(state)
        # Iterate over all possible actions in the current state
        actions = self.actions_per_state[state_tuple]
        for a in actions:
            # Calculate the expected value of taking action a in state s
            expected_value = 0
            next_possible_states = self.next_states_per_state[state_tuple, a]
            for next_state in next_possible_states:  # Iterate over all possible next states
                next_state_tuple = dict_to_tuple(next_state)

                transition_prob = self.transition_probability[
                    (state_tuple, a, next_state_tuple)]  # Probability of transitioning to s_prime
                reward = reward_function(state, a, self.initial)  # Reward for transitioning to s_prime
                expected_value += transition_prob * (reward + self.gamma * V[next_state_tuple])

            # Update the best action if this action is better than the current best
            if expected_value > max_value:
                best_action = a
                max_value = expected_value

        return best_action

    def policy_evaluation(self, policy):
        V = {dict_to_tuple(state): 0 for state, actions in self.actions_per_state.items()}
        theta = 0.01
        while True:
            delta = 0
            for state in self.all_states:
                value = 0
                state_tuple = dict_to_tuple(state)
                for action_combination, action_prob in policy[state_tuple].items():
                    for next_state in self.next_states_per_state[(state_tuple, action_combination)]:
                        next_state_tuple = dict_to_tuple(next_state)
                        transition = self.transition_probability[(state_tuple, action_combination, next_state_tuple)]
                        reward = reward_function(state, action_combination, self.initial)
                        value += action_prob * transition * (reward + self.gamma * V[next_state_tuple])
                delta = max(delta, np.abs(value - V[state_tuple]))
                V[state_tuple] = value
            if delta < theta:
                break
        return V

    def policy_improvement(self, V,old_policy):
        new_policy = {}
        policy_stable = True
        for state_tuple, actions in self.actions_per_state.items():
            state = tuple_to_dict(state_tuple)
            old_action = self.get_old_action(state, old_policy)

            # Find the new best action based on the value function V
            new_best_action = self.find_best_action_for_state(state, V, new_policy)

            # Update policy if the new best action is different from the old best action
            if old_action != new_best_action:
                policy_stable = False
                new_policy[state_tuple] = {
                    new_best_action: 1.0}  # Update policy to choose the new best action with probability 1
            elif state_tuple not in new_policy:  # Ensure policy is updated if it was previously undefined for state s
                new_policy[state_tuple] = {new_best_action: 1.0}
        return new_policy, policy_stable

    def policy_iteration(self):
        policy = {dict_to_tuple(state): {a: 1.0 / len(actions) for a in actions} for state, actions in
                  self.actions_per_state.items()}
        while True:
            V = self.policy_evaluation(policy)
            policy, policy_stable = self.policy_improvement(V,policy)
            if policy_stable:
                break
        return V, policy
