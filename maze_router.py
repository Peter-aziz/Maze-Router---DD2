from collections import deque
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
matplotlib.use('TkAgg')
import numpy as np
import re
import os

# ------------------------------- HELPER FUNCTIONS -------------------------------
#validate input
def is_valid(file_path):
    try:
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        # Validate grid size
        grid_line = lines[0]
        if not re.match(r'^\d+x\d+$', grid_line):
            print("Invalid grid size format.")
            return False
        width, height = map(int, grid_line.split('x'))
        if not (1 <= width <= 1000 and 1 <= height <= 1000):
            print("Grid size out of allowed bounds (1 to 1000).")
            return False
        # Validate obstacles
        for line in lines[1:]:
            if line.startswith("OBS"):
                if not re.match(r'^OBS\s*\(\d+,\s*\d+\)$', line):
                    print(f"Invalid obstacle format: {line}")
                    return False
                x, y = map(int, re.findall(r'\d+', line))
                if not (0 <= x < width and 0 <= y < height):
                    print(f"Obstacle out of bounds: {line}")
                    return False
            else:
                # Validate nets
                match = re.match(r'^(\w+)((\s*\(\d+,\s*\d+,\s*\d+\))+)$', line)
                if not match:
                    print(f"Invalid net format: {line}")
                    return False
                coords = re.findall(r'\(\d+,\s*\d+,\s*\d+\)', line)
                for c in coords:
                    l, x, y = map(int, re.findall(r'\d+', c))
                    if not (0 <= x < width and 0 <= y < height and 1<= l <= 2):
                        print(f"Pin out of bounds in net: {line}")
                        return False

        return True
    except Exception as e:
        print(f"Error while reading the file: {e}")
        return False
    
# parse input
def parse_input_file(filename):
    nets = {}
    obstacles = []
    grid_size = None

    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    grid_size = lines[0].split('x')
    width, height = int(grid_size[0]), int(grid_size[1])

    for line in lines[1:]:
        if line.startswith('OBS'):
            # Used to get the obstacles values 
            coords = re.findall(r'\((\d+),\s*(\d+)\)', line)
            if coords:
                x, y = map(int, coords[0])
                obstacles.append((x, y))
        else:
           # Used to get the nets values
            parts = line.split()
            net_name = parts[0]
            pins = []
            pin_matches = re.findall(r'\((\d+),\s*(\d+),\s*(\d+)\)', line)
            for match in pin_matches:
                layer, x, y = map(int, match)
                pins.append((layer-1, x, y))   # subtract one from the layer
            nets[net_name] = pins

    return width, height, obstacles, nets

# choose the sources as the ones closer to the edges
def reorder_pins (nets, chip_width, chip_height):
    new_nets = {}

    for net_name, pins in nets.items():
        def distance_to_edge(pin):
            _, x, y = pin
            return min(x, y, chip_width - x, chip_height - y)

        # Find source pin (closest to edge)
        source = min(pins, key=distance_to_edge)

        reordered_pins = [source] + [pin for pin in pins if pin != source]

        new_nets[net_name] = reordered_pins

    return new_nets

# reorder the nets based on the sum of manhattan distances (shortest first)
def reorder_nets_by_manhattan_distance(nets):
    def net_manhattan_score(pin_list):
        score = 0
        for i in range(len(pin_list)):
            for j in range(i + 1, len(pin_list)):
                _, x1, y1 = pin_list[i]
                _, x2, y2 = pin_list[j]
                score += abs(x1 - x2) + abs(y1 - y2)
        return score

    sorted_nets = dict(sorted(nets.items(), key=lambda item: net_manhattan_score(item[1])))
    return sorted_nets


# initialize grid
def initialize_grid(width, height, obstacles):
     # Create two layers: each is a 2D grid of zeros
    layer1 = [[0 for _ in range(width)] for _ in range(height)]
    layer2 = [[0 for _ in range(width)] for _ in range(height)]

    # Mark obstacles in both layers
    for x, y in obstacles:
        layer1[y][x] = 1

    return [layer1, layer2]  

