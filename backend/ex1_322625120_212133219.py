import search_322625120_212133219
import random
import math
from search_322625120_212133219 import Node
from itertools import product
import copy

ids = ["212133219", "322625120"]


class OnePieceProblem(search_322625120_212133219.Problem):
    """This class implements a medical problem according to problem description file"""

    def __init__(self, initial):
        """Don't forget to implement the goal test
        You should change the initial to your own representation.
        search.Problem.__init__(self, initial) creates the root node"""
        # state representation
        # state=(pirate_ship_info_tuple,
        #       marine_ship_info_tuple,
        #       collected_treasure_tuple,
        #       deposited_treasure_tuple,
        #       num_collected_per_ship
        #       )

        self.map = initial["map"]
        self.pirate_ships = initial["pirate_ships"]  # dict
        self.treasures = initial["treasures"]  # dict
        for pirate_name,pirate_coordinates in self.pirate_ships.items():
            self.base_coordinates=pirate_coordinates
            break
        self.marine_ships_looped = self.marine_ships_paths_looped(initial["marine_ships"])  # dict
        self.treasures_num = len(self.treasures)
        self.biggest_md = len(self.map) + len(self.map[0])

        # Convert pirate_ships dictionary to tuple of tuples
        pirate_ships_tuple = ()
        for key, value in self.pirate_ships.items():
            tuple_per_ship = (key, value)
            pirate_ships_tuple += (tuple_per_ship,)

        # Convert marine_ships dictionary to tuple of tuples
        marine_ships_tuple = ()
        for key, value in self.marine_ships_looped.items():
            tuple_per_marine = (key, value[0])
            marine_ships_tuple += (tuple_per_marine,)

        # Create an empty tuple for collected_treasures_tuple
        collected_treasures_list = ()

        # Create an empty tuple for deposited_treasures_tuple
        deposited_treasures_list = ()

        # Create an empty tuple for num_collected_per_ship
        num_collected_per_ship = ()

        initial_state_tuple = (pirate_ships_tuple,
                               marine_ships_tuple,
                               collected_treasures_list,
                               deposited_treasures_list,
                               num_collected_per_ship)
        self.root = Node(state=initial_state_tuple)

        search_322625120_212133219.Problem.__init__(self, initial_state_tuple)

    def actions(self, state, depth):
        """Returns all the actions that can be executed in the given
        state. The result should be a tuple (or other iterable) of actions
        as defined in the problem description file"""

        actions_dict = {}
        pirate_ships_tuple = state[0]
        # example: pirate_ships_tuple = ( ('pirate_ship_1',(0,2)), ('pirate_ship_2',(1,1)), )

        for item in pirate_ships_tuple:
            actions_per_ship_list = []
            ship_name = item[0]
            x = item[1][0]
            y = item[1][1]
            marine_ship_next_loc_list = self.marine_ships_loc(depth + 1)
            collected_per_ship_tuple = self.get_ship_num_collected(ship_name, state[4])
            ship_has_treasure = len(collected_per_ship_tuple) > 0

            # TODO instead of marine_ship_exist we can calculate the location on the marine in depth+1 and check if the collide
            # sail
            # need to avoid sailing into islands and avoid marine ships if the ship has treasures
            if x > 0:
                if self.map[x - 1][y] != 'I' and not ((x - 1, y) in marine_ship_next_loc_list and ship_has_treasure):
                    actions_per_ship_list.append(('sail', ship_name, (x - 1, y)))  # up
            if x < len(self.map) - 1:
                if self.map[x + 1][y] != 'I' and not ((x + 1, y) in marine_ship_next_loc_list and ship_has_treasure):
                    actions_per_ship_list.append(('sail', ship_name, (x + 1, y)))  # down
            if y > 0:
                if self.map[x][y - 1] != 'I' and not ((x, y - 1) in marine_ship_next_loc_list and ship_has_treasure):
                    actions_per_ship_list.append(('sail', ship_name, (x, y - 1)))  # left
            if y < len(self.map[0]) - 1:
                if self.map[x][y + 1] != 'I' and not ((x, y + 1) in marine_ship_next_loc_list and ship_has_treasure):
                    actions_per_ship_list.append(('sail', ship_name, (x, y + 1)))  # right

            # collect

            adjacent_treasures = self.find_adjacent_treasure(x, y)
            for adjacent_treasure in adjacent_treasures:
                if len(collected_per_ship_tuple) < 3:
                    if (adjacent_treasure[0] not in state[2]) and (adjacent_treasure[0] not in state[3]):  # if the treasure hasnt been collected or deposited yet
                        if not ((x, y) in marine_ship_next_loc_list):
                            actions_per_ship_list.append(('collect_treasure', ship_name, adjacent_treasure[0]))

            # deposit
            if self.map[x][y] == 'B':
                if len(collected_per_ship_tuple) > 1:
                    actions_per_ship_list.append(('deposit_treasure', ship_name))

            # wait
            # if a marine ship will be in the same x,y as the pirate in the next step and the pirate has treasures we
            # want to avoid waiting in place, so we don't lose our treasure
            if not ((x, y in marine_ship_next_loc_list) and ship_has_treasure):
                actions_per_ship_list.append(('wait', ship_name))

            actions_dict[ship_name] = actions_per_ship_list

        # Convert actions dictionary to a list of lists

        ship_moves_list_of_lists = []
        for key, value in actions_dict.items():
            ship_moves_list_of_lists += [value]

        # Generate all combinations

        all_combinations = tuple(product(*ship_moves_list_of_lists))

        # Filter actions:

        cres = copy.deepcopy(all_combinations)
        count = 0
        for i, action in enumerate(all_combinations):
            move_to_loc = []
            for atomic_action in action:
                if atomic_action[0] == 'sail':
                    if atomic_action[2] not in move_to_loc:
                        move_to_loc.append(atomic_action[2])
                    else:
                        cres = cres[:i - count] + cres[i + 1 - count:]
                        count += 1

        pirate_loc = []
        for pirate_tuple in pirate_ships_tuple:
            pirate_loc = [(pirate_tuple[0], pirate_tuple[1])]

        ccres = copy.deepcopy(cres)
        count = 0
        for i, action in enumerate(cres):
            for atomic_action in action:
                if atomic_action[0] == 'sail':
                    loc = atomic_action[2]
                    for pl in pirate_loc:
                        if loc in pl:
                            name = pl[0]
                            for atomic_act in action:
                                if name in atomic_act and atomic_act[0] != 'sail':
                                    ccres = ccres[:i - count] + ccres[i + 1 - count:]
                                    count += 1

        return tuple(all_combinations)

    def result(self, state, action, depth):
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""

        # action is in format ( ('sail','pirate_ship_1', (0,2) ), ('wait','pirate_ship_2'), )
        new_pirate_ship_list = []  # will be converted later into tuple of tuples

        new_state_0 = ()
        new_state_2 = state[2]
        new_state_3 = state[3]
        new_state_4 = state[4]

        for action_per_ship in action:
            action_name = action_per_ship[0]
            ship_name = action_per_ship[1]
            collected_per_ship_tuple = self.get_ship_num_collected(ship_name, state[4])

            # sail
            if action_name == 'sail':
                new_pirate_ship_info_tuple = (ship_name, action_per_ship[2])
                new_state_0 += (new_pirate_ship_info_tuple,)

            # collect
            # will update new_state_2 to include the treasure and new_state_4 to include the treasure in the ship tuple
            if action_name == 'collect_treasure':
                treasure_name = action_per_ship[2]
                new_state_2 += (treasure_name,)

                if len(collected_per_ship_tuple) == 0:
                    collected_per_ship_tuple = (ship_name, treasure_name)
                    new_state_4 = self.update_tuple_of_tuples(new_state_4, collected_per_ship_tuple, "add")
                else:
                    new_state_4 = self.update_tuple_of_tuples(new_state_4, collected_per_ship_tuple, "remove")
                    collected_per_ship_tuple += (treasure_name,)
                    new_state_4 = self.update_tuple_of_tuples(new_state_4, collected_per_ship_tuple, "add")

            # deposit
            # will update new_state_4 to remove the treasures the ship has collected
            # will update new_state_3 to include the deposited treasure
            # will update new_state_2 to remove treasure from collected list (((((((((((((((((((?))))))))))))))))))))))
            if action_name == 'deposit_treasure':
                new_state_4 = self.update_tuple_of_tuples(new_state_4, collected_per_ship_tuple, "remove")

                # remove treasure from collected treasures
                temp_new_state_2 = ()
                num_collected = len(collected_per_ship_tuple) - 1
                for collected_treasure in new_state_2:
                    if len(collected_per_ship_tuple) == 3:
                        if collected_treasure != (collected_per_ship_tuple[1]) and collected_treasure != (
                                collected_per_ship_tuple[2]):
                            temp_new_state_2 += ((collected_treasure),)
                        elif num_collected == 0:
                            temp_new_state_2 += ((collected_treasure),)
                        else:
                            num_collected -= 1

                    else:
                        if collected_treasure != (collected_per_ship_tuple[1]):
                            temp_new_state_2 += ((collected_treasure),)
                        elif num_collected == 0:
                            temp_new_state_2 += ((collected_treasure),)
                        else:
                            num_collected -= 1

                new_state_2 = temp_new_state_2

                # add treasures to deposited treasures
                for i in range(1, len(collected_per_ship_tuple)):
                    new_state_3 += ((collected_per_ship_tuple[i]),)

            for pirate_ship_info in state[0]:
                if action_name != "sail" and pirate_ship_info[0] == ship_name:
                    new_state_0 += (pirate_ship_info,)

        # if a treasure is collected we remove it from the list of overall treasure and keep it in collected tuple only
        # if a treasure is deposited we remove it from the list of overall treasures and keep it in deposited treasure
        # if marine ship take the treasures add to overall treasures again
        # the game stops if the num of deposited=num of overall

        # check if a marine caught one of the pirate ships and took its treasures
        #    for pirate_ship_tuple in new_state_0:
        #       ship_name = pirate_ship_tuple[0]
        #       x = pirate_ship_tuple[1][0]
        #       y = pirate_ship_tuple[1][1]
        #      if self.marine_ship_exists(x, y, depth):
        #          # remove the treasures the ship has collected from new_state[3]
        #
        # remove the tuple_per_ship from state[4]
        #          tuple_per_ship = self.get_ship_num_collected(ship_name, new_state_4)
        #          if len(tuple_per_ship) > 0:
        #              new_state_4 = self.update_tuple_of_tuples(new_state_4, tuple_per_ship, "remove")

        # moving marine ship by one
        new_state_1 = ()
        for marine_ship_name, marine_ship_path in self.marine_ships_looped.items():  #
            new_state_1 += ((marine_ship_name, marine_ship_path[depth % len(marine_ship_path)]),)

        new_state = (new_state_0,
                     new_state_1,
                     new_state_2,
                     new_state_3,
                     new_state_4)

        return new_state

    def goal_test(self, state):
        """ Given a state, checks if this is the goal state.
         Returns True if it is, False otherwise."""
        count_unique_treasures = len(set(state[3]))
        if self.treasures_num == count_unique_treasures:
            return True
        return False

    def h(self, node):
        """ This is the heuristic. It gets a node (not a state,
        state can be accessed via node.state)
        and returns a goal distance estimate"""
        if self.goal_test(node.state):
            return 0

        hue = self.h_222(node)+ self.h_1(node)
        return hue

    def h_1(self, node):
        """number of uncollected treasures divided by the number of pirates."""
        state = node.state
        collected_num = self.count_unique_items(state[2])
        deposited_num = self.count_unique_items(state[3])
        uncollected_num = self.treasures_num - collected_num - deposited_num
        pirates_num = (len(self.pirate_ships))
        return uncollected_num / pirates_num

    def h_222(self, node):
        """
               Sum of the distances from the pirate base to the closest sea cell adjacent to a treasure
               for each treasure, divided by the number of pirates.
               If there is a treasure which all the adjacent cells are islands, return infinity.
               """

        state = node.state
        total_distance = 0
        num_pirates = len(state[0])  # Number of pirates
        pirate_ships_info_tuple = state[0]
        deposited_treasure = state[3]
        collected_treasure = state[2]
        collected_per_ship_tuple = state[4]
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        # iterate over collected treasures and calculate distance from the ship the the base
        for item in collected_per_ship_tuple:
            distance = float('inf')
            ship_name = item[0]
            for pirate_ship_info in pirate_ships_info_tuple:  # ('pirate_ship_1',(1,0))
                if pirate_ship_info[0] == ship_name:
                    distance_from_base = self.manhattan_distance(pirate_ship_info[1], self.base_coordinates)
                    distance = min(distance, distance_from_base)
            if (len(collected_per_ship_tuple) == 3):
                total_distance += distance * 2
            else:
                total_distance += distance

        # TODO do the same for uncollected_treasures
        # find uncollected treasure
        uncollected = copy.deepcopy(self.treasures)
        for treasure in collected_treasure:
            if treasure in uncollected:
                del uncollected[treasure]
        for treasure in deposited_treasure:
            if treasure in uncollected:
                del uncollected[treasure]

        for treasure, treasure_coordinates in uncollected.items():
            treasure_x, treasure_y = treasure_coordinates[0], treasure_coordinates[1]
            distance = float('inf')  # If there is a treasure which all the adjacent cells are islands, return infinity
            # Check adjacent cells to the treasure
            for dx, dy in directions:
                x, y = treasure_x + dx, treasure_y + dy  # cell adjacent to a treasure
                # check boundaries and if the cell is sea cell.
                if 0 <= x < len(self.map) and 0 <= y < len(self.map[0]) and self.map[x][y] == 'S':
                    distance_from_base = self.manhattan_distance(self.base_coordinates, (x, y))
                    distance = min(distance, distance_from_base)

            if distance == float('inf'):
                return float('inf')  # If all adjacent cells are islands, return infinity
            else:
                total_distance += distance

        return total_distance / num_pirates


    def h_2(self, node):
        """
               Sum of the distances from the pirate base to the closest sea cell adjacent to a treasure
               for each treasure, divided by the number of pirates.
               If there is a treasure which all the adjacent cells are islands, return infinity.
               """
        state = node.state
        total_distance = 0
        num_pirates = len(state[0])  # Number of pirates
        pirate_ships_info_tuple = state[0]
        deposited_treasure = state[3]
        collected_treasure = state[2]
        collected_per_ship_tuple = state[4]
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        for item in collected_per_ship_tuple:
            distance = float('inf')
            ship_name = item[0]
            for pirate_ship_info in pirate_ships_info_tuple:
                if pirate_ship_info[0] == ship_name:
                    treasure_x, treasure_y = pirate_ship_info[1][0], pirate_ship_info[1][1]
                    # Check adjacent cells to the treasure
            for dx, dy in directions:
                x, y = treasure_x + dx, treasure_y + dy  # cell adjacent to a treasure
                if 0 <= x < len(self.map) and 0 <= y < len(self.map[0]) and self.map[x][y] == 'S':
                    distance_from_base = self.manhattan_distance(self.base_coordinates, (x, y))
                    distance = min(distance, distance_from_base)
            if (len(collected_per_ship_tuple) == 3):
                total_distance += distance * 2
            else:
                total_distance += distance

        # find uncollected treasure
        uncollected = copy.deepcopy(self.treasures)
        for treasure in collected_treasure:
            if treasure in uncollected:
                del uncollected[treasure]
        for treasure in deposited_treasure:
            if treasure in uncollected:
                del uncollected[treasure]

        for treasure, treasure_coordinates in uncollected.items():
            treasure_x, treasure_y = treasure_coordinates[0], treasure_coordinates[1]
            distance = float('inf')  # If there is a treasure which all the adjacent cells are islands, return infinity
            # Check adjacent cells to the treasure
            for dx, dy in directions:
                x, y = treasure_x + dx, treasure_y + dy  # cell adjacent to a treasure

                # check boundaries and if the cell is sea cell.
                if 0 <= x < len(self.map) and 0 <= y < len(self.map[0]) and self.map[x][y] == 'S':
                    distance_from_base = self.manhattan_distance(self.base_coordinates, (x, y))
                    distance = min(distance, distance_from_base)

            if distance == float('inf'):
                return float('inf')  # If all adjacent cells are islands, return infinity
            else:
                total_distance += distance
        return total_distance / num_pirates

    """Feel free to add your own functions
    (-2, -2, None) means there was a timeout"""

    def count_unique_items(self, tup):
        unique_items = {}  # Dictionary to store unique items as keys and their counts as values
        for item in tup:
            if item in unique_items:
                unique_items[item] += 1
            else:
                unique_items[item] = 1
        return len(unique_items)

    def update_tuple_of_tuples(self, tuple_of_tuples, tuple_per_ship, add_or_remove):
        """
        given tuple_of_tuples and tuple_per_ship it updates the tuple_of_tuples by replacing the old corresponding
        tuple for the ship with tuple_per_ship by creating a new tuple_of_tuples
        """
        if add_or_remove == "add":
            new_tuple_of_tuples = ()
            if len(tuple_of_tuples) == 0:
                new_tuple_of_tuples += ((tuple_per_ship),)
                return new_tuple_of_tuples
            for item in tuple_of_tuples:
                if item[0] == tuple_per_ship[0]:
                    new_tuple_of_tuples += (tuple_per_ship,)
                else:
                    new_tuple_of_tuples += ((item),)
            return new_tuple_of_tuples
        else:
            new_tuple_of_tuples = ()
            for item in tuple_of_tuples:
                if item[0] != tuple_per_ship[0]:
                    new_tuple_of_tuples += (tuple_per_ship,)
            return new_tuple_of_tuples



    def get_ship_num_collected(self, ship_name, tuple_of_tuples):
        """
        given a ship_name and a tuple_of_tuples in the format ( ('pirate_ship_1', 1,0) ,('pirate_ship_1', 1,0) )
        it returns the corresponding tuple for ship_name
        """
        for tuple in tuple_of_tuples:
            if tuple[0] == ship_name:
                return tuple
        return ()

    def find_adjacent_treasure(self, x, y):
        """
        given a ship_coordinate (x,y), return a tuple ofadjacent treasure coordinates if they exist
        """
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        adjacent_treasures = ()
        for treasure in self.treasures.items():
            if x + directions[0][0] == treasure[1][0] and y + directions[0][1] == treasure[1][1]:
                adjacent_treasures += (treasure,)
            if x + directions[1][0] == treasure[1][0] and y + directions[1][1] == treasure[1][1]:
                adjacent_treasures += (treasure,)
            if x + directions[2][0] == treasure[1][0] and y + directions[2][1] == treasure[1][1]:
                adjacent_treasures += (treasure,)
            if x + directions[3][0] == treasure[1][0] and y + directions[3][1] == treasure[1][1]:
                adjacent_treasures += (treasure,)

        return adjacent_treasures


    def marine_ships_paths_looped(self, marine_paths_dict):
        """
        give a dictionary of the marine_name and a list of marine path, returns a dictionary with the marine ship paths looped
        """
        looped_paths_dict = {}
        for ship, coordinates in marine_paths_dict.items():
            looped_paths = self.create_loop(coordinates)
            looped_paths_dict[ship] = looped_paths
        return looped_paths_dict

    def create_loop(self, coordinates):
        if not coordinates:
            return coordinates
        reversed_coordinates = coordinates[::-1]
        coordinates.extend(reversed_coordinates[1:])
        return coordinates


    def marine_ships_loc(self, depth):
        """ given the depth of the node, it returns a list of each ship's location in the depth"""
        marine_ships_loc_list = []
        for marine_ship, marine_path in self.marine_ships_looped.items():
            marine_ships_loc_list.append(marine_path[depth % len(marine_path)])
        return marine_ships_loc_list


    def manhattan_distance(self, location1, location2):

        return abs(location1[0] - location2[0]) + abs(location1[1] - location2[1])


def create_onepiece_problem(game):
    return OnePieceProblem(game)
