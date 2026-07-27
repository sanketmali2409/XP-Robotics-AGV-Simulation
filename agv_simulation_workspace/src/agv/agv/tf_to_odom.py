#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

class TfToOdom(Node):
    def __init__(self):
        super().__init__('tf_to_odom')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('odom_frame', 'map')
        
        self.base_frame = self.get_parameter('base_frame').value
        self.odom_frame = self.get_parameter('odom_frame').value
        
        self.odom_pub = self.create_publisher(Odometry, 'odometry/global_amcl', 10)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        self.timer = self.create_timer(0.05, self.timer_callback) # 20 Hz
        self.get_logger().info(f"Publishing TF ({self.odom_frame} -> {self.base_frame}) to odometry/filtered")

    def timer_callback(self):
        try:
            t = self.tf_buffer.lookup_transform(
                self.odom_frame,
                self.base_frame,
                rclpy.time.Time())
        except TransformException as ex:
            return

        msg = Odometry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.odom_frame
        msg.child_frame_id = self.base_frame
        
        msg.pose.pose.position.x = t.transform.translation.x
        msg.pose.pose.position.y = t.transform.translation.y
        msg.pose.pose.position.z = t.transform.translation.z
        msg.pose.pose.orientation = t.transform.rotation
        
        self.odom_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = TfToOdom()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
