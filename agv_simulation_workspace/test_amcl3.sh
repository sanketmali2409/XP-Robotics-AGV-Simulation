#!/bin/bash
killall -9 gzserver gzclient rviz2 python3 ros2
source install/setup.bash
echo "Starting amcl3..."
ros2 run nav2_amcl amcl --ros-args -p use_sim_time:=true -p odom_frame_id:="robot3/odom" -p base_frame_id:="robot3/base_link" -r __node:=amcl3 &
sleep 5
echo "Triggering configure..."
ros2 lifecycle set /amcl3 configure
sleep 5
echo "Logs:"
