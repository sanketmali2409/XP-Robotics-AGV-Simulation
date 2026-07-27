#!/bin/bash
killall -9 gzserver gzclient rviz2 python3 ros2
source install/setup.bash
ros2 launch agv multi_robot_navigation.launch.py > run13.log 2>&1 &
sleep 25
ros2 run agv test_orchestrator > orch13.log 2>&1 &
sleep 50
cat orch13.log
