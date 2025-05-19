# Maze Router - Lee's Algorithm Implementation

## Overview

This project implements a maze router using Lee's algorithm that supports multipin routing over two layers. The router finds paths between pins while avoiding obstacles, taking into account "wrong direction" moves and via (layer switch) costs.

## Assumptions

- **Grid Size:**  
  The first line of the input file specifies the grid size in the format `widthxheight` (e.g., `10x10`).

- **Obstacles:**  
  Obstacles are provided using the `OBS (x, y)` format. They are placed on layer 1.

- **Nets and Pins:**  
  Nets are defined with a net name followed by one or more pin coordinates in the format `(layer, x, y)`.  
  - The layer provided in the input is 1-indexed and is converted to 0-indexed internally.
  - The pin closest to the grid edge is assumed to be the source pin; the others are targets.

- **Routing Layers:**  
  The implementation assumes exactly two routing layers.
  Layer 1 preferred direction is horizontal
  Layer 2 preferred direction is vertical

- **Costs:**  
  - Moving to an adjacent cell costs 1.
  - Moves in an "unpreferred" direction incur an additional wrong direction cost (default: 20).
  - Switching layers (via move) adds a via cost (default: 20).

## How to Use

1. **Prepare the Input File**  
   Create a text file (default: `input.txt`) with the following format:
   - **Line 1:** Grid size, e.g., `10x10`
   - **Subsequent Lines:**  
     - Obstacles: `OBS (x, y)`  
     - Nets: `<net_name> (layer, x, y) (layer, x, y) ...`

2. **Run the Router**  
   Execute the script using Python:
   ```bash
   python maze_router.py
   ```
   Follow the interactive prompts to:
   - Specify the input file name (default: `input.txt`)..
   - Specify the output file name (default: `output.txt`).
   - Enter the wrong direction cost (default: 20).
   - Enter the via cost (default: 20).

3. **Output Files**  
   - The routed nets are saved to the specified output file in the following format Net_name (cell_1_layer, cell_1_x, cell_1_y) (cell_2_layer, cell_2_x, cell_2_y) ...
   - Optionally, a visualization (`routing_visualization.png`) can be generated to show the routing across the two layers.

## Limitations

- **Layer Limitation:**  
  The router supports only two layers. Expanding to more layers would require modifications to grid initialization and routing logic.

- **Scalability:**  
  Large grid sizes may lead to increased computation time due to the exhaustive nature of the search.

- **Basic Visualization:**  
  The routing visualization is simple and may not capture complex routing details or overlaps.

## Dependencies

- Python 3.x
- `matplotlib`
- `numpy`
- `re` (for regular expressions)
- `heapq` (for the priority queue)

## License

This project is licensed under the MIT License.
