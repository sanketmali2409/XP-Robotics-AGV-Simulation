# AGV Gazebo Simulation

This directory contains the URDF, SDF, and Gazebo world files for the AGV simulation model.

## Overview of Changes

The original CAD model export had a few issues that were corrected in this workspace:
- **Orientation Fix**: The robot initially spawned standing upright due to a Y-up axis export. A `base_link` was added to `AGV.urdf` to mathematically rotate the chassis 90 degrees so it lays flat.
- **Center Offset Fix**: The mathematical origin of the CAD model was far from the physical center. A precise translation offset was applied (`X=-0.325`, `Y=0.26`) so the robot spawns perfectly centered at `0,0,0` in the Gazebo world.
- **Gazebo World**: An `AGV.world` file was generated to encapsulate the model, adding necessary lighting and a ground plane for a complete simulation environment.

## How to Run

To open the simulation in Gazebo, open your terminal, navigate to this directory, and run the following command:

```bash
DISPLAY=:1 gazebo AGV.world
```

*(Note: The `DISPLAY=:1` prefix is required to ensure the graphical window connects to the correct display server).*





// Launching gazebo and rviz 

<!-- cd /home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/agv_simulation_workspace
source /opt/ros/humble/setup.bash
source install/setup.bash
export ROS_LOG_DIR=/tmp/ros_log
ros2 launch agv multi_robot_navigation.launch.py -->


//  Dashboard 

<!-- cd /home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/telemetry_and_graphs/web_dashboard
python3 app.py -->

// Robot 2 testing 

 <!-- cd /home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/agv_simulation_workspace
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 run agv test_orchestrator --ros-args -p robot_name:=robot2 -->

// robot 1 tesing 

<!-- cd /home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/agv_simulation_workspace
source /opt/ros/humble/setup.bash
source install/setup.bash
# Robot 1
ros2 run agv random_orchestrator --ros-args -p robot_name:=robot1 -->

// Robot 3 tesing 
<!-- cd /home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/agv_simulation_workspace
source /opt/ros/humble/setup.bash
source install/setup.bash
# Robot 3
ros2 run agv test_orchestrator --ros-args -p robot_name:=robot3 -->




# Interactive Dashboard Grid Implementation Plan

## Goal Description
The objective is to upgrade the web dashboard (`app.py` and `index.html`) with an interactive 5x5 grid of 25 nodes. When you select a robot and click a node in the UI, the dashboard will automatically calculate the robot's current location, plan a strict node-to-node path, and send the robot to the clicked destination.

## Proposed Changes

### 1. Backend (`app.py`)
- Add a new POST endpoint `/api/navigate_to_node`.
- This endpoint will accept JSON containing `robot_name` and `target_node` (e.g., "N24").
- It will use `subprocess.Popen` to asynchronously spawn a new ROS 2 execution script without blocking the web server.

### 2. ROS 2 Bridge (`go_to_node.py`)
- **[NEW] `src/grid_navigation/grid_navigation/go_to_node.py`**
  - A new script that takes `robot_name` and `dest_node` as parameters.
  - It will temporarily subscribe to the robot's odometry to find its current `(x, y)` position.
  - It will find the **closest** node to the robot's current position to use as the `start_node`.
  - It will then use the `GridPlanner` and `Nav2Client` we built earlier to execute the straight-line node-to-node path.
- **[MODIFY] `src/grid_navigation/setup.py`**
  - Add `go_to_node` to the console scripts entry points.

### 3. Frontend UI (`index.html`)
- **[MODIFY] `templates/index.html`**
  - Add custom CSS for a `grid-template-columns: repeat(5, 1fr)` layout.
  - Inject 25 buttons labeled N1 through N25 into the sidebar under the "TEST CONFIGURATION" section.
  - Add a JavaScript function that captures the button click, reads the currently selected robot from the dropdown, and sends the POST request to `/api/navigate_to_node`.

## User Review Required

> [!IMPORTANT]  
> The dashboard will send commands using the `grid_navigation` package we just created. This means it relies on Nav2. If you try to send a command to **Robot 1**, it will fail because Robot 1 is configured to use the basic PID controller, not Nav2. Is this acceptable, or should I attempt to make Robot 1 work with this as well? (Usually, it's best to stick to Robot 2 and 3 for this).

> [!NOTE]  
> The UI grid will be drawn exactly like the logical grid:
> N1 N2 N3 N4 N5
> N6 N7 ...
> N21 ... N25

## Verification Plan
1. Write the code and rebuild the `grid_navigation` package.
2. Restart the Flask app.
3. Open the browser and click a node on the dashboard.
4. Verify via terminal logs or RViz that the robot correctly calculates its start node and begins navigating the grid.
