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

    def _row_col(self, node_id):
        idx = node_id - 1
        return idx // self.cols, idx % self.cols

    def _id(self, row, col):
        return row * self.cols + col + 1

    def plan_path(self, start_node, dest_node):
        """
        Builds an L-shaped Manhattan path from start_node to dest_node:
        step horizontally along the start row until the destination column is
        reached, then step vertically along that column to the destination.
        The robot therefore passes through every node in between (a full row
        segment followed by a full column segment).
        Expects node names like 'N1', 'N25'. Returns a list of node names.
        """
        start_id = int(start_node[1:])
        dest_id = int(dest_node[1:])

        if start_id == dest_id:
            return [start_node]

        r1, c1 = self._row_col(start_id)
        r2, c2 = self._row_col(dest_id)

        path_ids = [start_id]

        # Horizontal leg: walk across the start row to the destination column.
        col_step = 1 if c2 > c1 else -1
        col = c1
        while col != c2:
            col += col_step
            path_ids.append(self._id(r1, col))

        # Vertical leg: walk down (or up) the destination column to the goal.
        row_step = 1 if r2 > r1 else -1
        row = r1
        while row != r2:
            row += row_step
            path_ids.append(self._id(row, c2))

        return [f"N{n}" for n in path_ids]
