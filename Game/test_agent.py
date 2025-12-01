import sys
import os
from agent import PyperplanAgent

# Mock classes for Block and Hole
class MockObj:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def test_solver():
    print("Testing FF Planner integration...")
    
    # Simple 3x3 map
    # P . .
    # . B .
    # . . H
    game_map = [
        ['.', '.', '.'],
        ['.', '.', '.'],
        ['.', '.', '.']
    ]
    
    player_pos = (0, 0)
    blocks = [MockObj(1, 1)]
    holes = [MockObj(2, 2)]
    
    agent = PyperplanAgent()
    
    print("Calling solve()...")
    plan = agent.solve(game_map, player_pos, blocks, holes, timeout=10)
    
    print(f"Plan result: {plan}")
    
    if plan == "Impossible":
        print("Test FAILED: Solver returned Impossible for a solvable problem.")
    elif isinstance(plan, list) and len(plan) > 0:
        print("Test PASSED: Solver returned a plan.")
        print("Plan steps:", plan)
    else:
        print(f"Test UNCERTAIN: Unexpected result: {plan}")

if __name__ == "__main__":
    test_solver()
