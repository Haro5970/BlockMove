import pygame
from game import Game
import threading
import queue
import sys

# Input thread function
def input_thread(input_queue):
    print("Type Prolog queries here (e.g., 'player(X, Y).'):")
    while True:
        try:
            # Read line from stdin
            query = sys.stdin.readline()
            if not query:
                break
            query = query.strip()
            if query:
                input_queue.put(query)
        except EOFError:
            break

# Create a queue for communication
input_q = queue.Queue()

# Start input thread as daemon
t = threading.Thread(target=input_thread, args=(input_q,), daemon=True)
t.start()

g = Game(input_q) # Pass queue to Game
print("Game initialized")
while True:
    print("Starting new game...")
    g.new()
    print("Game loop running...")
    g.run()
    print("Game loop ended.")
