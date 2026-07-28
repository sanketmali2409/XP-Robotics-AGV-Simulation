#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
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
        self.declare_parameter('enable_obstacle_avoidance', False)
        self.declare_parameter('odom_topic', 'odometry/global_amcl')
        
        # Publishers and Subscribers
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        odom_topic = self.get_parameter('odom_topic').value
        self.odom_sub = self.create_subscription(Odometry, odom_topic, self.odom_callback, 10)
        self.goal_sub = self.create_subscription(PoseStamped, 'goal_pose', self.goal_callback, 10)
        
        if self.get_parameter('enable_obstacle_avoidance').value:
            self.scan_sub = self.create_subscription(LaserScan, 'scan', self.scan_callback, 10)
            self.get_logger().info("Obstacle Avoidance ENABLED")
        else:
            self.get_logger().info("Obstacle Avoidance DISABLED")
        
        # Timer for control loop
        self.timer = self.create_timer(0.1, self.control_loop) # 10 Hz
        
        # State variables
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_theta = 0.0
        self.obstacle_detected = False
        
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
        self.k_p_angular = 1.5  # Increased to prevent stalling
        self.distance_tolerance = 0.02
        
        self.get_logger().info(f"Started PID Controller Node")
        self.get_logger().info("Awaiting goal...")

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        orientation_q = msg.pose.pose.orientation
        self.current_theta = euler_from_quaternion(
            orientation_q.x, orientation_q.y, orientation_q.z, orientation_q.w)

    def scan_callback(self, msg):
        # LiDAR scans are typically 360 degrees. We check the frontal cone.
        # -30 to +30 degrees. Depending on the LiDAR, 0 is straight ahead.
        angle_min = msg.angle_min
        angle_increment = msg.angle_increment
        
        obstacle_in_front = False
        for i, range_val in enumerate(msg.ranges):
            # Ignore infinites or extremely close noise
            if range_val < msg.range_min or range_val > msg.range_max:
                continue
                
            angle = angle_min + (i * angle_increment)
            
            # Check wider frontal cone (+/- 45 degrees = 0.785 rad)
            if abs(angle) < 0.785:
                # 0.8 meters threshold from the center of the LiDAR (giving ~0.5m buffer from the front edge)
                if range_val < 0.8:
                    obstacle_in_front = True
                    break
                    
        self.obstacle_detected = obstacle_in_front

    def goal_callback(self, msg):
        self.goal_x = msg.pose.position.x
        self.goal_y = msg.pose.position.y
        
        # Reset PID state for new goal
        self.integral_error = 0.0
        self.prev_error = 0.0
        if getattr(self, 'first_goal_received', False) == False:
            self.start_time = time.time()
            self.test_name = self.get_parameter('test_name').value
            # Don't hold the file open, just mark as initialized
            self.first_goal_received = True
            
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
        
        # Only log and act if we haven't reached tight tolerance (1.5 cm)
        if distance >= 0.015:
            # PID logic for Linear velocity
            self.integral_error += error * dt
            derivative_error = (error - self.prev_error) / dt
            self.prev_error = error
            
            output = (kp * error) + (ki * self.integral_error) + (kd * derivative_error)
            
            if abs(angle_error) > 0.5:
                msg.linear.x = 0.0
            else:
                msg.linear.x = output
                # Ensure minimum power to overcome friction if we are outside tolerance
                min_linear_power = 0.05
                if abs(error) > 0.01:
                    if msg.linear.x > 0:
                        msg.linear.x = max(msg.linear.x, min_linear_power)
                    elif msg.linear.x < 0:
                        msg.linear.x = min(msg.linear.x, -min_linear_power)
            
            # Angular control with minimum steering power to overcome static friction
            angular_cmd = self.k_p_angular * angle_error
            
            # If we need to turn noticeably, ensure we apply enough power to physically turn
            # Only apply this boost if we are far enough from the goal to prevent spinning in circles at the end!
            if abs(angle_error) > 0.05 and distance > 0.2:
                min_turn_power = 0.3  # Lowered from 1.0 to prevent violent spinning
                if angular_cmd > 0:
                    angular_cmd = max(angular_cmd, min_turn_power)
                else:
                    angular_cmd = min(angular_cmd, -min_turn_power)
                    
            msg.angular.z = angular_cmd
            
            # Obstacle Avoidance Override
            if self.obstacle_detected:
                msg.linear.x = 0.0
                # We can either let it turn in place, or stop completely. We'll let it keep its heading (turn) but stop moving forward.
                self.get_logger().warn("OBSTACLE DETECTED! Braking...", throttle_duration_sec=2.0)
            
            # Anti-windup and clamping
            msg.linear.x = max(min(msg.linear.x, 1.0), -1.0)
            msg.angular.z = max(min(msg.angular.z, 1.0), -1.0)
            
            # Log Data
            timestamp = time.time() - self.start_time
            with open(f'{self.test_name}.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    f"{timestamp:.3f}", 
                    f"{self.goal_x:.3f}", 
                    f"{self.goal_y:.3f}",
                    f"{self.current_x:.3f}",
                    f"{self.current_y:.3f}",
                    f"{error:.3f}", 
                    f"{msg.linear.x:.3f}", 
                    f"{kp:.3f}", f"{ki:.3f}", f"{kd:.3f}"
                ])
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
