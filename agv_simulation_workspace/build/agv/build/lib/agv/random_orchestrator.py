#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
import math
import time

class SequenceOrchestrator(Node):
    def __init__(self):
        super().__init__('sequence_orchestrator')
        
        self.declare_parameter('robot_name', 'robot1')
        self.declare_parameter('odom_topic', 'odometry/filtered')
        
        self.robot_name = self.get_parameter('robot_name').value
        odom_topic = self.get_parameter('odom_topic').value
        
        # 6 Waypoints from the test
        self.waypoints = [
            (1.0, 1.0),
            (2.0, 1.0),
            (1.0, 1.0),
            (0.0, 1.0),
            (-1.0, 1.0),
            (0.0, 1.0)
        ]
        
        self.current_wp_idx = 0
        self.current_x = 0.0
        self.current_y = 0.0
        self.min_error_for_current_wp = float('inf')
        self.all_errors = []
        
        self.goal_active = False
        self.goal_start_time = 0.0
        
        # Publishers and Subscribers
        self.pub = self.create_publisher(PoseStamped, f'/{self.robot_name}/goal_pose', 10)
        self.odom_sub = self.create_subscription(Odometry, f'/{self.robot_name}/{odom_topic}', self.odom_callback, 10)
        
        self.get_logger().info(f"--- Starting 6-Goal Sequence for {self.robot_name} ---")
        
        # Timer to run the state machine
        self.timer = self.create_timer(0.5, self.control_loop)

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        
        if self.goal_active:
            # Track the minimum error achieved during this waypoint's travel
            target_x, target_y = self.waypoints[self.current_wp_idx]
            dist = math.sqrt((target_x - self.current_x)**2 + (target_y - self.current_y)**2)
            if dist < self.min_error_for_current_wp:
                self.min_error_for_current_wp = dist

    def control_loop(self):
        if self.current_wp_idx >= len(self.waypoints):
            self.get_logger().info("🎉 All goals completed! Test sequence finished.")
            if hasattr(self, 'all_errors') and len(self.all_errors) > 0:
                avg = sum(self.all_errors) / len(self.all_errors)
                self.get_logger().info(f"📊 OVERALL SEQUENCE AVERAGE ARRIVAL ERROR: {avg * 100:.2f} cm")
            self.timer.cancel()
            rclpy.shutdown()
            return

        target_x, target_y = self.waypoints[self.current_wp_idx]

        if not self.goal_active:
            self.goal_active = True
            self.goal_start_time = time.time()
            self.min_error_for_current_wp = float('inf')
            self.get_logger().info(f"Commanded {self.robot_name} to Waypoint {self.current_wp_idx + 1} at ({target_x}, {target_y})")
            
        # Continuously publish the goal in case the controller missed the first one due to DDS discovery
        self.publish_goal(target_x, target_y)
            
        # Check if goal is reached or timed out
        elapsed = time.time() - self.goal_start_time
        
        dist = math.sqrt((target_x - self.current_x)**2 + (target_y - self.current_y)**2)
        
        # If it reaches within 5cm, consider it a success and move on
        if dist < 0.05:
            self.get_logger().info(f"✅ Waypoint {self.current_wp_idx + 1} Reached! Minimum Error: {self.min_error_for_current_wp * 100:.2f} cm")
            self.advance_goal()
        elif elapsed > 300.0:
            # If it takes more than 300 seconds (real time), it probably hit a wall and got stuck
            self.get_logger().warn(f"❌ TIMEOUT: Waypoint {self.current_wp_idx + 1} failed. Minimum Error achieved before getting stuck: {self.min_error_for_current_wp * 100:.2f} cm")
            self.advance_goal()

    def advance_goal(self):
        if hasattr(self, 'all_errors') and self.min_error_for_current_wp != float('inf'):
            self.all_errors.append(self.min_error_for_current_wp)
        self.current_wp_idx += 1
        self.goal_active = False

    def publish_goal(self, x, y):
        goal_msg = PoseStamped()
        goal_msg.header.frame_id = "map"
        goal_msg.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.position.x = float(x)
        goal_msg.pose.position.y = float(y)
        goal_msg.pose.orientation.w = 1.0 
        self.pub.publish(goal_msg)

def main(args=None):
    rclpy.init(args=args)
    node = SequenceOrchestrator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

if __name__ == '__main__':
    main()
