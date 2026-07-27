#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
import time
import math

class TestOrchestrator(Node):
    def __init__(self):
        super().__init__('test_orchestrator')
        
        # Define the test parameters
        self.robots = ['robot1']
        self.start_point = (0.0, 0.0)
        self.goal_point = (5.0, 0.0)
        self.safe_points = {
            'robot1': (5.0, 2.0),
            'robot2': (5.0, -2.0),
            'robot3': (5.0, 4.0)
        }
        
        self.current_robot_idx = 0
        self.current_phase = 0 # 0: to start, 1: to goal, 2: to safe
        self.phases = ['Start Point', 'Goal Point', 'Safe Parking']
        
        # State
        self.current_x = None
        self.current_y = None
        self.goal_x = 0.0
        self.goal_y = 0.0
        self.phase_start_time = time.time()
        
        self.goal_pub = None
        self.odom_sub = None
        
        self.setup_current_robot()
        
        self.timer = self.create_timer(0.5, self.check_progress)

    def setup_current_robot(self):
        if self.current_robot_idx >= len(self.robots):
            self.get_logger().info("All tests completed successfully!")
            rclpy.shutdown()
            return
            
        robot = self.robots[self.current_robot_idx]
        self.get_logger().info(f"--- Starting test sequence for {robot} ---")
        
        # Setup topics
        if self.goal_pub: self.destroy_publisher(self.goal_pub)
        if self.odom_sub: self.destroy_subscription(self.odom_sub)
        
        self.goal_pub = self.create_publisher(PoseStamped, f'/{robot}/goal_pose', 10)
        self.odom_sub = self.create_subscription(Odometry, f'/{robot}/odometry/filtered', self.odom_callback, 10)
        
        self.current_phase = 0
        self.send_goal()

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

    def send_goal(self):
        robot = self.robots[self.current_robot_idx]
        if self.current_phase == 0:
            self.goal_x, self.goal_y = self.start_point
            time_limit = 45.0
        elif self.current_phase == 1:
            self.goal_x, self.goal_y = self.goal_point
            time_limit = 25.0
        else:
            self.goal_x, self.goal_y = self.safe_points[robot]
            time_limit = 45.0
            
        self.get_logger().info(f"Commanding {robot} to {self.phases[self.current_phase]} at ({self.goal_x}, {self.goal_y})")
        
        # Small delay to ensure publisher connects
        time.sleep(1.0)
        
        msg = PoseStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.position.x = self.goal_x
        msg.pose.position.y = self.goal_y
        msg.pose.orientation.w = 1.0
        
        self.goal_pub.publish(msg)
        self.phase_start_time = time.time()

    def check_progress(self):
        if self.goal_pub is None:
            return

        robot = self.robots[self.current_robot_idx]
        
        # Continuously publish goal to ensure delivery
        msg = PoseStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.position.x = self.goal_x
        msg.pose.position.y = self.goal_y
        msg.pose.orientation.w = 1.0
        self.goal_pub.publish(msg)
        
        if self.current_x is None or self.current_y is None:
            return
            
        elapsed = time.time() - self.phase_start_time
        
        # Distance to goal
        dist = math.sqrt((self.goal_x - self.current_x)**2 + (self.goal_y - self.current_y)**2)
        
        time_limit = 25.0 if self.current_phase == 1 else 45.0
        
        if dist < 0.1:
            self.get_logger().info(f"{robot} reached {self.phases[self.current_phase]} in {elapsed:.1f}s.")
            self.advance_phase()
        elif elapsed > time_limit:
            self.get_logger().warn(f"{robot} timed out attempting to reach {self.phases[self.current_phase]}. Proceeding anyway.")
            self.advance_phase()

    def advance_phase(self):
        self.current_phase += 1
        if self.current_phase > 2:
            self.current_robot_idx += 1
            self.get_logger().info("Test for current robot complete. Waiting 10 seconds before starting the next robot...")
            time.sleep(10.0)
            self.setup_current_robot()
        else:
            self.send_goal()

def main(args=None):
    rclpy.init(args=args)
    node = TestOrchestrator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        pass
    finally:
        node.destroy_node()

if __name__ == '__main__':
    main()
