# map.py
import random
import matplotlib.pyplot as plt
import matplotlib.patheffects as patheffects

GRID_SIZE = 20
GOLD =50

class Map:
    def __init__(self):
        # Initialize empty grid
        self.grid = [[{"gold": 0, "deposit": None} for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Place deposit points
        self.deposit_points = [(0, 0), (GRID_SIZE - 1, GRID_SIZE - 1)]
        self.grid[0][0]["deposit"] = "group1"
        self.grid[GRID_SIZE - 1][GRID_SIZE - 1]["deposit"] = "group2"
        
        # Place random gold bars
        for _ in range(GOLD):  
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if self.grid[y][x]["deposit"] is None:
                self.grid[y][x]["gold"] += 1
                


        # Score tracker
        self.scores = {"group1": 0, "group2": 0}
        
        # Set up matplotlib
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        plt.ion()  # interactive mode ON
        plt.show()

    def display(self, robots, step =0):
        """Visualize map with matplotlib."""
        self.ax.clear()
        self.ax.set_xlim(-0.5, GRID_SIZE - 0.5)
        self.ax.set_ylim(-0.5, GRID_SIZE - 0.5)
        self.ax.set_xticks(range(GRID_SIZE))
        self.ax.set_yticks(range(GRID_SIZE))
        self.ax.grid(True)

        # Draw deposits
        for (x, y), group in zip(self.deposit_points, ["group1", "group2"]):
            color = "blue" if group == "group1" else "red"
            self.ax.scatter(x, y, c=color, marker="s", s=200, label=f"{group} deposit")

        # Draw gold
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                gold_amt = self.grid[y][x]["gold"]
                if gold_amt > 0:
                    self.ax.scatter(x, y, c="gold", marker="o", s=100)
                    # draw number of golds
                    self.ax.text(x, y, str(gold_amt), color="black", fontsize=8, ha="center", va="center")
        
        # Prepare grouping of robots by position so IDs can be stacked when overlapping
        from collections import defaultdict as _dd
        positions = _dd(list)
        
        # Draw robots
        for r in robots:
            color = "blue" if r.group == "group1" else "red"
            vision_color = "lightgreen" if r.group == "group1" else "darkseagreen"

            # Vision overlay (semi-transparent)
            for (vx, vy) in r.sense():
                self.ax.add_patch(plt.Rectangle((vx - 0.5, vy - 0.5), 1, 1,
                                                facecolor=vision_color, alpha=0.2))

            # Robot body
            self.ax.scatter(r.x, r.y, c=color, s=80, edgecolors="black")
            
            # Draw facing direction as arrow
            dx, dy = 0, 0
            if r.facing == "N": dy = 0.3
            elif r.facing == "S": dy = -0.3
            elif r.facing == "E": dx = 0.3
            elif r.facing == "W": dx = -0.3
            self.ax.arrow(r.x, r.y, dx, dy, head_width=0.2, head_length=0.2, fc=color, ec=color)

             # 🟡 Mark carrying gold
            if r.carrying:
                self.ax.scatter(r.x, r.y, c="gold", marker="o", s=200, alpha=0.6, edgecolors="black")
            
            positions[(r.x, r.y)].append(r)

            # Draw stacked IDs for positions that contain one or more robots
        for (px, py), robots_at in positions.items():
            # start slightly above the robot marker; stack upward
            base_offset = 0.25
            gap = 0.5
            # If many robots, reduce font size to fit
            fontsize = 8 if len(robots_at) <= 4 else max(6, 8 - (len(robots_at) - 4))
            for idx, r in enumerate(sorted(robots_at, key=lambda rr: rr.id)):
                offset_y = base_offset + idx * gap
                try:
                    self.ax.text(
                        px,
                        py + offset_y,
                        str(r.id),
                        color="white",
                        fontsize=fontsize,
                        ha="center",
                        va="bottom",
                        weight="bold",
                        path_effects=[patheffects.Stroke(linewidth=1.5, foreground='black'), patheffects.Normal()]
                    )
                except Exception:
                    # Fallback: plain text
                    self.ax.text(px, py + offset_y, str(r.id), color="black", fontsize=fontsize, ha="center", va="bottom")

        # Title → Step counter + scores
        self.ax.set_title(f"Step {step} | Scores → Group1: {self.scores['group1']} | Group2: {self.scores['group2']}")

        plt.pause(0.05)  # update frame