#!/bin/bash
killall -9 gzserver gzclient rviz2 python3 ros2
source install/setup.bash
echo "Starting multi-robot navigation..."
ros2 launch agv multi_robot_navigation.launch.py > run_movement.log 2>&1 &
sleep 25
echo "Sending test goals via orchestrator..."
ros2 run agv test_orchestrator > orch_movement.log 2>&1 &
sleep 15
echo "Checking if controller_server is publishing cmd_vel..."
timeout 10 ros2 topic echo /robot3/cmd_vel | grep -m 3 -A 2 "linear"
