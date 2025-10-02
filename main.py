# main.py
import time
from map import Map
from bot import Robot
 
def main():
    world = Map()
    robots = []

    # Create robots
    for i in range(10):
        
        robots.append(Robot(i, "group1", 0, 0,"N"))
        robots.append(Robot(i+10, "group2", 19, 19,"S"))

    group_status = update_group_status(robots)
    # print(group_status)
    
    for r in robots:
        r.group_status = group_status[r.group]
    print("group status updated")


    for step in range(1000):
        print(f"\n=== Step {step} ===")

        # --- Phase 1: Start ---
        for r in robots:
            r.start_phase(world, robots)
        print("start phase complete")
        # --- Phase 2: Decision ---
        for r in robots:
            r.decision_phase(world, robots)
        print("decision phase complete")
        # --- Phase 3: Action ---
        for r in robots:
            r.action_phase(world, robots)
        print("action phase complete")
        
        # --- Display ---
        world.display(robots, step)
        # time.sleep(0.02)

def update_group_status(robots):
    """
    Updates the status of all robots in each group and returns a dictionary
    with group names as keys and their robots' statuses as values.
    """
    group_status = {}
    for r in robots:
        if r.group not in group_status:
            group_status[r.group] = {}
        group_status[r.group][r.id] ={
            "x": r.x,
            "y": r.y,
            "facing": r.facing,
            "state": r.state,
            "partner_id": r.partner_id,
            "gold_target": r.gold_target,
            "carrying": r.carrying
        }
    return group_status

if __name__ == "__main__":
    main()