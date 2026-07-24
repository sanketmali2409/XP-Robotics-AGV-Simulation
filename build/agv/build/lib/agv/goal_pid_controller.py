#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
import math
import csv
import time

def euler_from_quaternion(x, y, z, w):
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    return math.atan2(t3, t4)

class GoalPIDController(Node):
    def __init__(self):
        super().__init__('goal_pid_controller')
        
        # Declare parameters
        self.declare_parameter('kp', 0.5)
        self.declare_parameter('ki', 0.0)
        self.declare_parameter('kd', 0.0)
        self.declare_parameter('test_name', 'manual_controller')
        
        # Publishers and Subscribers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odometry/filtered', self.odom_callback, 10)
        self.goal_sub = self.create_subscription(PoseStamped, '/goal_pose', self.goal_callback, 10)
        
        # Timer for control loop
        self.timer = self.create_timer(0.1, self.control_loop) # 10 Hz
        
        # State variables
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_theta = 0.0
        
        self.goal_x = None
        self.goal_y = None
        
        # PID internal state
        self.integral_error = 0.0
        self.prev_error = 0.0
        self.last_time = self.get_clock().now()
        
        # CSV Logging state
        self.start_time = None
        self.csv_file = None
        self.csv_writer = None
        
        # Constants
        self.k_p_angular = 0.3  # Reduced from 1.0 to prevent aggressive spin loops with casters
        self.distance_tolerance = 0.02
        
        self.get_logger().info(f"Started PID Controller Node")
        self.get_logger().info("Awaiting goal...")

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        orientation_q = msg.pose.pose.orientation
        self.current_theta = euler_from_quaternion(
            orientation_q.x, orientation_q.y, orientation_q.z, orientation_q.w)

    def goal_callback(self, msg):
        self.goal_x = msg.pose.position.x
        self.goal_y = msg.pose.position.y
        
        # Reset PID state for new goal
        self.integral_error = 0.0
        self.prev_error = 0.0
        self.start_time = time.time()
        self.last_time = self.get_clock().now()
        
        # Close old CSV if open
        if self.csv_file and not self.csv_file.closed:
            self.csv_file.close()
            
        # Open new CSV based on current parameter
        self.test_name = self.get_parameter('test_name').value
        self.csv_file = open(f'{self.test_name}.csv', 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['Timestamp', 'Target_X', 'Actual_X', 'Error', 'PWM_Command', 'Kp', 'Ki', 'Kd'])
        
        self.get_logger().info(f"New goal received: x={self.goal_x:.2f}, y={self.goal_y:.2f} (Test: {self.test_name})")

    def control_loop(self):
        if self.goal_x is None or self.goal_y is None:
            return

        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        if dt <= 0.0:
            return
            
        self.last_time = current_time

        # Get PID params dynamically
        kp = self.get_parameter('kp').value
        ki = self.get_parameter('ki').value
        kd = self.get_parameter('kd').value

        # Calculate error
        diff_x = self.goal_x - self.current_x
        diff_y = self.goal_y - self.current_y
        distance = math.sqrt(diff_x**2 + diff_y**2)
        angle_to_goal = math.atan2(diff_y, diff_x)
        
        # Angular error
        angle_error = angle_to_goal - self.current_theta
        while angle_error > math.pi: angle_error -= 2 * math.pi
        while angle_error < -math.pi: angle_error += 2 * math.pi

        msg = Twist()
        
        # Project the global error vector onto the robot's local forward axis.
        # This allows 1D overshoots to result in reversing, and 2D navigation to work correctly.
        error = diff_x * math.cos(self.current_theta) + diff_y * math.sin(self.current_theta)
        
        # Only log and act if we haven't reached tight tolerance
        if abs(error) >= self.distance_tolerance or abs(angle_error) > 0.1:
            # PID logic for Linear velocity
            self.integral_error += error * dt
            derivative_error = (error - self.prev_error) / dt
            self.prev_error = error
            
            output = (kp * error) + (ki * self.integral_error) + (kd * derivative_error)
            
            msg.linear.x = output
            
            # Angular control with minimum steering power to overcome static friction
            angular_cmd = self.k_p_angular * angle_error
            
            # If we need to turn noticeably, ensure we apply enough power to physically turn
            if abs(angle_error) > 0.05:
                min_turn_power = 0.5  # Minimum rad/s required to overcome floor friction
                if angular_cmd > 0:
                    angular_cmd = max(angular_cmd, min_turn_power)
                else:
                    angular_cmd = min(angular_cmd, -min_turn_power)
                    
            msg.angular.z = angular_cmd
            
            # Anti-windup and clamping
            msg.linear.x = max(min(msg.linear.x, 1.0), -1.0)
            msg.angular.z = max(min(msg.angular.z, 1.0), -1.0)
            
            # Log Data
            timestamp = time.time() - self.start_time
            self.csv_writer.writerow([
                f"{timestamp:.3f}", 
                f"{self.goal_x:.3f}", 
                f"{self.current_x:.3f}", 
                f"{error:.3f}", 
                f"{msg.linear.x:.3f}", 
                f"{kp:.3f}", f"{ki:.3f}", f"{kd:.3f}"
            ])
            self.csv_file.flush()
        else:
            # Goal reached
            msg.linear.x = 0.0
            msg.angular.z = 0.0
            self.get_logger().info(f"Test {self.test_name} complete. Reached goal.", once=True)
            self.goal_x = None
            self.goal_y = None
            
        self.cmd_vel_pub.publish(msg)

    def destroy_node(self):
        if self.csv_file and not self.csv_file.closed:
            self.csv_file.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = GoalPIDController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
