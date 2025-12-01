import sys
import os
import subprocess

import time

class PyperplanAgent:
    def __init__(self):
        print("Initializing WSL connection...")
        self.game_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            # Start a persistent WSL bash session
            # We use stdbuf -i0 -o0 -e0 to disable buffering if possible, but wsl might not support it directly on launch.
            # Just launching "wsl" starts the default shell.
            # We merge stderr into stdout to capture all output in one stream.
            self.wsl_process = subprocess.Popen(
                ["wsl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                bufsize=0, # Unbuffered
                cwd=self.game_dir
            )
            print("WSL Process started successfully.")
        except Exception as e:
            print(f"Failed to start WSL process: {e}")
            self.wsl_process = None

    def __del__(self):
        if hasattr(self, 'wsl_process') and self.wsl_process:
            print("Terminating WSL process...")
            self.wsl_process.terminate()

    def solve(self, game_map, player_pos, blocks, holes, timeout=60):
        if not self.wsl_process:
            print("WSL process is not running.")
            return "Impossible"

        # print("Generating problem.pddl...")
        self.generate_problem(game_map, player_pos, blocks, holes)
        
        # print("Running FF Planner via persistent WSL...")
        # FF executable path (relative to where game.py is run)
        ff_path = "./ff/ff"
        domain_file = "domain.pddl"
        problem_file = "problem.pddl"
        
        # Command to run in the persistent shell
        # We append a unique marker to know when the command finishes
        marker = "__END_OF_PLAN__"
        cmd = f"{ff_path} -o {domain_file} -f {problem_file}; echo {marker}\n"
        
        start_time = time.time()
        
        try:
            # Send command
            self.wsl_process.stdin.write(cmd)
            self.wsl_process.stdin.flush()
            
            # Read output
            output_lines = []
            while True:
                # Read line by line
                line = self.wsl_process.stdout.readline()
                
                if not line:
                    # Process ended unexpectedly
                    break
                
                line = line.strip()
                if line == marker:
                    break
                
                output_lines.append(line)
                
        except Exception as e:
            print(f"Error during WSL communication: {e}")
            return "Impossible"
            
        end_time = time.time()
        
        total_wsl_time = end_time - start_time
        print(f"Total WSL Execution Time: {total_wsl_time:.4f} seconds")

        full_output = "\n".join(output_lines)

        # Check for success
        # FF usually prints "found legal plan"
        if "found legal plan" in full_output:
            print("Solution found!")
            
            # Extract FF internal time
            for line in output_lines:
                if "seconds" in line:
                    print(f"FF Internal Time: {line}")
            
            plan = self.parse_ff_solution(full_output)
            return plan
        else:
            print("No solution found in FF output.")
            # print("--- FF OUTPUT ---")
            # print(full_output)
            return "Impossible"

    def generate_problem(self, game_map, player_pos, blocks, holes):
        problem_path = os.path.join(self.game_dir, 'problem.pddl')
        with open(problem_path, 'w') as f:
            f.write("(define (problem blockmove-1)\n")
            f.write("  (:domain blockmove)\n")
            
            # Objects
            locs = []
            height = len(game_map)
            width = len(game_map[0])
            
            for y in range(height):
                for x in range(width):
                    if game_map[y][x] != 'W':
                        locs.append(f"l_{x}_{y}")
            
            block_names = [f"b{i}" for i in range(len(blocks))]
            
            f.write(f"  (:objects {' '.join(locs)} - loc {' '.join(block_names)} - block up down left right - direction)\n")
            
            # Init
            f.write("  (:init\n")
            
            # Connectivity
            for y in range(height):
                for x in range(width):
                    if game_map[y][x] == 'W': continue
                    
                    # Check 4 directions
                    # UP (0, -1)
                    if y > 0 and game_map[y-1][x] != 'W':
                        f.write(f"    (connected l_{x}_{y} l_{x}_{y-1} up)\n")
                    # DOWN (0, 1)
                    if y < height - 1 and game_map[y+1][x] != 'W':
                        f.write(f"    (connected l_{x}_{y} l_{x}_{y+1} down)\n")
                    # LEFT (-1, 0)
                    if x > 0 and game_map[y][x-1] != 'W':
                        f.write(f"    (connected l_{x}_{y} l_{x-1}_{y} left)\n")
                    # RIGHT (1, 0)
                    if x < width - 1 and game_map[y][x+1] != 'W':
                        f.write(f"    (connected l_{x}_{y} l_{x+1}_{y} right)\n")

            # Player
            f.write(f"    (at-player l_{int(player_pos[0])}_{int(player_pos[1])})\n")
            
            # Blocks
            block_locs = set()
            for i, b in enumerate(blocks):
                f.write(f"    (at b{i} l_{b.x}_{b.y})\n")
                block_locs.add((b.x, b.y))
            
            # Holes
            for h in holes:
                f.write(f"    (is-hole l_{h.x}_{h.y})\n")
            
            # Clear
            for y in range(height):
                for x in range(width):
                    if game_map[y][x] != 'W':
                        if (x, y) != (int(player_pos[0]), int(player_pos[1])) and (x, y) not in block_locs:
                            f.write(f"    (clear l_{x}_{y})\n")
            
            f.write("  )\n")
            
            # Goal
            f.write("  (:goal (and\n")
            for b in block_names:
                f.write(f"    (stored {b})\n")
            f.write("  ))\n")
            f.write(")\n")

    def parse_ff_solution(self, output):
        plan = []
        lines = output.splitlines()
        parsing_plan = False
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Start parsing when we see "step"
            if line.startswith("step"):
                parsing_plan = True
            
            if parsing_plan:
                # Format 1: "step    0: UP"
                # Format 2: "        1: RIGHT" (indented, starts with number)
                
                parts = line.split(":")
                if len(parts) > 1:
                    # Check if the part before colon ends with a number
                    # "step 0" -> ends with 0
                    # "1" -> ends with 1
                    prefix = parts[0].strip()
                    if not (prefix.startswith("step") or prefix[0].isdigit()):
                        continue
                        
                    action = parts[1].strip().upper()
                    
                    action_parts = action.split()
                    if not action_parts: continue
                    
                    op_name = action_parts[0]
                    
                    direction = None
                    if op_name == "MOVE":
                        direction = action_parts[3]
                    elif op_name == "PUSH":
                        direction = action_parts[4]
                    elif op_name == "PUSH-TO-HOLE":
                        direction = action_parts[4]
                        
                    if direction:
                        plan.append(direction.upper())
                        
        return plan
