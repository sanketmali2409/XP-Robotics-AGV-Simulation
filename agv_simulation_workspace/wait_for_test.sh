#!/bin/bash
killall -9 gzserver gzclient rviz2 python3 ros2
source install/setup.bash

echo "Starting everything..."
ros2 launch agv multi_robot_navigation.launch.py > final_combined.log 2>&1 &

echo "Waiting 30 seconds for Gazebo and Nav2 to fully initialize..."
sleep 30

echo "Starting Test Orchestrator..."
# Run until finished!
ros2 run agv test_orchestrator

echo "Checking CSV Results:"
cat robot3_lidar_test.csv
