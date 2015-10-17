import networkx as nx
import random
from base_player import BasePlayer
from settings import *

class Player(BasePlayer):
    build_cost = INIT_BUILD_COST
    stat_sel = []
    stations = []
    missed_orders = []
    path_length_weight = 2 # used in scoring how good paths are
    time_for_first_build = 15
    
    def should_build(self, time, money):
        if time < self.time_for_first_build or time > GAME_LENGTH / 2:
            return False
        return len(self.stations) < HUBS-1 and money >= self.build_cost and len(self.stat_sel) > 0

    def __init__(self, state):
        self.missed_orders = []
        self.stations = []
        self.stat_sel = []
        graph = state.get_graph()
        for node in graph.nodes():
            if (len(graph.neighbors(node)) >= 2):
                self.stat_sel.extend([node])
        return

    def value_after_dist(self, dist):
        proposed_value = SCORE_MEAN - DECAY_FACTOR * dist
        if proposed_value < 0:
            proposed_value = 0
        return proposed_value

    # Checks if we can use a given path
    def path_is_valid(self, state, path):
        graph = state.get_graph()
        for i in range(0, len(path) - 1):
            if path[i + 1] not in graph.edge[path[i]] or graph.edge[path[i]][path[i + 1]]['in_use']:
                return False
        return True

    def get_best_station(self, graph):
        best_score, best_node = 0, None
        for node in self.stat_sel:
            order_distances = []
            for order in self.missed_orders:
                try:
                    path = nx.shortest_path(graph, node, order.get_node())
                    order_distances.append(len(path))
                except:
                    pass
            order_distances.sort()
            num_neighbors = len(graph.neighbors(node))
            score = sum([1.0/d for d in order_distances[:num_neighbors]])
            if score > best_score:
                best_score = score
                best_node = node
        return best_node

    def get_most_neighbor_station(self, graph):
        max_edges = 0
        for node in self.stat_sel:
            if len(graph.neighbors(node)) > max_edges:
                max_edges = len(graph.neighbors(node))
        vertex_choices = filter(lambda node: len(graph.neighbors(node)) == max_edges, self.stat_sel)
        vertex = random.choice(vertex_choices)
        return vertex

    # lower is better
    def path_score(self, order, path):
        return self.path_length_weight * DECAY_FACTOR * len(path) - order.money

    def step(self, state):
        """
        Determine actions based on the current state of the city. Called every
        time step. This function must take less than Settings.STEP_TIMEOUT
        seconds.
        --- Parameters ---
        state : State
            The state of the game. See state.py for more information.
        --- Returns ---
        commands : dict list
            Each command should be generated via self.send_command or
            self.build_command. The commands are evaluated in order.
        """
        
        graph = state.get_graph()
        commands = []

        for order, path in state.get_active_orders():
            pairs = [(path[i], path[i+1]) for i in range(len(path)-1)]
            graph.remove_edges_from(pairs)
        
        # Decide if we should build a new station
        if self.should_build(state.get_time(), state.get_money()):
            station = self.get_best_station(state.get_graph())
            self.missed_orders = []
            if station != None:
                self.stat_sel = filter(lambda x: x != station and x not in graph.neighbors(station), self.stat_sel)
                self.build_cost = self.build_cost * BUILD_FACTOR
                self.stations.append(station)
                commands.append(self.build_command(station))
        
        pending_orders = state.get_pending_orders()

        # Add pending orders to missed orders
        for order in pending_orders:
            if order.id not in [o.id for o in self.missed_orders]:
                self.missed_orders.append(order)

        while True:
            shortest_order, shortest_path = None, None
            for order in pending_orders:
                for station in self.stations:
                    try:
                        path = nx.shortest_path(graph, station, order.get_node())
                        if shortest_path == None or self.path_score(order, path) < self.path_score(shortest_order, shortest_path):
                            shortest_order, shortest_path = order, path
                    except:
                        pass
            if shortest_path == None:
                break
            elif len(shortest_path) * DECAY_FACTOR >= order.money:
                pending_orders.remove(shortest_order)
            else:
                assert (self.path_is_valid(state, shortest_path))
                commands.append(self.send_command(shortest_order, shortest_path))
                pairs = [(shortest_path[i], shortest_path[i+1]) for i in range(len(shortest_path)-1)]
                graph.remove_edges_from(pairs)
                pending_orders.remove(shortest_order)
                # self.missed_orders.remove(shortest_order)
        return commands
