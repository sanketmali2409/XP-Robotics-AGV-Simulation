#!/usr/bin/env python3
"""
Filters LaserScan returns that fall inside the robot's own silhouette
footprint, so the silhouette (added to the URDF for inter-robot visibility)
is invisible to the robot's own costmap and AMCL.

The silhouette is a box in base_link at X:[-0.25,0.25] Y:[-0.20,0.20]
Z:[0.20,0.55]. LiDAR is at base_link (0.325, 0, 0.35), so in laser_frame the
silhouette occupies X:[-0.575,-0.075] Y:[-0.20,0.20]. Defaults include a
small safety margin.
"""
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class ScanSelfFilter(Node):
    def __init__(self):
        super().__init__('scan_self_filter')
        self.declare_parameter('input_topic', 'scan')
        self.declare_parameter('output_topic', 'scan_filtered')
        self.declare_parameter('x_min', -0.60)
        self.declare_parameter('x_max', -0.05)
        self.declare_parameter('y_min', -0.25)
        self.declare_parameter('y_max',  0.25)

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value
        self.x_min = self.get_parameter('x_min').value
        self.x_max = self.get_parameter('x_max').value
        self.y_min = self.get_parameter('y_min').value
        self.y_max = self.get_parameter('y_max').value

        self.pub = self.create_publisher(LaserScan, output_topic, 10)
        self.sub = self.create_subscription(LaserScan, input_topic, self._on_scan, 10)
        self.get_logger().info(
            f"scan_self_filter: {input_topic} -> {output_topic} "
            f"| footprint x=[{self.x_min:.2f},{self.x_max:.2f}] "
            f"y=[{self.y_min:.2f},{self.y_max:.2f}]"
        )

    def _on_scan(self, msg: LaserScan):
        ranges = list(msg.ranges)
        for i, r in enumerate(ranges):
            if math.isinf(r) or math.isnan(r) or r < msg.range_min or r > msg.range_max:
                continue
            angle = msg.angle_min + i * msg.angle_increment
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            if self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max:
                # Below range_min => treated as invalid by Nav2 and AMCL.
                ranges[i] = 0.0
        msg.ranges = ranges
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = ScanSelfFilter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
