#!/usr/bin/env python3
"""
PID-based grid navigator for robot1 (or any robot driven by goal_pid_controller).

BFS-plans a Manhattan path across the 25-node grid and drives the robot
through each waypoint by publishing PoseStamped to /<robot>/goal_pose.
Arrival is detected by watching the robot's odometry.
"""
import math
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from nav_msgs.msg import Path

from grid_navigation.grid_nodes import GridMap
from grid_navigation.path_planner import GridPlanner


def find_closest_node(grid_map, x, y):
    closest = None
    min_dist = float('inf')
    for node_name, (nx, ny, _) in grid_map.get_all_nodes().items():
        dist = math.hypot(nx - x, ny - y)
        if dist < min_dist:
            min_dist = dist
            closest = node_name
    return closest


class PidGridNavigator(Node):
    def __init__(self):
        super().__init__('pid_grid_navigator')

        self.declare_parameter('robot_name', 'robot1')
        self.declare_parameter('dest_node', 'N25')
        self.declare_parameter('odom_topic', 'odometry/global_amcl')
        self.declare_parameter('arrival_tolerance', 0.08)
        self.declare_parameter('waypoint_timeout', 60.0)
        self.declare_parameter('grid_spacing', 1.0)

        self.robot_name = self.get_parameter('robot_name').value
        self.dest_node = self.get_parameter('dest_node').value
        odom_topic = self.get_parameter('odom_topic').value
        self.tolerance = float(self.get_parameter('arrival_tolerance').value)
        self.timeout = float(self.get_parameter('waypoint_timeout').value)
        spacing = float(self.get_parameter('grid_spacing').value)

        self.grid = GridMap(spacing=spacing, start_x=0.0, start_y=0.0)
        self.planner = GridPlanner(cols=5, rows=5)

        self.current_x = None
        self.current_y = None

        self.goal_pub = self.create_publisher(
            PoseStamped, f'/{self.robot_name}/goal_pose', 10)
        self.path_pub = self.create_publisher(
            Path, f'/{self.robot_name}/grid_path', 10)
        self.create_subscription(
            Odometry,
            f'/{self.robot_name}/{odom_topic}',
            self.odom_callback,
            10,
        )

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

    def wait_for_odom(self, timeout=5.0):
        deadline = time.time() + timeout
        while self.current_x is None and time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
        return self.current_x is not None

    def publish_goal(self, x, y):
        msg = PoseStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.position.x = float(x)
        msg.pose.position.y = float(y)
        msg.pose.orientation.w = 1.0
        self.goal_pub.publish(msg)

    def publish_path_to_rviz(self, path_coords):
        msg = Path()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        for (x, y) in path_coords:
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.header.stamp = msg.header.stamp
            pose.pose.position.x = float(x)
            pose.pose.position.y = float(y)
            pose.pose.orientation.w = 1.0
            msg.poses.append(pose)
        self.path_pub.publish(msg)

    def drive_to_waypoint(self, x, y):
        """Republishes the goal at 2 Hz until the robot is within tolerance or times out."""
        start = time.time()
        # Republish periodically; the PID controller resets its integral on
        # every goal message, so we send it once and then only re-send if
        # progress stalls.
        self.publish_goal(x, y)
        last_republish = time.time()
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.current_x is None:
                continue
            dist = math.hypot(x - self.current_x, y - self.current_y)
            if dist < self.tolerance:
                return True
            if time.time() - start > self.timeout:
                self.get_logger().warn(
                    f'Timed out reaching ({x:.2f}, {y:.2f}); '
                    f'last error {dist * 100:.1f} cm')
                return False
            # Re-publish the goal every 5 s in case the PID missed the first
            # message due to DDS discovery.
            if time.time() - last_republish > 5.0:
                self.publish_goal(x, y)
                last_republish = time.time()

    def run(self):
        dest = self.grid.get_node(self.dest_node)
        if dest is None:
            self.get_logger().error(f'Unknown destination node {self.dest_node}')
            return

        if not self.wait_for_odom(timeout=5.0):
            self.get_logger().error(
                f'No odometry received on /{self.robot_name}/'
                f'{self.get_parameter("odom_topic").value}; aborting.')
            return

        start_node = find_closest_node(self.grid, self.current_x, self.current_y)
        self.get_logger().info(
            f'{self.robot_name} at ({self.current_x:.2f}, {self.current_y:.2f}); '
            f'snapping to {start_node} and planning to {self.dest_node}.')

        path = self.planner.plan_path(start_node, self.dest_node)
        if not path:
            self.get_logger().error(
                f'No path found from {start_node} to {self.dest_node}')
            return

        self.get_logger().info('Path: ' + ' -> '.join(path))
        path_coords = [self.grid.get_node(n)[:2] for n in path]
        self.publish_path_to_rviz(path_coords)

        for i, node_name in enumerate(path):
            x, y, _ = self.grid.get_node(node_name)
            self.get_logger().info(
                f'[{i + 1}/{len(path)}] Driving to {node_name} at ({x:.2f}, {y:.2f})')
            if not self.drive_to_waypoint(x, y):
                self.get_logger().error(
                    f'Failed to reach {node_name}; aborting remaining path.')
                return

        self.get_logger().info(f'Reached destination {self.dest_node}.')


def main():
    rclpy.init()
    node = PidGridNavigator()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
