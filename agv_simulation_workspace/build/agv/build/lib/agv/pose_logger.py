#!/usr/bin/env python3
"""
Persistent pose logger — appends the robot's live odometry (and the current
Nav2 plan endpoint as the target) to a CSV at 10 Hz. This exists because
trajectory_visualizer only publishes RViz paths and test_orchestrator only
runs during scripted test suites, so grid_navigation runs otherwise leave
the dashboard's CSV empty.
"""
import os
import time
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry, Path


class PoseLogger(Node):
    def __init__(self):
        super().__init__('pose_logger')
        self.declare_parameter('robot_name', 'robot2')
        self.declare_parameter('csv_path', '')
        self.declare_parameter('odom_topic', 'odometry/global_amcl')

        self.robot_name = self.get_parameter('robot_name').value
        self.csv_path = self.get_parameter('csv_path').value
        odom_topic = self.get_parameter('odom_topic').value

        if not self.csv_path:
            self.csv_path = f'/tmp/{self.robot_name}_live.csv'

        self.actual_x = 0.0
        self.actual_y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self.have_pose = False

        self.create_subscription(
            Odometry, f'/{self.robot_name}/{odom_topic}', self._on_odom, 10)
        # Nav2 publishes the current planned path here; the last pose is the goal.
        self.create_subscription(
            Path, f'/{self.robot_name}/plan', self._on_plan, 10)

        # Fresh file each launch so old test-runner data doesn't pollute.
        with open(self.csv_path, 'w') as f:
            f.write('Timestamp,Target_X,Target_Y,Actual_X,Actual_Y\n')
        self.csv_f = open(self.csv_path, 'a', buffering=1)

        self.start_time = time.time()
        self.create_timer(0.1, self._write_row)
        self.get_logger().info(
            f'pose_logger for {self.robot_name} → {self.csv_path} '
            f'(odom: /{self.robot_name}/{odom_topic})'
        )

    def _on_odom(self, msg):
        self.actual_x = msg.pose.pose.position.x
        self.actual_y = msg.pose.pose.position.y
        self.have_pose = True

    def _on_plan(self, msg):
        if msg.poses:
            p = msg.poses[-1].pose.position
            self.target_x = p.x
            self.target_y = p.y

    def _write_row(self):
        if not self.have_pose:
            return
        t = time.time() - self.start_time
        self.csv_f.write(
            f'{t:.2f},{self.target_x:.2f},{self.target_y:.2f},'
            f'{self.actual_x:.2f},{self.actual_y:.2f}\n'
        )


def main():
    rclpy.init()
    node = PoseLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.csv_f.close()
        except Exception:
            pass
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
