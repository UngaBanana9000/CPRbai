import random
from map import GRID_SIZE

DIRECTIONS = ["N", "E", "S", "W"]

class Robot:
    def __init__(self, robot_id, group, x, y,rank=0):
        self.robot_id = robot_id 
        self.group = group
        self.x = x
        self.y = y
        self.facing = random.choice(DIRECTIONS) 
        self.carrying_gold = False
        self.partner = None 
        self.target = None
        self.rank = rank  # tie-breaking value
        self.inbox = []  # direct messages from teammates
        
        # ✅ team-local dictionary: gold_coord -> (robot1_id, robot2_id)
        self.team_assignments = {}
        
    def send(self, teammate, message):
        """Send a message to a teammate."""
        if teammate.group == self.group:  # only same team
            teammate.inbox.append((self.robot_id, message))

    def broadcast(self, robots, message):
        """Send message to all teammates."""
        for r in robots:
            if r.group == self.group and r != self:
                r.inbox.append((self.robot_id, message))


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
  
    def orient_towards(self, tx, ty):
        """Turn to face the target coordinate."""
        if self.y < ty:
            self.turn("N")
        elif self.y > ty:
            self.turn("S")
        elif self.x < tx:
            self.turn("E")
        elif self.x > tx:
            self.turn("W")
        
    def orient_towards_deposit(self, deposit):
        """Orient toward deposit, prefer N/S over E/W if both options exist."""
        dx = deposit[0] - self.x
        dy = deposit[1] - self.y

        # Prefer N/S first
        if dy > 0:
            self.turn("N")
        elif dy < 0:
            self.turn("S")
        elif dx > 0:
            self.turn("E")
        elif dx < 0:
            self.turn("W")

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
        action = random.choices(["forward", "turn"], weights=[70, 30])[0]

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



    # def sense(self): #only coordinates
    #     """Return list of cells visible in front (3 at 1 step, 5 at 2 steps)."""
    #     visible = []
    #     if self.facing == "N":
    #         # One step north
    #         visible += [(self.x + dx, self.y + 1) for dx in (-1, 0, 1)]
    #         # Two steps north
    #         visible += [(self.x + dx, self.y + 2) for dx in (-2, -1, 0, 1, 2)]
    #     elif self.facing == "S":
    #         visible += [(self.x + dx, self.y - 1) for dx in (-1, 0, 1)]
    #         visible += [(self.x + dx, self.y - 2) for dx in (-2, -1, 0, 1, 2)]
    #     elif self.facing == "E":
    #         visible += [(self.x + 1, self.y + dy) for dy in (-1, 0, 1)]
    #         visible += [(self.x + 2, self.y + dy) for dy in (-2, -1, 0, 1, 2)]
    #     elif self.facing == "W":
    #         visible += [(self.x - 1, self.y + dy) for dy in (-1, 0, 1)]
    #         visible += [(self.x - 2, self.y + dy) for dy in (-2, -1, 0, 1, 2)]

    #     # Keep only valid grid positions
    #     return [(x, y) for x, y in visible if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE]
    
    def sense(self, world_map): # coordinates + cell info
        """Return info about visible cells (gold, deposit)."""
        visible_coords = []
        if self.facing == "N":
            visible_coords += [(self.x + dx, self.y + 1) for dx in (-1, 0, 1)]
            visible_coords += [(self.x + dx, self.y + 2) for dx in (-2, -1, 0, 1, 2)]
        elif self.facing == "S":
            visible_coords += [(self.x + dx, self.y - 1) for dx in (-1, 0, 1)]
            visible_coords += [(self.x + dx, self.y - 2) for dx in (-2, -1, 0, 1, 2)]
        elif self.facing == "E":
            visible_coords += [(self.x + 1, self.y + dy) for dy in (-1, 0, 1)]
            visible_coords += [(self.x + 2, self.y + dy) for dy in (-2, -1, 0, 1, 2)]
        elif self.facing == "W":
            visible_coords += [(self.x - 1, self.y + dy) for dy in (-1, 0, 1)]
            visible_coords += [(self.x - 2, self.y + dy) for dy in (-2, -1, 0, 1, 2)]

        visible = []
        for (x, y) in visible_coords:
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                cell = world_map.grid[y][x]   # <- robot can ONLY see cells in sight
                visible.append(((x, y), cell.copy()))  # contains {"gold": n, "deposit": ...}
        return visible

    def assign_gold(self, tx, ty, robots, world_map):
        """
        Assign pairs of robots to gold.
        Handles multiple gold in the same cell.
        """
        # Count how many robots are already assigned to this gold
        assigned_pair_ids = self.team_assignments.get((tx, ty), ())
        assigned_count = len(assigned_pair_ids) // 2  # each pair = 2 robots

        # How many pairs are needed? Each gold requires 1 pair
        gold_amount = world_map.grid[ty][tx]["gold"]
        pairs_needed = gold_amount - assigned_count
        if pairs_needed <= 0:
            return  # enough pairs already assigned

        # Only consider free robots
        candidates = [r for r in robots if r.group == self.group and not r.carrying_gold and not r.partner]
        if len(candidates) < 2:
            return  # not enough free robots

        # Sort candidates by distance then rank
        candidates.sort(key=lambda r: (r.distance(tx, ty), -r.rank))

        # Assign up to `pairs_needed` pairs
        pairs_to_assign = min(pairs_needed, len(candidates) // 2)
        for i in range(pairs_to_assign):
            pair = candidates[i*2:i*2+2]
            for r in pair:
                r.target = (tx, ty)
                r.partner = [p for p in pair if p != r][0]

            # Update team assignment
            existing = list(self.team_assignments.get((tx, ty), ()))
            existing += [r.robot_id for r in pair]
            self.team_assignments[(tx, ty)] = tuple(existing)

            print(f"📢 {self.group} robots {[r.robot_id for r in pair]} assigned to gold at ({tx},{ty})")


    def act(self, world_map, robots):
        """Decide action each cycle with pair assignment and rank-based tie-breaker."""

        # 1️⃣ Sense local gold
        visible = self.sense(world_map)
        for (vx, vy), cell in visible:
            if cell["gold"] > 0 and (vx, vy) not in self.team_assignments:
                self.broadcast(robots, {"type": "gold", "pos": (vx, vy)})
                print(f"📡 Robot {self.robot_id} broadcasting gold at ({vx},{vy})")
                break  # broadcast only first visible gold

        # 2️⃣ Process teammate messages
        for sender_id, msg in self.inbox:
            if msg["type"] == "gold":
                tx, ty = msg["pos"]
                if (tx, ty) not in self.team_assignments:
                    self.assign_gold(tx, ty, robots, world_map)
        self.inbox.clear()  # clear after reading

        # 3️⃣ Move toward gold / pickup
        if self.partner and not self.carrying_gold:
            if self.target:
                tx, ty = self.target
                if (self.x, self.y) == (tx, ty) and (self.partner.x, self.partner.y) == (tx, ty):
                    
                    # ✅ Orient both toward deposit before picking up
                    deposit = world_map.deposit_points[0] if self.group == "group1" else world_map.deposit_points[1]
                    self.orient_towards_deposit(deposit)
                    self.partner.orient_towards_deposit(deposit)

                    # ✅ Only pick up if both facing same direction
                    if self.facing == self.partner.facing:
                        if world_map.grid[self.y][self.x]["gold"] > 0:
                            world_map.grid[self.y][self.x]["gold"] -= 1
                            # After picking up gold
                            if world_map.grid[self.y][self.x]["gold"] == 0:
                                if (self.x, self.y) in self.team_assignments:
                                    del self.team_assignments[(self.x, self.y)]

                            self.carrying_gold = self.partner.carrying_gold = True
                            # Clear assignment
                            if (tx, ty) in self.team_assignments:
                                del self.team_assignments[(tx, ty)]
                            # Set deposit as next target
                            self.target = self.partner.target = deposit
                            print(f"🤝 Robots {self.robot_id} & {self.partner.robot_id} picked up gold, heading to deposit")
                    else:
                        # Wait until both oriented
                        print(f"⏳ Robots {self.robot_id} & {self.partner.robot_id} orienting toward deposit")
                else:
                    self.move_towards(tx, ty)
            return


        # 4️⃣ Carrying gold → deposit
        if self.carrying_gold and self.partner:
            deposit = world_map.deposit_points[0] if self.group == "group1" else world_map.deposit_points[1]
            self.target = self.partner.target = deposit

            self.move_towards(*deposit)

            if (self.x, self.y) == deposit and (self.partner.x, self.partner.y) == deposit:
                world_map.scores[self.group] += 1
                print(f"✅ {self.group} robots {self.robot_id} & {self.partner.robot_id} deposited gold! Score: {world_map.scores[self.group]}")
                self.reset_pairing()
            return

        # 5️⃣ Idle / random move
        if not self.carrying_gold and not self.partner and self.target is None:
            self.random_move()
            
    def reset_pairing(self):
        """Reset robot and partner state after deposit or failed pickup."""
        if self.partner:
            self.partner.partner = None
            self.partner.target = None
            self.partner.carrying_gold = False
        self.partner = None
        self.target = None
        self.carrying_gold = False