# write output
def write_output_file(routed_nets, output_filename):
    with open(output_filename, 'w') as f:
        for net_name, path in routed_nets.items():
            f.write(f"{net_name} ")
            for layer, x, y in path:
                f.write(f"({layer+1}, {x}, {y}) ")
            f.write("\n")

# Visualize the routed nets
def visualize_routing(width, height, obstacles, routed_nets, nets):
    layer_grids = [np.full((height, width), '', dtype=object) for _ in range(2)]
    via_positions = set()

    # Mark obstacles in layer 1 (index 0)
    for (x, y) in obstacles:
        layer_grids[0][y][x] = 'obs'  # Mark obstacle cell with 'obs'

    # Identify via positions for reference
    for net_name, path in routed_nets.items():
        for j in range(1, len(path)):
            prev_layer, x1, y1 = path[j - 1]
            curr_layer, x2, y2 = path[j]
            if (x1, y1) == (x2, y2) and prev_layer != curr_layer:
                via_positions.add((x1, y1))

    # Collect all pin positions across all nets for quick lookup
    pins_positions = set()
    for pin_list in nets.values():
        for layer, x, y in pin_list:
            pins_positions.add((layer, x, y))

    for net_name, path in routed_nets.items():
        for i, (layer, x, y) in enumerate(path):
            is_via = (x, y) in via_positions
            is_pin = (layer, x, y) in pins_positions
            step_num = i + 1  # 1-based step numbering

            if is_pin:
                label = f"{step_num}"
                if is_via:
                    label += " v"
            else:
                # Non-pin steps
                if i == 0:
                    label = f"S {step_num}"
                    if is_via:
                        label += " v"
                elif i == len(path) - 1:
                    label = f"T {step_num}"
                    if is_via:
                        label += " v"
                else:
                    label = f"{step_num}"
                    if is_via:
                        label += " v"

            layer_grids[layer][y][x] = label

    # Colors
    cmap = {
        'obs': '#1f77b4',  # blue
        'P': '#76b900',    # green for pins
        'S': '#f28e2b',    # orange for source prefix
        'T': '#76b900',    # green for target prefix (same as pin)
    }

    fig, axs = plt.subplots(1, 2, figsize=(width * 1.2, height))
    for layer in [0, 1]:
        ax = axs[layer]
        ax.set_title(f"Layer {layer + 1}")
        for y in range(height):
            for x in range(width):
                val = layer_grids[layer][y][x]
                color = 'white'
                if val == 'obs':
                    color = cmap['obs']
                elif (layer, x, y) in pins_positions:
                    color = cmap['P']   # Use pin color if it's a pin cell, regardless of label prefix
                elif val.startswith('S'):
                    color = cmap['S']
                elif val.startswith('T'):
                    color = cmap['T']
                elif val != '':
                    color = '#dddddd'  # light grey for path

                ax.add_patch(plt.Rectangle((x, y), 1, 1, color=color, ec='black'))
                if val and val != 'obs':
                    ax.text(x + 0.5, y + 0.5, val, va='center', ha='center', fontsize=8)

        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        ax.set_xticks(range(width))
        ax.set_yticks(range(height))
        ax.set_aspect('equal')
        ax.invert_yaxis()
        ax.grid(True)

    plt.suptitle("Maze Routing - Side-by-Side Layer Visualization with Vias and Numbering")
    plt.tight_layout()
    plt.savefig("routing_visualization.png")
    plt.show()

