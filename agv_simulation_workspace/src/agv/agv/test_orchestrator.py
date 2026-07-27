#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from nav_msgs.msg import Odometry
import time

class TestOrchestrator(Node):
    def __init__(self):
        super().__init__('test_orchestrator', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)
        ])
        
        self.robots = ['robot3']
        
        self.waypoints = [
            (-3.5, 3.5),
            (3.5, 3.5),
            (3.5, -3.5),
            (-3.5, -3.5),
            (0.0, 0.0),
            (-2.0, 2.0)
        ]
        
        self.current_robot_idx = 0
        self.current_phase = 0
        
        self.action_client = None
        self.odom_sub = None
        self.timer = None
        self.csv_f = None
        
        self.actual_x = 0.0
        self.actual_y = 0.0
        self.goal_x = 0.0
        self.goal_y = 0.0
        self.goal_active = False
        
        self.start_time = self.get_clock().now()
        
        self.setup_current_robot()

    def odom_callback(self, msg):
        self.actual_x = msg.pose.pose.position.x
        self.actual_y = msg.pose.pose.position.y

    def log_telemetry(self):
        if self.goal_active and self.csv_f:
            t = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
            self.csv_f.write(f"{t:.2f},{self.goal_x:.2f},{self.goal_y:.2f},{self.actual_x:.2f},{self.actual_y:.2f}\n")
            self.csv_f.flush()

    def setup_current_robot(self):
        if self.current_robot_idx >= len(self.robots):
            self.get_logger().info("All tests completed successfully!")
            rclpy.shutdown()
            return
            
        robot = self.robots[self.current_robot_idx]
        self.get_logger().info(f"--- Starting Nav2 test sequence for {robot} ---")
        
        if self.action_client:
            self.action_client.destroy()
        if self.odom_sub:
            self.odom_sub.destroy()
        if self.csv_f:
            self.csv_f.close()
        if self.timer:
            self.timer.destroy()
            
        self.action_client = ActionClient(self, NavigateToPose, f'/{robot}/navigate_to_pose')
        self.odom_sub = self.create_subscription(Odometry, f'/{robot}/odometry/global_amcl', self.odom_callback, 10)
        
        csv_name = f"/home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/agv_simulation_workspace/{robot}_lidar_test.csv"
        try:
            self.csv_f = open(csv_name, 'w')
            self.csv_f.write("Timestamp,Target_X,Target_Y,Actual_X,Actual_Y\n")
            self.get_logger().info(f"Created CSV file: {csv_name}")
        except Exception as e:
            self.get_logger().warn(f"Could not clear CSV {csv_name}: {e}")
        
        self.timer = self.create_timer(0.1, self.log_telemetry)
        
        self.current_phase = 0
        self.achieved_goals = 0
        self.send_goal()

    def send_goal(self):
        robot = self.robots[self.current_robot_idx]
        if self.current_phase < len(self.waypoints):
            self.goal_x, self.goal_y = self.waypoints[self.current_phase]
            phase_name = f"Waypoint {self.current_phase + 1}"
        else:
            return
            
        self.get_logger().info(f"Waiting for Nav2 action server for {robot}...")
        self.action_client.wait_for_server()
        
        self.get_logger().info(f"Commanding {robot} via Nav2 to {phase_name} at ({self.goal_x}, {self.goal_y})")
        
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = self.goal_x
        goal_msg.pose.pose.position.y = self.goal_y
        goal_msg.pose.pose.orientation.w = 1.0
        
        self.send_goal_future = self.action_client.send_goal_async(goal_msg)
        self.send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Nav2 rejected the goal!')
            self.goal_active = False
            self.advance_phase()
            return

        self.get_logger().info('Nav2 accepted the goal. Path planning in progress... (30s timeout started)')
        self.goal_active = True
        
        # Start a 30-second maximum travel timeout for this goal
        self.timeout_timer = self.create_timer(30.0, lambda: self.on_goal_timeout(goal_handle))
        
        self.get_result_future = goal_handle.get_result_async()
        self.get_result_future.add_done_callback(self.get_result_callback)

    def on_goal_timeout(self, goal_handle):
        if self.timeout_timer:
            self.timeout_timer.destroy()
            self.timeout_timer = None
            
        self.get_logger().warn(f'TIMEOUT: Failed to reach Waypoint {self.current_phase + 1} within 30 seconds. Canceling goal and advancing.')
        # Try to cancel the goal on the action server
        self.action_client._cancel_goal_async(goal_handle)
        
        self.goal_active = False
        self.advance_phase()

    def get_result_callback(self, future):
        # Cancel the timeout timer if the goal completes before 30 seconds
        if hasattr(self, 'timeout_timer') and self.timeout_timer:
            self.timeout_timer.destroy()
            self.timeout_timer = None
            
        result = future.result().result
        status = future.result().status
        
        # If the goal was already marked inactive (e.g., by a timeout), do not advance again
        if not self.goal_active:
            return
            
        self.goal_active = False
        
        # 4 is SUCCEEDED in actionlib status
        if status == 4:
            self.get_logger().info(f'SUCCESS: Reached Waypoint {self.current_phase + 1} under 30s! Immediately advancing to next goal.')
            self.achieved_goals += 1
        else:
            self.get_logger().warn(f'FAILED: Nav2 returned status code {status}')
            
        self.advance_phase()
        
    def advance_phase(self):
        self.current_phase += 1
        if self.current_phase >= len(self.waypoints):
            robot = self.robots[self.current_robot_idx]
            self.get_logger().info(f"--- NAV2 TEST SUMMARY FOR {robot} ---")
            self.get_logger().info(f"Achieved Goals: {self.achieved_goals} / {len(self.waypoints)}")
            
            self.current_robot_idx += 1
            if self.current_robot_idx >= len(self.robots):
                self.get_logger().info("All tests completed successfully!")
                rclpy.shutdown()
                return
            time.sleep(2.0)
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
