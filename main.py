import time
from map import Map
from bot import Robot

def main():
    world = Map()
    robots = []

    # Create robots (10 each team)
    for i in range(10):
        robots.append(Robot(i, "group1", 0, 0))
        robots.append(Robot(i+10, "group2", 19, 19))

    for step in range(500):
        print(f"\n=== Step {step} ===")
        for robot in robots:
            robot.act(world, robots)
        world.display(robots, step)
        # time.sleep(0.01)

if __name__ == "__main__":
    main()
