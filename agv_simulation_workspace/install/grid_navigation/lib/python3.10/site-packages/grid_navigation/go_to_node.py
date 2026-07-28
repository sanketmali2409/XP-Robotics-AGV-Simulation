#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import argparse
import math
from nav_msgs.msg import Odometry

from grid_navigation.grid_nodes import GridMap
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
    
    # Log the robot's current pose for context, then send ONE Nav2 goal
    # straight to the destination node. Nav2's global planner will pick the
    # optimal path from wherever the robot currently is — no detour through
    # a "closest grid node" first.
    grid = GridMap(spacing=1.0, start_x=0.0, start_y=0.0)
    dest = grid.get_node(dest_node)
    if dest is None:
        print(f"ERROR: Unknown destination node {dest_node}")
        rclpy.shutdown()
        return
    dest_x, dest_y, dest_yaw = dest

    odom_reader = OdomReader(robot_name)
    rclpy.spin_once(odom_reader, timeout_sec=2.0)
    if odom_reader.current_x is not None:
        print(f"INFO: {robot_name} currently at "
              f"({odom_reader.current_x:.2f}, {odom_reader.current_y:.2f}), "
              f"sending direct Nav2 goal to {dest_node} "
              f"({dest_x:.2f}, {dest_y:.2f}).")
    else:
        print(f"WARN: Could not read odometry for {robot_name}; sending goal anyway.")
    odom_reader.destroy_node()

    navigator = Nav2Client(robot_name=robot_name)
    try:
        # Publish the straight start->goal line to RViz so the operator sees
        # the intent, even though Nav2 may curve around obstacles.
        if odom_reader.current_x is not None:
            navigator.publish_path_to_rviz([
                (odom_reader.current_x, odom_reader.current_y),
                (dest_x, dest_y),
            ])
        ok = navigator.navigate_to_pose(dest_x, dest_y, dest_yaw)
        if ok:
            navigator.get_logger().info(f"Reached {dest_node}.")
        else:
            navigator.get_logger().warn(f"Nav2 failed to reach {dest_node}.")
    except KeyboardInterrupt:
        pass
    finally:
        navigator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
