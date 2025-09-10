import random
from map import GRID_SIZE

DIRECTIONS = ["N", "E", "S", "W"]

class Robot:
    def __init__(self, robot_id, group, x, y):
        self.robot_id = robot_id 
        self.group = group
        self.x = x
        self.y = y
        self.facing = random.choice(DIRECTIONS) 
        self.carrying_gold = False
        self.partner = None 
        self.target = None
        self.inbox = []  # direct messages from teammates
        
        
        
    def send(self, teammate, message):
        """Send a message to a teammate."""
        if teammate.group == self.group:  # only same team
            teammate.inbox.append((self.robot_id, message))

    def broadcast(self, robots, message):
        """Send message to all teammates in same group."""
        for r in robots:
            if r.group == self.group and r != self:
                self.send(r, message)

    def read_messages(self):
        """Retrieve and clear inbox."""
        msgs = self.inbox[:]
        self.inbox.clear()
        return msgs



    def distance(self, tx, ty):
        """
        Estimate number of cycles (turns + forward moves) to reach (tx, ty).
        """
        dx = tx - self.x
        dy = ty - self.y

        # Forward steps needed (Manhattan distance)
        steps = abs(dx) + abs(dy)

        # Determine primary direction needed (N/S vs E/W)
        needed_dirs = []
        turns = 0
        if dy > 0 and self.facing != "N":
            needed_dirs.append("N")
            turns += 1
        elif dy < 0 and self.facing != "S":
            needed_dirs.append("S")
            turns += 1
        if dx > 0 and self.facing != "E":
            needed_dirs.append("E")
            turns += 1
        elif dx < 0 and self.facing != "W":
            needed_dirs.append("W")
            turns += 1
            
        return steps + turns


    def move_towards(self, tx, ty):
        """Move one step towards target (tx, ty)."""
        
        if self.y < ty:
            if self.facing != "N":
                self.turn("N")
            else:
                self.move_forward()
        elif self.y > ty:
            if self.facing != "S":
                self.turn("S")
            else:
                self.move_forward()
        elif self.x < tx:
            if self.facing != "E":
                self.turn("E")
            else:
                self.move_forward()
        elif self.x > tx:
            if self.facing != "W":
                self.turn("W")
            else:
                self.move_forward()   
                
    def move_forward(self):
        """Move one step forward in facing direction."""
        if self.facing == "S" and self.y > 0:
            self.y -= 1
        elif self.facing == "N" and self.y < GRID_SIZE - 1:
            self.y += 1
        elif self.facing == "E" and self.x < GRID_SIZE - 1:
            self.x += 1
        elif self.facing == "W" and self.x > 0:
            self.x -= 1
            
    def turn(self, new_facing):
        """Turn to new facing direction."""
        if new_facing in DIRECTIONS:
            self.facing = new_facing
        
    def rand_turn(exclude=None):    
        return random.choice([d for d in DIRECTIONS if d not in (exclude or [])])
    
    def get_safe_directions(self):
        """Return list of directions that won't point outside the grid from current position."""
        safe = []
        if self.y < GRID_SIZE - 1:  # can go North
            safe.append("N")
        if self.y > 0:              # can go South
            safe.append("S")
        if self.x < GRID_SIZE - 1:  # can go East
            safe.append("E")
        if self.x > 0:              # can go West
            safe.append("W")
        return safe #list of safe directions
 
    
    def random_move(self):
        """At each cycle, robot either moves forward one step or turns to a safe new direction."""
        action = random.choice(["forward", "turn"])

        if action == "forward":
            # Try to move forward; if blocked by edge, force a turn
            if (self.facing == "S" and self.y > 0):
                self.move_forward()
            elif (self.facing == "N" and self.y < GRID_SIZE - 1):
                self.move_forward()
            elif (self.facing == "E" and self.x < GRID_SIZE - 1):
                self.move_forward()
            elif (self.facing == "W" and self.x > 0):
                self.move_forward()
            else:
                # If at edge, force a safe turn
                safe_dirs = self.get_safe_directions()
                if safe_dirs:
                    self.turn(random.choice(safe_dirs))
        else:
            # Turn to a safe direction
            safe_dirs = self.get_safe_directions()
            if safe_dirs:
                self.turn(random.choice(safe_dirs))



    def sense(self):
        """Return list of cells visible in front (3 at 1 step, 5 at 2 steps)."""
        visible = []
        if self.facing == "N":
            # One step north
            visible += [(self.x + dx, self.y + 1) for dx in (-1, 0, 1)]
            # Two steps north
            visible += [(self.x + dx, self.y + 2) for dx in (-2, -1, 0, 1, 2)]
        elif self.facing == "S":
            visible += [(self.x + dx, self.y - 1) for dx in (-1, 0, 1)]
            visible += [(self.x + dx, self.y - 2) for dx in (-2, -1, 0, 1, 2)]
        elif self.facing == "E":
            visible += [(self.x + 1, self.y + dy) for dy in (-1, 0, 1)]
            visible += [(self.x + 2, self.y + dy) for dy in (-2, -1, 0, 1, 2)]
        elif self.facing == "W":
            visible += [(self.x - 1, self.y + dy) for dy in (-1, 0, 1)]
            visible += [(self.x - 2, self.y + dy) for dy in (-2, -1, 0, 1, 2)]

        # Keep only valid grid positions
        return [(x, y) for x, y in visible if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE]


    def act(self, world_map, robots):
        """Decide action each cycle."""

        # === 1. Detect gold ===
        if not self.carrying_gold and not self.partner:
            visible = self.sense()
            for (vx, vy) in visible:
                if world_map.grid[vy][vx]["gold"] > 0:
                    teammates = [r for r in robots if r.group == self.group and r != self and not r.carrying_gold and not r.partner]
                    if teammates:
                        # Pick the teammate with lowest cycle distance to this gold
                        nearest = min(teammates, key=lambda r: r.distance(vx, vy))
                        self.partner = nearest
                        nearest.partner = self
                        self.target = (vx, vy)
                        nearest.target = (vx, vy)
                        print(f"📢 Robot {self.robot_id} ({self.group}) sees gold at ({vx},{vy}) "
                              f"and called {nearest.robot_id} (distance={nearest.distance(vx, vy)})")
                    break  # stop after first visible gold

        # === 2. Move toward gold ===
        if self.partner and not self.carrying_gold:
            if self.target:
                self.move_towards(*self.target)

            # Check if both robots have reached the gold cell
            if self.target and (self.x, self.y) == self.target and (self.partner.x, self.partner.y) == self.target:
                if world_map.grid[self.y][self.x]["gold"] > 0:
                    world_map.grid[self.y][self.x]["gold"] -= 1
                    self.carrying_gold = self.partner.carrying_gold = True
                    # After picking up, set deposit as next target
                    deposit = world_map.deposit_points[0] if self.group == "group1" else world_map.deposit_points[1]
                    self.target = deposit
                    self.partner.target = deposit
                    print(f"🤝 Robots {self.robot_id} & {self.partner.robot_id} picked up gold at {self.target}, heading to deposit")
            return  # stop here if working on pickup

        # === 3. Carrying gold → go to deposit ===
        if self.carrying_gold and self.partner:
            deposit = world_map.deposit_points[0] if self.group == "group1" else world_map.deposit_points[1]
            self.target = deposit
            self.partner.target = deposit

            # Move toward deposit
            self.move_towards(*deposit)

            # Check if both reached deposit
            if (self.x, self.y) == deposit and (self.partner.x, self.partner.y) == deposit:
                world_map.scores[self.group] += 1
                print(f"✅ {self.group} robots {self.robot_id} & {self.partner.robot_id} deposited gold! Score: {world_map.scores[self.group]}")
                # Reset state
                self.carrying_gold = self.partner.carrying_gold = False
                self.partner.partner = None
                self.partner = None
                self.target = None
            return

        # === 4. Idle behavior (wander) ===
        if not self.carrying_gold and not self.partner:
            self.random_move()
