#!/bin/bash
killall -9 gzserver gzclient rviz2 python3 ros2
source install/setup.bash
ros2 launch agv multi_robot_navigation.launch.py > final_run.log 2>&1 &
echo "Waiting 30 seconds for simulation to stabilize..."
sleep 30
echo "Starting test_orchestrator..."
ros2 run agv test_orchestrator > final_orch.log 2>&1 &
sleep 40
cat final_orch.log
