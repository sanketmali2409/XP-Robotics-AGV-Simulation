#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped

class TrajectoryVisualizer(Node):
    def __init__(self):
        super().__init__('trajectory_visualizer', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)
        ])
        
        self.declare_parameter('robot_name', 'robot1')
        self.robot_name = self.get_parameter('robot_name').value
        
        self.declare_parameter('odom_topic', 'odometry/global_amcl')
        self.odom_topic = self.get_parameter('odom_topic').value
        
        self.path_msg = Path()
        self.path_msg.header.frame_id = "map"
        
        # Subscribe to odometry
        # We use a broader QoS profile (10) to catch odom messages
        self.odom_sub = self.create_subscription(
            Odometry, 
            f'/{self.robot_name}/{self.odom_topic}', 
            self.odom_callback, 
            10
        )
        
        # Publisher for the continuous path trail
        self.path_pub = self.create_publisher(Path, f'/{self.robot_name}/actual_trajectory', 10)
        
        self.get_logger().info(f"Started trajectory visualizer for {self.robot_name}")

    def odom_callback(self, msg):
        pose = PoseStamped()
        pose.header = msg.header
        # Overwrite frame_id to map so it renders globally in RViz
        pose.header.frame_id = "map"
        pose.pose = msg.pose.pose
        # Slightly elevate the path so it doesn't clip into the ground/map image (z-fighting)
        pose.pose.position.z = 0.05
        
        self.path_msg.poses.append(pose)
        self.path_msg.header.stamp = self.get_clock().now().to_msg()
        
        self.path_pub.publish(self.path_msg)

def main(args=None):
    rclpy.init(args=args)
    node = TrajectoryVisualizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
