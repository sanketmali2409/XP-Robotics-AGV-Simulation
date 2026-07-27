import rclpy
from nav_msgs.msg import Odometry
import time

def main():
    rclpy.init()
    node = rclpy.create_node('pose_checker')
    
    pose = None
    def odom_callback(msg):
        nonlocal pose
        pose = msg.pose.pose.position
    
    sub = node.create_subscription(Odometry, '/robot3/odom', odom_callback, 10)
    
    end_time = time.time() + 3
    while time.time() < end_time and pose is None:
        rclpy.spin_once(node, timeout_sec=0.1)
        
    if pose:
        print(f"Current Position - X: {pose.x:.3f}, Y: {pose.y:.3f}")
    else:
        print("Failed to get pose!")
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
