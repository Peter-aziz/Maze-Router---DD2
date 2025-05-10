from collections import deque
import matplotlib.pyplot as plt
import numpy as np
import re
import os

## helper functions
#check the test cases are valid ...

def parse_input_file(filename):
    nets = {}
    obstacles = []
    grid_size = None

    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    grid_size = lines[0].split('x')
    width, height = int(grid_size[0]), int(grid_size[1])


## 
    for line in lines[1:]:
        if line.startswith('OBS'):
            # Used to get the obstacles values 
            coords = re.findall(r'\((\d+),\s*(\d+)\)', line)
            if coords:
                x, y = map(int, coords[0])
                obstacles.append((x, y))
            else:
                print(f"Warning: Malformed obstacle: {line}")
        else:
            # Used to get the nets values
            parts = line.split()
            net_name = parts[0]
            pins = []
            pin_matches = re.findall(r'\((\d+),\s*(\d+)\)', line)
            for match in pin_matches:
                x, y = map(int, match)
                pins.append((x, y))

            if len(pins) != 2:
                print(f"Error: Net {net_name} does not have exactly 2 pins. Skipping.")
                continue

            nets[net_name] = pins

    return width, height, obstacles, nets


def initialize_grid(width, height, obstacles):
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            row.append(0)
        grid.append(row)
    for x, y in obstacles:
        grid[y][x] = 1
    return grid

def lee_algorithm(grid, source, target, wrong_direction_cost):
    width = len(grid[0])
    height = len(grid)
    queue = deque([source])
    visited = set([source])
    parent = {source: None}
    costs = {source: 0}

    while queue:
        current = queue.popleft()
        x, y = current
        if current == target:
            break
            # i think these are all the directions - revise later
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if grid[ny][nx] == 0:
                    direction_cost = 0
                    if dx == 0:
                        direction_cost = wrong_direction_cost
                    new_cost = costs[current] + 1 + direction_cost
                    new_pos = (nx, ny)
                    if new_pos not in costs or new_cost < costs[new_pos]:
                        costs[new_pos] = new_cost
                        parent[new_pos] = current
                        queue.append(new_pos)
                        visited.add(new_pos)

    if target in parent:
        path = []
        curr = target
        while curr is not None:
            path.append(curr)
            curr = parent[curr]
        # Reverse to gett the correctt path
        path.reverse()
        return path
    else:
        return None

def route_all_nets(width, height, obstacles, nets, wrong_direction_cost):
    grid = initialize_grid(width, height, obstacles)
    routed_nets = {}
    for net_name, pins in nets.items():
        # Mark pins as available even if we have an obsss in place- just for errors in the input file
        for x, y in pins:
            grid[y][x] = 0

        source, target = pins
        path = lee_algorithm(grid, source, target, wrong_direction_cost)
        if path is None:
            print(f"Failed to route net {net_name}")
        else:
            routed_nets[net_name] = path
            for x, y in path:
                grid[y][x] = 1
        # Mark pins as used --> for the next internation
        for x, y in pins:
            grid[y][x] = 1
    return routed_nets

def write_output_file(routed_nets, output_filename):
    with open(output_filename, 'w') as f:
        for net_name, path in routed_nets.items():
            f.write(f"{net_name} ")
            for x, y in path:
                f.write(f"({x}, {y}) ")
            f.write("\n")

## Visualize the routing
def visualize_routing(width, height, obstacles, routed_nets):
    grid = np.full((height, width), '', dtype=object)

    # mark obstacles
    for x, y in obstacles:
        grid[y][x] = 'obs'

    # mark routed paths and store source & target
    for net_name, path in routed_nets.items():
        for i, (x, y) in enumerate(path):
            if (x, y) == path[0]:
                grid[y][x] = 'S'
            elif (x, y) == path[-1]:
                grid[y][x] = 'T'
            elif grid[y][x] not in ('S', 'T'):
                grid[y][x] = str(i) 

    fig, ax = plt.subplots(figsize=(width / 2, height / 2)) #not sure
    cmap = {
        'obs': '#1f77b4',   # blue for obstacles
        'S': '#f28e2b',     # orange for source
        'T': '#76b900',     # green for target
    }

    for y in range(height):
        for x in range(width):
            val = grid[y][x]
            color = 'white'
            if val in cmap:
                color = cmap[val] # obstacle or source or target
            elif val.isdigit():
                color = '#dddddd'  # path
            ax.add_patch(plt.Rectangle((x, y), 1, 1, color=color, ec='black'))
            if val and val not in ['obs']:
                ax.text(x + 0.5, y + 0.5, val, va='center', ha='center', fontsize=8)

    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_xticks(range(width))
    ax.set_yticks(range(height))
    ax.set_xticklabels(range(width))
    ax.set_yticklabels(range(height))
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.set_title("Maze Routing Grid View")
    plt.grid(True)
    plt.savefig("routing_visualization.png")
    plt.show()





def main():

    print("======= Welcome to Lee's Algorithm Maze Router ======")

    # Get input file
    input_file = input("Enter input file name (default: input.txt): ").strip() or "input.txt"
    while not os.path.exists(input_file):
        print("❌ File not found.")
        input_file = input("Enter a valid input file name: ").strip()

    # Get output file
    output_file = input("Enter output file name (default: output.txt): ").strip() or "output.txt"

    # Get wrong direction cost
    try:
        wrong_direction_cost_input = input("Enter wrong direction cost (default: 20): ").strip()
        wrong_direction_cost = int(wrong_direction_cost_input) if wrong_direction_cost_input else 20
    except ValueError:
        print("⚠️ Invalid cost, using default value 20.")
        wrong_direction_cost = 20

    ## ========= for later ============
    # # Get VIAs cost
    # try:
    #     VIA_cost_input = input("Enter VIA cost (default: 20): ").strip()
    #     VIA_cost = int(VIA_cost_input) if VIA_cost_input else 20
    # except ValueError:
    #     print("⚠️ Invalid cost, using default value 20.")
    #     VIA_cost = 20

    print("\n Starting routing...")
    width, height, obstacles, nets = parse_input_file(input_file)
    routed_nets = route_all_nets(width, height, obstacles, nets, wrong_direction_cost)
    write_output_file(routed_nets, output_file)

    print(f"✅ Routing completed. Results saved to {output_file}")

    # visualize
    visualize = input("Do you want to generate a visualization? (y/n): ").strip().lower()
    if visualize == 'y':
        visualize_routing(width, height, obstacles, routed_nets)
        print("✅ Visualization saved as routing_visualization.png")


if __name__ == "__main__":
    main()
