# bot.py
import random
from collections import defaultdict
from map import GRID_SIZE

DIRECTIONS = ["N", "E", "S", "W"]

class Robot:


    def __init__(self, robot_id, group, x, y,facing):
        self.id = robot_id
        self.group = group
        self.x = x
        self.y = y
        self.facing = facing
        self.state = "idle"

        self.partner_id = None
        self.gold_target = None
        self.carrying = False
        self.deposit = (0, 0) if self.group == "group1" else (GRID_SIZE - 1, GRID_SIZE - 1)

        self.group_status = {} # {0:{x:0,y:0,facing:N,state:idle, partner_id:None,gold_target:None,carrying:False} }
        self.known_gold = {} 
       
        self.inbox = []


    # -------------------
    # Messaging helpers
    # -------------------
    def broadcast_to_team(self, msg, robots):
        for r in robots:
            if r.group == self.group and r.id != self.id:
                r.inbox.append(msg)

    def process_latest_inbox(self):
        """
        Read the latest inbox entry (if any).
        Expected message format: [known_gold, group_status]
        - known_gold: dict {(x,y): amt}
        - group_status: either a single status dict with 'id' or a mapping id->status
        Update self.known_gold and self.group_status (merge, taking min for duplicate gold amounts).
        Does not remove messages from inbox.
        """
        if not self.inbox:
            return

        msg = self.inbox[-1]
        if not isinstance(msg, (list, tuple)) or len(msg) < 2:
            return

        incoming_known, incoming_group_status = msg[0], msg[1]

        # Merge known_gold (use min when we have existing estimate)
        if isinstance(incoming_known, dict):
            for pos, amt in incoming_known.items():
                pos_t = tuple(pos)
                if pos_t in self.known_gold:
                    self.known_gold[pos_t] = min(self.known_gold[pos_t], amt)
                else:
                    self.known_gold[pos_t] = amt

        # Merge group_status
        if isinstance(incoming_group_status, dict):
            # single status (has 'id')?
            if "id" in incoming_group_status:
                self.group_status[incoming_group_status["id"]] = incoming_group_status
            else:
                # assume mapping id->status
                for rid, status in incoming_group_status.items():
                    self.group_status[rid] = status

    # -------------------
    # Phase: Start
    # -------------------
    def start_phase(self, world, robots):
        # read latest message (if any) and merge into local maps
        self.process_latest_inbox()
        self.inbox.clear()  # clear inbox after processing
        print(f"Start known_gold {self.id}: {self.known_gold}")
        print(f"Start group_status {self.id}: {self.group_status}")
        # sense environment and update local known_gold
        for (vx, vy) in self.sense():
            amt = world.grid[vy][vx]["gold"]
            if amt > 0:
                self.known_gold[(vx, vy)] = amt

        if self.state != self.group_status[self.id]["state"]:
            self.sync_with_group_status


        # build message [known_gold, group_status] and broadcast to team
        msg = [self.known_gold, self.group_status]
        self.broadcast_to_team(msg,robots)

        # # update own status in group_status
        # self.group_status[self.id] = {
        #     "x": self.x,
        #     "y": self.y,
        #     "facing": self.facing,
        #     "state": self.state,
        #     "partner_id": self.partner_id,
        #     "gold_target": self.gold_target,
        #     "carrying": self.carrying
        # }
    # -------------------
    # Phase: Decision
    # -------------------
    def decision_phase(self, world, robots):
        self.process_latest_inbox()
        self.inbox.clear()
        print(f"Decision known_gold {self.id}: {self.known_gold}")
        print(f"Decision group_status {self.id}: {self.group_status}")

        if self.state == "idle":
            nearest_gold = self.find_nearest_unclaimed_gold()
            if nearest_gold:
                self.gold_target = nearest_gold
                self.state = "paired_for_gold"
                
                # Find nearest idle partner
                idle_partners = [
                    r for r in robots 
                    if r.group == self.group and r.id != self.id and r.state == "idle"
                ]
                if idle_partners:
                    partner = min(idle_partners, key=lambda r: self.distance(r.x, r.y))
                    self.partner_id = partner.id
                    # Send message to partner to pair up
                    self.group_status[self.partner_id] = {
                        "x": partner.x,
                        "y": partner.y,
                        "facing": partner.facing,
                        "state": "paired_for_gold",
                        "partner_id": self.id,
                        "gold_target": self.gold_target}
                        
                else:
                    # No available partners; revert to idle
                    self.state = "idle"
                    self.gold_target = None

            msg = [self.known_gold, self.group_status]
            self.broadcast_to_team(msg, robots)
        elif self.state == "paired_for_gold":
            

        
        

    # -------------------
    # Phase: Action
    # -------------------
    def action_phase(self, world, robots):
        if self.state == "idle":
            self.random_move()
        elif self.state in ("paired_for_gold", "carrying"):
            target_x, target_y = self.gold_target if self.state == "paired_for_gold" else self.deposit
            partner = next((r for r in robots if r.id == self.partner_id), None)
            if partner:
                dist_to_partner = abs(self.x - partner.x) + abs(self.y - partner.y)
                if self.is_leader:
                    if dist_to_partner > 1:
                        pass  # wait
                    else:
                        self.move_towards(target_x, target_y)
                else:
                    if dist_to_partner > 1:
                        self.move_towards(partner.x, partner.y)
                    else:
                        self.move_towards(target_x, target_y)

            # Check for pick or deposit
            if self.state == "paired_for_gold" and (self.x, self.y) == (target_x, target_y) and world.grid[target_y][target_x]["gold"] > 0:
                if partner and (partner.x, partner.y) == (target_x, target_y):
                    if self.is_leader:
                        world.grid[target_y][target_x]["gold"] -= 1
                        self.state = "carrying"
                        self.carrying = True
                        self.gold_target = None
                        self.send_next_cycle(self.partner_id, {
                            "type": "transition",
                            "sender": self.id,
                            "data": {"new_state": "carrying", "target_id": self.partner_id}
                        })
            elif self.state == "carrying" and (self.x, self.y) == self.deposit:
                if partner and (partner.x, partner.y) == self.deposit:
                    if self.is_leader:
                        world.scores[self.group] += 1
                        self.carrying = False
                        self.state = "idle"
                        self.partner_id = None
                        self.is_leader = False
                        self.send_next_cycle(partner.id, {
                            "type": "transition",
                            "sender": self.id,
                            "data": {"new_state": "idle", "target_id": partner.id}
                        })

    # -------------------
    # Movement/sense
    # -------------------

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
   
    def find_nearest_unclaimed_gold(self):
        """
        Find the nearest unclaimed gold from the robot's current position.
        Returns the position (x, y) of the nearest gold or None if no unclaimed gold is found.
        """
        nearest_gold = None
        min_distance = float('inf')

        # Collect all gold positions currently targeted by other robots in the group
        targeted_gold_positions = {
            status["gold_target"] for status in self.group_status.values()
            if status["gold_target"] is not None
        }

        for (gold_x, gold_y), amount in self.known_gold.items():
            if amount > 0 and (gold_x, gold_y) not in targeted_gold_positions: # Check if the gold is still available
                distance = self.distance(gold_x,gold_y)  
                if distance < min_distance:
                    min_distance = distance
                    nearest_gold = (gold_x, gold_y)

        return nearest_gold
    
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

    def turn_towards(self, tx, ty):
        """Turn towards target without moving."""
        if self.y < ty:
            self.turn("N")
        elif self.y > ty:
            self.turn("S")
        elif self.x < tx:
            self.turn("E")
        elif self.x > tx:
            self.turn("W")

    def random_move(self):
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
        """Return list of cells visible in front (3 at 1+, 5 at 2+)."""
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
    
    def sync_with_group_status(self):
 
        if self.id in self.group_status:
            status = self.group_status[self.id]
            self.x = status.get("x", self.x)
            self.y = status.get("y", self.y)
            self.facing = status.get("facing", self.facing)
            self.state = status.get("state", self.state)
            self.partner_id = status.get("partner_id", self.partner_id)
            self.gold_target = status.get("gold_target", self.gold_target)
            self.carrying = status.get("carrying", self.carrying)