import pygame
import sys
from os import path
from settings import *
from sprites import *
from agent import PyperplanAgent

import random
from collections import namedtuple

class Game:
    def __init__(self, input_queue=None):
        self.input_queue = input_queue
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        
        # Initialize Prolog Bridge
        # Assuming Ontology folder is at the same level as Game folder
        ontology_path = path.join(path.dirname(__file__), '..', 'Ontology', 'game.pl')
        from prolog_bridge import PrologBridge
        self.prolog_bridge = PrologBridge(ontology_path)
        
        self.agent = PyperplanAgent()
        self.plan = []
        self.plan_timer = 0
        self.auto_playing = False

    def generate_map(self):
        while True:
            self.map_data = []
            # Create empty grid
            for row in range(int(GRIDHEIGHT)):
                line = []
                for col in range(int(GRIDWIDTH)):
                    if row == 0 or row == int(GRIDHEIGHT) - 1 or col == 0 or col == int(GRIDWIDTH) - 1:
                        line.append('W') # Boundary walls
                    else:
                        if random.random() < 0.1: # 10% chance of inner wall
                            line.append('W')
                        else:
                            line.append('.')
                self.map_data.append(line)

            # Place Player
            player_pos = None
            while True:
                rx = random.randint(1, int(GRIDWIDTH) - 2)
                ry = random.randint(1, int(GRIDHEIGHT) - 2)
                if self.map_data[ry][rx] == '.':
                    self.map_data[ry][rx] = 'P'
                    player_pos = (rx, ry)
                    break

            # Place Blocks and Holes
            num_blocks = random.randint(3, 5)
            blocks_pos = []
            holes_pos = []
            
            # Place Blocks
            for _ in range(num_blocks):
                while True:
                    rx = random.randint(1, int(GRIDWIDTH) - 2)
                    ry = random.randint(1, int(GRIDHEIGHT) - 2)
                    if self.map_data[ry][rx] == '.':
                        self.map_data[ry][rx] = 'B'
                        blocks_pos.append((rx, ry))
                        break
            
            # Place Holes
            for _ in range(num_blocks):
                while True:
                    rx = random.randint(1, int(GRIDWIDTH) - 2)
                    ry = random.randint(1, int(GRIDHEIGHT) - 2)
                    if self.map_data[ry][rx] == '.':
                        self.map_data[ry][rx] = 'H'
                        holes_pos.append((rx, ry))
                        break
            
            if self.is_valid_map(player_pos, blocks_pos, holes_pos):
                break

    def is_valid_map(self, player_pos, blocks_pos, holes_pos):
        # 1. Check reachability using Flood Fill (Player Accessibility)
        # Can player reach all blocks?
        reachable = set()
        queue = [player_pos]
        visited = set([player_pos])
        
        while queue:
            cx, cy = queue.pop(0)
            reachable.add((cx, cy))
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < int(GRIDWIDTH) and 0 <= ny < int(GRIDHEIGHT):
                    if self.map_data[ny][nx] != 'W' and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
        
        # Check if all blocks are reachable
        for bx, by in blocks_pos:
            if (bx, by) not in reachable:
                return False
                
        # 2. Dead Square Detection (Reverse Reachability)
        # Identify squares from which a block can NEVER reach a hole
        # We start from holes and pull blocks backwards
        
        safe_squares = set(holes_pos)
        queue = list(holes_pos)
        visited_safe = set(holes_pos)
        
        while queue:
            cx, cy = queue.pop(0)
            
            # Try pulling a block FROM a neighbor (nx, ny) TO here (cx, cy)
            # This corresponds to Pushing from nx, ny to cx, cy
            # Directions: If we push UP (dy=-1), block moves from (cx, cy+1) to (cx, cy)
            # Player must be at (cx, cy+2)
            
            # Neighbors of cx, cy are potential sources
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx - dx, cy - dy # Potential block position (source)
                
                # Check bounds
                if not (0 <= nx < int(GRIDWIDTH) and 0 <= ny < int(GRIDHEIGHT)):
                    continue
                    
                if self.map_data[ny][nx] == 'W':
                    continue
                    
                if (nx, ny) in visited_safe:
                    continue
                
                # Check if player can push from nx, ny to cx, cy
                # Player needs to be at:
                px, py = nx - dx, ny - dy
                
                # Check player bounds and wall
                if 0 <= px < int(GRIDWIDTH) and 0 <= py < int(GRIDHEIGHT):
                    if self.map_data[py][px] != 'W':
                        # Valid push is possible!
                        visited_safe.add((nx, ny))
                        safe_squares.add((nx, ny))
                        queue.append((nx, ny))
        
        # Check if any block is on a dead square (not in safe_squares)
        for bx, by in blocks_pos:
            if (bx, by) not in safe_squares:
                return False

        return True

    def new(self):
        print("Game.new() called")
        self.generate_map()
        print("Map generated")
        self.all_sprites = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.blocks = pygame.sprite.Group()
        self.holes = pygame.sprite.Group()
        
        for row, tiles in enumerate(self.map_data):
            for col, tile in enumerate(tiles):
                if tile == 'W':
                    Wall(self, col, row)
                if tile == 'B':
                    Block(self, col, row)
                if tile == 'H':
                    Hole(self, col, row)
                if tile == 'P':
                    self.player = Player(self, col, row)
        
        self.plan = []
        self.auto_playing = False

    def run(self):
        self.playing = True
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update()
            self.draw()

    def quit(self):
        pygame.quit()
        sys.exit()

    def update(self):
        self.all_sprites.update()
        
        # Execute Auto Plan
        if self.auto_playing and self.plan:
            now = pygame.time.get_ticks()
            if now - self.plan_timer > 50: # Execute move every 50ms
                self.plan_timer = now
                move_dir = self.plan.pop(0)
                print(f"Auto Move: {move_dir}")
                
                dx, dy = 0, 0
                if move_dir == 'UP': dy = -1
                elif move_dir == 'DOWN': dy = 1
                elif move_dir == 'LEFT': dx = -1
                elif move_dir == 'RIGHT': dx = 1
                
                self.check_move(dx, dy)
                
                if not self.plan:
                    print("Auto Play Finished")
                    self.auto_playing = False

        # Check for console input
        if self.input_queue and not self.input_queue.empty():
            query = self.input_queue.get()
            print(f"\n[Console] Executing query: {query}")
            
            # Sync state first to ensure accuracy
            self.prolog_bridge.sync_state(
                (self.player.x, self.player.y),
                self.blocks,
                self.walls,
                self.holes
            )
            
            # Execute query
            results = self.prolog_bridge.query(query)
            if not results:
                print("  -> No solutions or false.")
            else:
                for i, sol in enumerate(results):
                    print(f"  -> Solution {i+1}: {sol}")

        # Check win condition
        if len(self.blocks) == 0:
            print("You Win!")
            self.playing = False

    def draw(self):
        self.screen.fill(DARKGREY)
        self.all_sprites.draw(self.screen)
        pygame.display.flip()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                if not self.auto_playing: # Disable manual control during auto-play
                    if event.key == pygame.K_LEFT:
                        self.check_move(-1, 0)
                    if event.key == pygame.K_RIGHT:
                        self.check_move(1, 0)
                    if event.key == pygame.K_UP:
                        self.check_move(0, -1)
                    if event.key == pygame.K_DOWN:
                        self.check_move(0, 1)
                    if event.key == pygame.K_r:
                        self.new()
                    if event.key == pygame.K_p:
                        # Sync current state to Prolog
                        print("[Game] Syncing state to Prolog...")
                        self.prolog_bridge.sync_state(
                            (self.player.x, self.player.y),
                            self.blocks,
                            self.walls,
                            self.holes
                        )

                        # Debug: Print Prolog Player Position
                        pos = self.prolog_bridge.get_player_pos()
                        print(f"[Prolog] Player Position: {pos}")
                        
                        # Debug: Run a custom query
                        print("[Prolog] Running custom query: block(X, Y)")
                        blocks = self.prolog_bridge.query("block(X, Y)")
                        for b in blocks:
                            print(f"  - Block at ({b['X']}, {b['Y']})")
                    
                    if event.key == pygame.K_a:
                        print("Starting Auto Play...")
                        plan = self.agent.solve(self.map_data, (self.player.x, self.player.y), self.blocks, self.holes)
                        if plan == "Impossible":
                            print("Impossible to solve!")
                        elif plan:
                            print(f"Plan found: {plan}")
                            self.plan = plan
                            self.auto_playing = True
                            self.plan_timer = pygame.time.get_ticks()

    def check_move(self, dx, dy):
        target_x = self.player.x + dx
        target_y = self.player.y + dy

        # Check for walls
        for wall in self.walls:
            if wall.x == target_x and wall.y == target_y:
                self.player.bounce(dx, dy)
                return # Blocked by wall

        # Check for blocks
        for block in self.blocks:
            if block.x == target_x and block.y == target_y:
                # Try to move the block
                if self.move_block(block, dx, dy):
                    self.player.move(dx, dy)
                else:
                    self.player.bounce(dx, dy)
                return # Player moved or was blocked by immovable block

        # If no obstacles, move player
        self.player.move(dx, dy)

    def move_block(self, block, dx, dy):
        target_x = block.x + dx
        target_y = block.y + dy

        # Check if block hits wall
        for wall in self.walls:
            if wall.x == target_x and wall.y == target_y:
                return False

        # Check if block hits another block
        for other_block in self.blocks:
            if other_block.x == target_x and other_block.y == target_y:
                return False

        # Move block
        block.move(dx, dy)

        # Check if block falls in hole
        for hole in self.holes:
            if hole.x == block.x and hole.y == block.y:
                block.kill()
        
        return True
