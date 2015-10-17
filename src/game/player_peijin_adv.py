import networkx as nx
import random
from base_player import BasePlayer
from settings import *

LEARNING_PERIOD = 10

class Player(BasePlayer):
    global LEARNING_PERIOD
    
    build_cost = INIT_BUILD_COST
    candidate_map = dict((n, 0) for n in range(GRAPH_SIZE))
    time_passed = 0
    stations = []
    building = True
    
    def __init__(self, state):
        return

    # Checks if we can use a given path
    def path_is_valid(self, state, path):
        graph = state.get_graph()
        for i in range(0, len(path) - 1):
            if path[i + 1] not in graph.edge[path[i]] or graph.edge[path[i]][path[i + 1]]['in_use']:
                return False
        return True

    def path_score(self, order, path):
        return order.money - DECAY_FACTOR * len(path)

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
        
        self.time_passed = self.time_passed + 1
        
        graph = state.get_graph()
        commands = []
        
        if (state.get_time() > 980):
            print "Max stations:", len(self.stations)
        
        for order, path in state.get_active_orders():
            pairs = [(path[i], path[i+1]) for i in range(len(path)-1)]
            graph.remove_edges_from(pairs)
        
        if self.building and state.get_time() > LEARNING_PERIOD and state.get_money() >= self.build_cost:
            print state.get_time()
            maxnode = max(self.candidate_map, key=self.candidate_map.get)
            remain = GAME_LENGTH - state.get_time()
            print "Expected:", self.candidate_map[maxnode] * remain / self.time_passed
            if self.candidate_map[maxnode] * remain / self.time_passed > self.build_cost:
                self.stations.append(maxnode)
                self.candidate_map = dict((n, 0) for n in 
                    filter(lambda x : x not in self.stations and x not in graph.neighbors(maxnode), range(GRAPH_SIZE)))
                self.time_passed = 0
                self.build_cost = self.build_cost * BUILD_FACTOR
                commands.append(self.build_command(maxnode))
            else:
                self.building = False
                        
        pending_orders = state.get_pending_orders()
        
        for order in pending_orders:
            mpath, mscore = None, 0
            for station in self.stations:
                try:
                    path = nx.shortest_path(graph, station, order.get_node())
                    if mpath == None or self.path_score(order, path) > self.path_score(order, mpath):
                        mpath, mscore = path, self.path_score(order, path)
                except:
                    pass
            for node in self.candidate_map:
                try:
                    path = nx.shortest_path(graph, node, order.get_node())
                    if self.path_score(order, path) > mscore:
                        self.candidate_map[node] = self.candidate_map[node] + self.path_score(order, path) - mscore
                except:
                    pass
        
        while True:
            best_order, best_path, best_score = None, None, 0
            for order in pending_orders:
                for station in self.stations:
                    try:
                        path = nx.shortest_path(graph, station, order.get_node())
                        if best_path == None or self.path_score(order, path) > self.path_score(order, best_path):
                            best_order, best_path, best_score = order, path, self.path_score(order, path)
                    except:
                        pass
                        
            if best_order == None:
                break
            else:
                assert (self.path_is_valid(state, best_path))
                commands.append(self.send_command(best_order, best_path))
                pairs = [(best_path[i], best_path[i+1]) for i in range(len(best_path)-1)]
                graph.remove_edges_from(pairs)
                pending_orders.remove(best_order)                             
                    
        return commands
