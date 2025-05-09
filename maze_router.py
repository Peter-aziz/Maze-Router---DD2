VIA_COST = 50
WRONG_DIRECTION_COST = 20
from collections import deque

def parse_input_file(filename):
    grid_size = None
    obstacles = []
    nets = {}

    with open(filename, 'r') as f:
        lines = f.readlines()

    grid_size = lines[0].strip().split('x')
    width, height = int(grid_size[0]), int(grid_size[1])

    for line in lines[1:]:
        if line.startswith('OBS'):
            # Parse obstacle coordinates
            coords = line.strip()[5:-1].split(',')
            x, y = int(coords[0]), int(coords[1])
            obstacles.append((x, y))
        else:
            # Parse net definition
            parts = line.strip().split()
            net_name = parts[0]
            pins = []

            for pin_def in parts[1:]:
                pin_def = pin_def[1:-1]
                layer, x, y = map(int, pin_def.split(','))
                pins.append((layer, x, y))

            nets[net_name] = pins

    return width, height, obstacles, nets


def lee_algorithm(grid, source, target, via_cost, wrong_direction_cost):
    queue = deque([source])
    visited = set([source])
    parent = {source: None}
    costs = {source: 0}

    source_layer, source_x, source_y = source
    target_layer, target_x, target_y = target

    directions = [
        (0, 0, 1),   # right (y+1)
        (0, 0, -1),  # left (y-1)
        (0, 1, 0),   # down (x+1)
        (0, -1, 0),  # up (x-1)
        (1, 0, 0),   # via up (layer+1)
        (-1, 0, 0),  # via down (layer-1)
    ]

    def is_wrong_direction(layer, dx, dy):
        if layer == 0 and dx != 0:
            return True  # V on H
        if layer == 1 and dy != 0:
            return True  # H on V
        return False

    # Wave propagation
    while queue:
        current = queue.popleft()
        if current == target:
            break

        curr_layer, curr_x, curr_y = current
        for dl, dx, dy in directions:
            new_layer = curr_layer + dl
            new_x = curr_x + dx
            new_y = curr_y + dy
            neighbor = (new_layer, new_x, new_y)

            # Bounds and obstacle check
            if (0 <= new_layer < len(grid) and
                0 <= new_x < len(grid[0]) and
                0 <= new_y < len(grid[0][0]) and
                grid[new_layer][new_x][new_y] == 0 and
                neighbor not in visited):

                # Calculate cost
                cost = costs[current]
                if dl != 0:
                    cost += via_cost
                elif is_wrong_direction(curr_layer, dx, dy):
                    cost += wrong_direction_cost
                else:
                    cost += 1  

                visited.add(neighbor)
                costs[neighbor] = cost
                parent[neighbor] = current
                queue.append(neighbor)

    # Backtrack to find path
    path = []
    if target in parent:
        curr = target
        while curr:
            path.append(curr)
            curr = parent[curr]
        path.reverse()

    return path

def route_nets(grid, nets, via_cost, wrong_direction_cost):
    routed_paths = {}
    for net_name, pins in nets.items():
        if len(pins) != 2:
            print(f"Skipping net {net_name}: for now.")
            continue

        source, target = pins[0], pins[1]
        path = lee_algorithm(grid, source, target, via_cost, wrong_direction_cost)

        if not path:
            print(f"Routing failed for net {net_name}")
            continue

        # Mark the path on the grid
        for layer, x, y in path:
            grid[layer][y][x] = 2  # Or a unique number per net for more clarity
        routed_paths[net_name] = path

    return routed_paths

def main():
    width, height, obstacles, nets = parse_input_file("input.txt")
   

if __name__ == "__main__":
    main()
