#!/bin/bash
source install/setup.bash

echo "Waiting for bt_navigator to become active..."
while true; do
    STATE=$(ros2 lifecycle get /robot3/bt_navigator 2>/dev/null)
    if [[ "$STATE" == *"active [3]"* ]]; then
        echo "bt_navigator is ACTIVE!"
        break
    fi
    sleep 2
done

echo "Starting Test Orchestrator..."
ros2 run agv test_orchestrator

echo "Checking CSV Results:"
cat robot3_lidar_test.csv