# ------------------------------- LEE MAZE ALG. MULTIPIN -------------------------------
def lee_algorithm_multisource(grid, pins, wrong_direction_cost, via_cost=20):
    import heapq
    width = len(grid[0][0])
    height = len(grid[0])
    
    # Start from the first pin as initial source.
    sources = set([pins[0]])
    targets = set(pins[1:])
    full_path = []
    
    while targets:
        # Use a heap-based priority queue to always expand the lowest cost node next.
        heap = []
        for s in sources:
            heapq.heappush(heap, (0, s))
        parent = {pos: None for pos in sources}
        costs = {pos: 0 for pos in sources}
        found_target = None

        while heap:
            curr_cost, current = heapq.heappop(heap)
            layer, x, y = current

            # If we reached one of the target pins, stop.
            if current in targets:
                found_target = current
                break

            # Explore 4 cardinal directions.
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    # Allow expansion if cell is free or it is a target.
                    if grid[layer][ny][nx] == 0 or (layer, nx, ny) in targets:
                        # Add wrong direction cost depending on the current layer.
                        direction_cost = 0
                        if (layer == 0 and dx == 0) or (layer == 1 and dy == 0):
                            direction_cost = wrong_direction_cost
                        new_cost = curr_cost + 1 + direction_cost
                        new_pos = (layer, nx, ny)
                        if new_pos not in costs or new_cost < costs[new_pos]:
                            costs[new_pos] = new_cost
                            parent[new_pos] = current
                            heapq.heappush(heap, (new_cost, new_pos))

            # Try switching layers (via move).
            other_layer = 1 - layer
            if grid[other_layer][y][x] == 0 or (other_layer, x, y) in targets:
                via_pos = (other_layer, x, y)
                new_cost = curr_cost + via_cost
                if via_pos not in costs or new_cost < costs[via_pos]:
                    costs[via_pos] = new_cost
                    parent[via_pos] = current
                    heapq.heappush(heap, (new_cost, via_pos))
        
        if found_target is None:
            print("Failed to connect all pins.")
            return None  # Cannot connect all pins

        # Traceback the path from the found target.
        path = []
        curr = found_target
        while curr is not None:
            path.append(curr)
            curr = parent[curr]
        path.reverse()

        # Mark the traced path as part of the source for subsequent connections.
        for cell in path:
            sources.add(cell)
            grid[cell[0]][cell[2]][cell[1]] = 1  # Mark the cell as occupied
        full_path.extend(path)
        targets.remove(found_target)

    return full_path


# ------------------------------- ROUTING FUNCTION -------------------------------
def route_all_nets(width, height, obstacles, nets, wrong_direction_cost, via_cost=20):
    grid = initialize_grid(width, height, obstacles)
    routed_nets = {}

    for net_name, pins in nets.items():
        # Ensure pins are clear in the grid
        for layer, x, y in pins:
            grid[layer][y][x] = 0

        path = lee_algorithm_multisource(grid, pins, wrong_direction_cost, via_cost)
        if path is None:
            print(f"Failed to route net {net_name}")
        else:
            routed_nets[net_name] = path
            for layer, x, y in path:
                grid[layer][y][x] = 1

        # Mark pins as occupied for next net
        for layer, x, y in pins:
            grid[layer][y][x] = 1

    return routed_nets

#================================== MAIN ==================================
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

     # Get VIAs cost
    try:
        VIA_cost_input = input("Enter VIA cost (default: 20): ").strip()
        VIA_cost = int(VIA_cost_input) if VIA_cost_input else 20
    except ValueError:
        print("⚠️ Invalid cost, using default value 20.")
        VIA_cost = 20

    print("\n")
    if is_valid(input_file):
        print("\n Starting routing...")
        
        width, height, obstacles, nets = parse_input_file(input_file)
        new_nets = reorder_pins(nets, width, height)
        reordered_nets = reorder_nets_by_manhattan_distance(new_nets)
        routed_nets = route_all_nets(width, height, obstacles, reordered_nets, wrong_direction_cost, VIA_cost)

        routed_nets = route_all_nets(width, height, obstacles, new_nets, wrong_direction_cost, VIA_cost)
        write_output_file(routed_nets, output_file)

        print(f"✅ Routing completed. Results saved to {output_file}")

    else:
        print("Couldn't start routing...")

    # visualize
    visualize = input("Do you want to generate a visualization? (y/n): ").strip().lower()
    if visualize == 'y':
        visualize_routing(width, height, obstacles, routed_nets, new_nets)
        print("✅ Visualization saved as routing_visualization.png")
if __name__ == "__main__":
    main()
