#!/bin/bash
killall -9 gzserver gzclient rviz2 python3 ros2
source install/setup.bash
echo "Starting Gazebo first..."
ros2 launch agv multi_robot_bringup.launch.py > gazebo.log 2>&1 &
sleep 20
echo "Starting Nav2..."
ros2 launch agv multi_robot_navigation.launch.py > nav.log 2>&1 &
sleep 20
echo "Sending goals..."
ros2 run agv test_orchestrator > orch.log 2>&1 &
sleep 30
cat orch.log
