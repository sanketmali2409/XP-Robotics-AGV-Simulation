# PID Test Results

## Overview
This folder contains the results of the AGV PID tuning experiment. The tests compare P, PI, and PID controllers.

## Files in this Folder
- **target_vs_actual.png**: Shows how closely each controller followed the goal distance (2.0m). The ideal line is the red dashed line.
- **error_vs_time.png**: Shows the difference between the target and actual position over time. An ideal controller brings this to exactly 0 quickly without oscillating.
- **output_vs_time.png**: Shows the velocity commands sent to the robot's motors (PWM/cmd_vel). Helps identify if the motors are being pushed too hard or oscillating.
- **performance_metrics.txt**: A text summary of control theory metrics like Rise Time (speed), Overshoot (past the goal), and Steady-State Error (how close it settles).
- **.csv files**: The raw data logs containing timestamps, actual positions, errors, and the Kp, Ki, Kd values used for each run.

## How to Understand the Results
1. **Look at `target_vs_actual.png`**: The best controller will quickly reach the red dotted line (Rise Time) and stay precisely on it without bouncing around (Overshoot & Settling Time).
2. **Look at `performance_metrics.txt`**: You want the lowest possible **Steady-State Error** and **Max Overshoot**, while having a fast **Rise Time**.
3. **Check your PID values**: Open the `.csv` files to see what Kp, Ki, and Kd values resulted in these graphs so you know what to tune next.
