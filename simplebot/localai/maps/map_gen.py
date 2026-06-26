#!/usr/bin/env python3
import re

def generate_ascii_map(file_path):
    points = []
    
    # 1. Parse the coordinates from the file
    try:
        with open(file_path, 'r') as f:
            for line in f:
                # Matches patterns like x=15.5, y=-10.2
                match = re.search(r"x=\s*([-+]?\d*\.\d+|\d+),\s*y=\s*([-+]?\d*\.\d+|\d+)", line)
                if match:
                    points.append((float(match.group(1)), float(match.group(2))))
    except FileNotFoundError:
        print("Error: simple_map.txt not found.")
        return

    if not points:
        print("No coordinate data found in file.")
        return

    # 2. Normalize coordinates to a grid
    # We find the min/max to size our ASCII "canvas"
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)

    # Padding and scale (adjust scale if the map is too big/small)
    scale = 5.0  # Every 5cm is 1 character
    width = int((max_x - min_x) / scale) + 3
    height = int((max_y - min_y) / scale) + 3

    # Initialize grid with empty space
    grid = [[" " for _ in range(width)] for _ in range(height)]

    # 3. Draw the path
    for i, (px, py) in enumerate(points):
        # Convert cm to grid indices
        grid_x = int((px - min_x) / scale) + 1
        grid_y = int((py - min_y) / scale) + 1
        
        if i == 0:
            grid[grid_y][grid_x] = "S"  # Start point
        elif i == len(points) - 1:
            grid[grid_y][grid_x] = "B"  # Current Bot position
        else:
            # Only draw a dot if it's not overwriting the Start
            if grid[grid_y][grid_x] == " ":
                grid[grid_y][grid_x] = "."

    # 4. Print the map with a border
    print("\n--- Z-Bot Path Map ---")
    print("+" + "-" * width + "+")
    # Reverse Y axis so positive is "up" on the screen
    for row in reversed(grid):
        print("|" + "".join(row) + "|")
    print("+" + "-" * width + "+")
    print("Legend: S=Start, B=Bot, .=Path (Scale: 1 char = 5cm)")

if __name__ == "__main__":
    generate_ascii_map("simple_map.txt")

