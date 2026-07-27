#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
import random
import time
import threading

class RandomOrchestrator(Node):
    def __init__(self):
        super().__init__('random_orchestrator', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)
        ])
        
        # Publishers for all 3 robots
        self.pub1 = self.create_publisher(PoseStamped, '/robot1/goal_pose', 10)
        self.pub2 = self.create_publisher(PoseStamped, '/robot2/goal_pose', 10)
        self.pub3 = self.create_publisher(PoseStamped, '/robot3/goal_pose', 10)
        
        self.get_logger().info("Random Orchestrator Started! Sending goals every 15 seconds...")
        
        # Start a thread to continuously send random goals
        self.thread = threading.Thread(target=self.send_goals_loop)
        self.thread.start()

    def send_goals_loop(self):
        while rclpy.ok():
            # Generate random coordinates in a 10x10 area (-5 to 5)
            x1, y1 = random.uniform(-4, 5), random.uniform(-4, 4)
            x2, y2 = random.uniform(-4, 5), random.uniform(-4, 4)
            x3, y3 = random.uniform(-4, 5), random.uniform(-4, 4)
            
            self.publish_goal(self.pub1, x1, y1, "robot1")
            self.publish_goal(self.pub2, x2, y2, "robot2")
            self.publish_goal(self.pub3, x3, y3, "robot3")
            
            # Wait 15 seconds before sending new goals
            time.sleep(15)

    def publish_goal(self, pub, x, y, robot_name):
        goal_msg = PoseStamped()
        goal_msg.header.frame_id = "map"
        goal_msg.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.position.x = x
        goal_msg.pose.position.y = y
        goal_msg.pose.orientation.w = 1.0 # default facing forward
        
        pub.publish(goal_msg)
        self.get_logger().info(f"Commanded {robot_name} to Random Point: ({x:.2f}, {y:.2f})")

def main(args=None):
    rclpy.init(args=args)
    node = RandomOrchestrator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
