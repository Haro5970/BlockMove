from pyswip import Prolog
import os

class PrologBridge:
    def __init__(self, ontology_path):
        self.prolog = Prolog()
        # Convert to absolute path and forward slashes for Prolog
        abs_path = os.path.abspath(ontology_path).replace('\\', '/')
        print(f"Loading Prolog file from: {abs_path}")
        try:
            self.prolog.consult(abs_path)
            print("Prolog file loaded successfully.")
        except Exception as e:
            print(f"Error loading Prolog file: {e}")

    def query(self, query_str):
        """
        Executes a raw Prolog query and returns a list of solutions.
        Each solution is a dictionary mapping variable names to values.
        """
        try:
            solutions = list(self.prolog.query(query_str))
            return solutions
        except Exception as e:
            print(f"Error executing query '{query_str}': {e}")
            return []

    def get_player_pos(self):
        """
        Helper to get player position from Prolog.
        Returns (X, Y) or None if not found.
        """
        solutions = self.query("player(X, Y)")
        if solutions:
            return solutions[0]['X'], solutions[0]['Y']
        return None

    def sync_state(self, player_pos, blocks, walls, holes):
        """
        Synchronize Python game state to Prolog.
        """
        # Clear existing dynamic facts
        self.prolog.retractall("player(_, _)")
        self.prolog.retractall("block(_, _)")
        self.prolog.retractall("wall(_, _)")
        self.prolog.retractall("hole(_, _)")

        # Assert new player position
        # Note: Prolog is 1-based usually, but our logic seems to handle coordinates directly.
        # If Python is 0-based, we might want to +1 if we want 1-based in Prolog, 
        # but for consistency let's stick to what Python uses (0-based) or convert.
        # The previous game.pl used 1-based (1,1). Python uses 0-based.
        # Let's use 0-based for simplicity in mapping, or +1 if we want to be "Prolog-ish".
        # Given the previous hardcoded values were 1,1 etc, let's just pass raw values 
        # and assume the Prolog logic (in_bounds etc) handles it or we adjust board_size.
        
        px, py = player_pos
        self.prolog.assertz(f"player({px}, {py})")

        # Assert blocks
        for block in blocks:
            self.prolog.assertz(f"block({block.x}, {block.y})")

        # Assert walls
        for wall in walls:
            self.prolog.assertz(f"wall({wall.x}, {wall.y})")

        # Assert holes
        for hole in holes:
            self.prolog.assertz(f"hole({hole.x}, {hole.y})")
            
        print("[Bridge] State synchronized to Prolog.")
