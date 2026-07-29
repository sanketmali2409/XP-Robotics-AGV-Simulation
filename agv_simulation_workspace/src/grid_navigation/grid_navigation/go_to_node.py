#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import argparse
import math
import time
from nav_msgs.msg import Odometry

from grid_navigation.grid_nodes import GridMap
from grid_navigation.path_planner import GridPlanner
from grid_navigation.navigator import Nav2Client

class OdomReader(Node):
    def __init__(self, robot_name):
        super().__init__('grid_odom_reader')
        self.current_x = None
        self.current_y = None
        
        # Subscribe to AMCL odometry for robot2 and robot3
        self.sub = self.create_subscription(
            Odometry,
            f'/{robot_name}/odometry/global_amcl',
            self.odom_callback,
            10
        )
        
    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

def find_closest_node(grid_map, x, y):
    closest = None
    min_dist = float('inf')
    for node_name, (nx, ny, nyaw) in grid_map.get_all_nodes().items():
        dist = math.hypot(nx - x, ny - y)
        if dist < min_dist:
            min_dist = dist
            closest = node_name
    return closest

def main():
    rclpy.init()
    
    # Setup temp node to read parameters
    temp_node = rclpy.node.Node('grid_nav_dynamic_init')
    temp_node.declare_parameter('robot_name', 'robot3')
    temp_node.declare_parameter('dest_node', 'N25')
    
    robot_name = temp_node.get_parameter('robot_name').value
    dest_node = temp_node.get_parameter('dest_node').value
    temp_node.destroy_node()
    
    grid = GridMap(spacing=1.0, start_x=0.0, start_y=0.0)
    planner = GridPlanner(cols=5, rows=5)
    dest = grid.get_node(dest_node)
    if dest is None:
        print(f"ERROR: Unknown destination node {dest_node}")
        rclpy.shutdown()
        return

    # Snap the robot's current pose to the nearest grid node so the planner
    # can build an L-shaped Manhattan path that steps through every node
    # between the start and the destination.
    odom_reader = OdomReader(robot_name)
    start_time = time.time()
    while odom_reader.current_x is None and time.time() - start_time < 5.0:
        rclpy.spin_once(odom_reader, timeout_sec=0.2)

    if odom_reader.current_x is None:
        print(f"WARN: No odometry for {robot_name}; defaulting start to N1.")
        start_node = 'N1'
    else:
        start_node = find_closest_node(
            grid, odom_reader.current_x, odom_reader.current_y)
        print(f"INFO: {robot_name} at "
              f"({odom_reader.current_x:.2f}, {odom_reader.current_y:.2f}); "
              f"snapping to {start_node}.")
    odom_reader.destroy_node()

    path = planner.plan_path(start_node, dest_node)
    if not path:
        print(f"ERROR: No path from {start_node} to {dest_node}.")
        rclpy.shutdown()
        return
    print(f"INFO: L-shaped path: {' -> '.join(path)}")

    navigator = Nav2Client(robot_name=robot_name)
    try:
        path_coords = [grid.get_node(n)[:2] for n in path]
        navigator.publish_path_to_rviz(path_coords)

        for i, node_name in enumerate(path):
            x, y, yaw = grid.get_node(node_name)
            navigator.get_logger().info(
                f"[{i+1}/{len(path)}] Navigating to {node_name} "
                f"at ({x:.2f}, {y:.2f})")
            if not navigator.navigate_to_pose(x, y, yaw):
                navigator.get_logger().warn(
                    f"Nav2 failed at {node_name}; aborting remaining path.")
                return
        navigator.get_logger().info(f"Reached {dest_node}.")
    except KeyboardInterrupt:
        pass
    finally:
        navigator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
