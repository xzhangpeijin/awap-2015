import networkx as nx
import random
from base_player import BasePlayer
from settings import *

class Player(BasePlayer):
    build_cost = INIT_BUILD_COST
    stat_sel = []
    stations = []
    
    def should_build(self, time, money):
        if time > GAME_LENGTH / 2:
            return False
        return len(self.stations) < HUBS and money >= self.build_cost and len(self.stat_sel) > 0

    def __init__(self, state):
        graph = state.get_graph()
        for node in graph.nodes():
            self.stat_sel.extend([node] * len(graph.neighbors(node)))
        return

    # Checks if we can use a given path
    def path_is_valid(self, state, path):
        graph = state.get_graph()
        for i in range(0, len(path) - 1):
            if path[i + 1] not in graph.edge[path[i]] or graph.edge[path[i]][path[i + 1]]['in_use']:
                return False
        return True

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
        
        if self.should_build(state.get_time(), state.get_money()):
            station = random.choice(self.stat_sel)
            filter(lambda x: x != station and x not in graph.neighbors(station), self.stat_sel)
            self.build_cost = self.build_cost * BUILD_FACTOR
            self.stations.append(station)
            commands.append(self.build_command(station))
        
        pending_orders = state.get_pending_orders()
        while True:
            shortest_order, shortest_path = None, None
            for order in pending_orders:
                for station in self.stations:
                    try:
                        path = nx.shortest_path(graph, station, order.get_node())
                        if shortest_path == None or len(path) < len(shortest_path):
                            shortest_order, shortest_path = order, path
                    except:
                        pass
            if shortest_path == None:
                break
            else:
                pending_orders.remove(order)
                if (self.path_is_valid(state, shortest_path)):
                    commands.append(self.send_command(order, shortest_path))
                    pairs = [(shortest_path[i], shortest_path[i+1]) for i in range(len(shortest_path)-1)]
                    graph.remove_edges_from(pairs)
                    
        return commands
