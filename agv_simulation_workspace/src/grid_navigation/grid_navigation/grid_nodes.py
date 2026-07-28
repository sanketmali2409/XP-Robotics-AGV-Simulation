#!/usr/bin/env python3

class GridMap:
    """
    Stores and generates a 5x5 grid of predefined navigation nodes.
    By default, N1 is at (0.0, 0.0). N2 is at (spacing, 0.0), etc.
    """
    def __init__(self, spacing=1.0, start_x=0.0, start_y=0.0):
        self.nodes = {}
        self.spacing = spacing
        self.generate_grid(start_x, start_y)

    def generate_grid(self, start_x, start_y):
        """
        Generates 25 nodes labeled N1 to N25 in a 5x5 grid layout.
        Example layout:
        N1  N2  N3  N4  N5
        N6  N7  N8  N9  N10
        ...
        N21 N22 N23 N24 N25
        """
        node_id = 1
        for row in range(5):
            for col in range(5):
                # Calculate Cartesian coordinates. 
                # Moving right increases X, moving down decreases Y.
                x = start_x + (col * self.spacing)
                y = start_y - (row * self.spacing) 
                yaw = 0.0 # Default orientation
                
                self.nodes[f"N{node_id}"] = (x, y, yaw)
                node_id += 1

    def get_node(self, node_name):
        """Returns the (x, y, yaw) coordinates of a given node name, or None if invalid."""
        return self.nodes.get(node_name)

    def get_all_nodes(self):
        """Returns the dictionary of all nodes."""
        return self.nodes
