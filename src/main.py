from game.game import Game
from server.server import run_server
import sys, json
import math

def print_usage():
    print 'Usage: %s [shell|web]' % sys.argv[0]
    exit(1)

def make_game():
    return Game("game.player")

def mean(array):
    return float(sum(array))/len(array)

def stddev(array):
    ave = mean(array)
    sse = sum((i - ave) ** 2 for i in array)
    dev = math.sqrt(sse / (len(array) - 1))
    return dev / math.sqrt(len(array))

def main():
    if len(sys.argv) == 1: print_usage()

    moneys = []
    command = sys.argv[1]
    if command == 'web':
        run_server(make_game())
    elif command == 'shell':
        num_iterations = 10
        for i in range(num_iterations):
            game = make_game()
            while not game.is_over():
                game.step()
            moneys.append(game.state.get_money())
        print mean(moneys), stddev(moneys)
        print moneys
    else: print_usage()

if __name__ == "__main__":
    main()
