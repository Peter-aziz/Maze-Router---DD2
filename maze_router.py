from collections import deque
import matplotlib.pyplot as plt
import numpy as np
import re

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

## Visualize the routing -- add a visualtisation function here







def main():
    import argparse
    parser = argparse.ArgumentParser(description='Lee\'s Algorithm Maze Router (1 layer, 2-pin nets)')
    parser.add_argument('input_file', help='Input file with grid and net definitions')
    parser.add_argument('output_file', help='Output file for routing results')
    parser.add_argument('--wrong_direction_cost', type=int, default=20, help='Cost for routing in non-preferred direction')
    args = parser.parse_args()

    width, height, obstacles, nets = parse_input_file(args.input_file)
    routed_nets = route_all_nets(width, height, obstacles, nets, args.wrong_direction_cost)
    write_output_file(routed_nets, args.output_file)
    print(f"Routing completed. Results written to {args.output_file}")
    # call the visualization function
    
    print(f"Visualization saved as routing_visualization.png")

if __name__ == "__main__":
    main()
