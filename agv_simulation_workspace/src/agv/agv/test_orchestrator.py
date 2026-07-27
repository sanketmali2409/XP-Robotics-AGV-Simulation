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
        self.robots = ['robot3']
        
        # New set of waypoints for Robot 3 (Avoiding the Blue Box at X=2, Y=2)
        self.waypoints = [
            (-3.5, 3.5),
            (3.5, 3.5),
            (3.5, -3.5),
            (-3.5, -3.5),
            (-3.5, 0.0),
            (0.0, 0.0)
        ]
        
        self.current_robot_idx = 0
        self.current_phase = 0
        self.retry_count = 0
        
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
        self.odom_sub = self.create_subscription(Odometry, f'/{robot}/odometry/global_amcl', self.odom_callback, 10)
        
        # Clear the CSV file for this robot so we only show live data (use absolute path)
        csv_name = f"/home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/agv_simulation_workspace/{robot}_lidar_test.csv"
        if robot == 'robot1':
            csv_name = "/home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/agv_simulation_workspace/robot1_ekf_test.csv"
        
        try:
            with open(csv_name, 'w') as f:
                f.write("Timestamp,Target_X,Target_Y,Actual_X,Actual_Y,Error,PWM_Command,Kp,Ki,Kd\n")
            self.get_logger().info(f"Cleared CSV file: {csv_name}")
        except Exception as e:
            self.get_logger().warn(f"Could not clear CSV {csv_name}: {e}")
        
        self.current_phase = 0
        self.achieved_goals = 0
        self.total_errors = []
        self.settle_start_time = None
        self.send_goal()

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

    def send_goal(self):
        robot = self.robots[self.current_robot_idx]
        if self.current_phase < len(self.waypoints):
            self.goal_x, self.goal_y = self.waypoints[self.current_phase]
            phase_name = f"Waypoint {self.current_phase + 1}"
        else:
            return
            
        self.get_logger().info(f"Commanding {robot} to {phase_name} at ({self.goal_x}, {self.goal_y})")
        
        # Small delay to ensure publisher connects
        time.sleep(1.0)
        
        msg = PoseStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.position.x = self.goal_x
        msg.pose.position.y = self.goal_y
        msg.pose.orientation.w = 1.0
        
        self.goal_pub.publish(msg)
        self.phase_start_time = self.get_clock().now().nanoseconds / 1e9
        self.settle_start_time = None

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
            
        current_time = self.get_clock().now().nanoseconds / 1e9
        elapsed = current_time - self.phase_start_time
        
        # Distance to goal
        dist = math.sqrt((self.goal_x - self.current_x)**2 + (self.goal_y - self.current_y)**2)
        
        time_limit = 20.0 # Strict 20s timeout per goal (now properly using sim time)
        phase_name = f"Waypoint {self.current_phase + 1}"
        
        # 1.5 cm = 0.015 meters
        if dist < 0.015:
            if self.settle_start_time is None:
                self.settle_start_time = current_time
            elif current_time - self.settle_start_time >= 2.0:
                self.achieved_goals += 1
                self.total_errors.append(dist)
                self.get_logger().info(f"SUCCESS: {robot} achieved and settled at {phase_name} in {elapsed:.1f}s. Final Error: {dist*100:.2f} cm")
                self.advance_phase()
        else:
            self.settle_start_time = None
            if elapsed > time_limit:
                self.total_errors.append(dist)
                self.get_logger().warn(f"TIMEOUT: {robot} NOT achieved {phase_name} after {elapsed:.1f}s. Final Error: {dist*100:.2f} cm")
                self.advance_phase()

    def advance_phase(self):
        self.current_phase += 1
        if self.current_phase >= len(self.waypoints):
            robot = self.robots[self.current_robot_idx]
            avg_err = sum(self.total_errors) / len(self.total_errors) if self.total_errors else 0.0
            self.get_logger().info(f"--- TEST SUMMARY FOR {robot} ---")
            self.get_logger().info(f"Achieved Goals (< 1.5 cm): {self.achieved_goals} / {len(self.waypoints)}")
            self.get_logger().info(f"Average Final Error Across All Goals: {avg_err*100:.2f} cm")
            
            self.current_robot_idx += 1
            if self.current_robot_idx >= len(self.robots):
                self.get_logger().info("All tests completed successfully!")
                rclpy.shutdown()
                return
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
