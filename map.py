import random

GRID_SIZE = 20

class Map:
    def __init__(self):
        # Initialize empty grid
        self.grid = [[{"gold": 0, "deposit": None} for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Place deposit points
        self.deposit_points = [(0, 0), (GRID_SIZE - 1, GRID_SIZE - 1)]
        self.grid[0][0]["deposit"] = "group1"
        self.grid[GRID_SIZE - 1][GRID_SIZE - 1]["deposit"] = "group2"
        
        # Place random gold bars
        for _ in range(30):  
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if self.grid[y][x]["deposit"] is None:
                self.grid[y][x]["gold"] += 1


        self.gold_claims = {}  # (x,y) -> [robot_ids]
        # Score tracker
        self.scores = {"group1": 0, "group2": 0}

    def display(self, robots):
        """Print grid with robots, gold, deposits, and scores."""
        for y in range(GRID_SIZE):
            row = []
            for x in range(GRID_SIZE):
                cell = self.grid[y][x]# fix y to flip columns
                robots_here = [r for r in robots if r.x == x and r.y == y]

                # Default marker
                marker = ".."

                # Deposit marker
                if cell["deposit"] == "group1":
                    marker = "D1"
                elif cell["deposit"] == "group2":
                    marker = "D2"

                # Gold marker
                if cell["gold"] > 0:
                    marker = f"G{cell['gold']}"

                # Robots override
                if robots_here:
                    marker = "|".join([
                        f"{'R1' if r.group=='group1' else 'R2'}{r.robot_id%10}{r.facing}"
                        for r in robots_here
                    ])

                row.append(f"{marker:8}")
            print("".join(row))
        print(f"Scores → Group1: {self.scores['group1']} | Group2: {self.scores['group2']}\n")
