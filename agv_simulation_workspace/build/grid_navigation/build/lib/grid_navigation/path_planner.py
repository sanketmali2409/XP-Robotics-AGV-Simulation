#!/usr/bin/env python3
from collections import deque

class GridPlanner:
    """
    Handles path planning on the 5x5 grid.
    Ensures the robot only moves in straight-line segments between connected nodes.
    """
    def __init__(self, cols=5, rows=5):
        self.cols = cols
        self.rows = rows

    def get_neighbors(self, node_id):
        """Returns valid adjacent node IDs (Up, Down, Left, Right)."""
        neighbors = []
        idx = node_id - 1
        row = idx // self.cols
        col = idx % self.cols

        if col > 0: # Left
            neighbors.append(node_id - 1)
        if col < self.cols - 1: # Right
            neighbors.append(node_id + 1)
        if row > 0: # Up
            neighbors.append(node_id - self.cols)
        if row < self.rows - 1: # Down
            neighbors.append(node_id + self.cols)

        return neighbors

    def plan_path(self, start_node, dest_node):
        """
        Uses Breadth-First Search (BFS) to find the shortest sequence of nodes
        from start_node to dest_node.
        Expects node names like 'N1', 'N25'. Returns a list of node names.
        """
        start_id = int(start_node[1:])
        dest_id = int(dest_node[1:])

        if start_id == dest_id:
            return [start_node]

        queue = deque([[start_id]])
        visited = set([start_id])

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == dest_id:
                return [f"N{node}" for node in path]

            for neighbor in self.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)

        return [] # No path found
