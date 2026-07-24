#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rcl_interfaces.srv import SetParameters
from std_srvs.srv import Empty
from geometry_msgs.msg import PoseStamped
import time

class TestRunner(Node):
    def __init__(self):
        super().__init__('test_runner')
        
        self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        
        # Service clients
        self.param_client = self.create_client(SetParameters, '/goal_pid_controller/set_parameters')
        self.reset_client = self.create_client(Empty, '/reset_simulation')
        
        while not self.param_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /goal_pid_controller parameter service...')
            
        while not self.reset_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for Gazebo /reset_simulation service...')

    def run_experiment(self, test_name, kp, ki, kd):
        self.get_logger().info(f"--- Starting Experiment: {test_name} ---")
        
        # 1. Reset Simulation
        self.get_logger().info("Resetting Gazebo World...")
        req_reset = Empty.Request()
        future_reset = self.reset_client.call_async(req_reset)
        rclpy.spin_until_future_complete(self, future_reset)
        time.sleep(1.0) # wait for physics to settle
        
        # 2. Set Parameters
        self.get_logger().info(f"Setting Parameters: Kp={kp}, Ki={ki}, Kd={kd}")
        req_param = SetParameters.Request()
        req_param.parameters = [
            Parameter('test_name', Parameter.Type.STRING, test_name).to_parameter_msg(),
            Parameter('kp', Parameter.Type.DOUBLE, kp).to_parameter_msg(),
            Parameter('ki', Parameter.Type.DOUBLE, ki).to_parameter_msg(),
            Parameter('kd', Parameter.Type.DOUBLE, kd).to_parameter_msg()
        ]
        future_param = self.param_client.call_async(req_param)
        rclpy.spin_until_future_complete(self, future_param)
        time.sleep(0.5)
        
        # 3. Publish Goal (X=2.0)
        self.get_logger().info("Publishing Goal: X=2.0")
        goal_msg = PoseStamped()
        goal_msg.header.frame_id = 'odom'
        goal_msg.pose.position.x = 2.0
        goal_msg.pose.position.y = 0.0
        goal_msg.pose.orientation.w = 1.0 # facing forward
        
        self.goal_pub.publish(goal_msg)
        
        # 4. Wait for completion
        self.get_logger().info("Waiting 10 seconds for test completion...")
        time.sleep(10.0)
        self.get_logger().info(f"Experiment {test_name} finished.\n")

def main(args=None):
    rclpy.init(args=args)
    runner = TestRunner()
    
    # Define Tests
    # Note: These values are standard baselines to show the difference.
    # P-Only: Will have steady state error or sluggish arrival
    # PI: Fixes steady state error but might overshoot
    # PID: Faster response, damped overshoot
    tests = [
        {'name': 'p_controller', 'kp': 0.5, 'ki': 0.0, 'kd': 0.0},
        {'name': 'pi_controller', 'kp': 0.5, 'ki': 0.05, 'kd': 0.0},
        {'name': 'pid_controller', 'kp': 0.5, 'ki': 0.02, 'kd': 0.5}
    ]
    
    for t in tests:
        runner.run_experiment(t['name'], t['kp'], t['ki'], t['kd'])
        
    runner.get_logger().info("All tests completed successfully. CSV files have been generated.")
    
    runner.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
