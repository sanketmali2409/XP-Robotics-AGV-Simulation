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


// PID Testing 
<!-- ros2 launch agv agv_bringup.launch.py

python3 save_manual_result.py -->

