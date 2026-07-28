#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path

class Nav2Client(Node):
    """
    Handles communication with the Nav2 NavigateToPose action server.
    Provides a simple blocking method to send a goal and wait for its completion.
    """
    def __init__(self, robot_name):
        super().__init__(f'{robot_name}_grid_navigator')
        self.robot_name = robot_name
        self.action_client = ActionClient(self, NavigateToPose, f'/{robot_name}/navigate_to_pose')
        
        # Publisher to visualize the path in RViz
        self.path_pub = self.create_publisher(Path, f'/{robot_name}/grid_path', 10)
        
        # Wait for the action server to be available
        self.get_logger().info(f"Waiting for Nav2 action server for {self.robot_name}...")
        self.action_client.wait_for_server()
        self.get_logger().info("Nav2 action server connected.")

    def navigate_to_pose(self, x, y, yaw=0.0):
        """
        Sends a single NavigateToPose goal and waits for completion.
        Returns True if successful, False otherwise.
        """
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        
        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.position.z = 0.0
        
        # Simple yaw to quaternion (yaw is in radians)
        import math
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.get_logger().info(f"Sending goal to ({x:.2f}, {y:.2f})...")

        # Send the goal asynchronously
        send_goal_future = self.action_client.send_goal_async(goal_msg)
        
        # Wait for the server to accept or reject the goal
        rclpy.spin_until_future_complete(self, send_goal_future)
        goal_handle = send_goal_future.result()

        if not goal_handle.accepted:
            self.get_logger().error("Goal was rejected by server!")
            return False

        self.get_logger().info("Goal accepted by server, waiting for result...")
        
        # Wait for the result
        get_result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, get_result_future)
        
        status = get_result_future.result().status
        
        # Status 4 corresponds to SUCCEEDED in actionlib
        if status == 4:
            self.get_logger().info("✅ Goal successfully reached!")
            return True
        else:
            self.get_logger().warn(f"❌ Goal failed or was canceled. Status: {status}")
            return False

    def publish_path_to_rviz(self, path_coords):
        """
        Takes a list of (x, y) tuples and publishes them as a nav_msgs/Path
        so it can be visualized in RViz.
        """
        path_msg = Path()
        path_msg.header.frame_id = 'map'
        path_msg.header.stamp = self.get_clock().now().to_msg()
        
        for (x, y) in path_coords:
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.header.stamp = path_msg.header.stamp
            pose.pose.position.x = float(x)
            pose.pose.position.y = float(y)
            pose.pose.position.z = 0.0
            pose.pose.orientation.w = 1.0
            path_msg.poses.append(pose)
            
        self.path_pub.publish(path_msg)
        self.get_logger().info("Published planned path to RViz.")
