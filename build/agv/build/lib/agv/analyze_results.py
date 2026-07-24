#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def calculate_metrics(df):
    target = df['Target_X'].iloc[-1]
    actual = df['Actual_X'].values
    time = df['Timestamp'].values
    error = df['Error'].values
    
    metrics = {}
    
    # 1. Rise Time (time to go from 10% to 90% of final target)
    try:
        t_10 = time[np.where(actual >= 0.1 * target)[0][0]]
        t_90 = time[np.where(actual >= 0.9 * target)[0][0]]
        metrics['Rise Time (s)'] = round(t_90 - t_10, 3)
    except IndexError:
        metrics['Rise Time (s)'] = "N/A"
        
    # 2. Maximum Overshoot (%)
    max_val = np.max(actual)
    if max_val > target:
        overshoot = ((max_val - target) / target) * 100
    else:
        overshoot = 0.0
    metrics['Max Overshoot (%)'] = round(overshoot, 2)
    
    # 3. Settling Time (time to stay within 2% of target)
    tolerance = 0.02 * target
    settled_indices = np.where(np.abs(actual - target) > tolerance)[0]
    if len(settled_indices) > 0 and settled_indices[-1] < len(time) - 1:
        metrics['Settling Time (s)'] = round(time[settled_indices[-1] + 1], 3)
    else:
        metrics['Settling Time (s)'] = "Not Settled"
        
    # 4. Steady-state error (error at the very end of the run)
    metrics['Steady-State Error'] = round(abs(target - actual[-1]), 4)
    
    # 5. Max Absolute Error
    metrics['Max Abs Error'] = round(np.max(np.abs(error)), 4)
    
    # 6. Mean Absolute Error (MAE)
    metrics['MAE'] = round(np.mean(np.abs(error)), 4)
    
    # 7. RMSE
    metrics['RMSE'] = round(np.sqrt(np.mean(error**2)), 4)
    
    return metrics

def main():
    files = {
        'P Controller': 'p_controller.csv',
        'PI Controller': 'pi_controller.csv',
        'PID Controller': 'pid_controller.csv'
    }
    
    data = {}
    for name, file in files.items():
        if os.path.exists(file):
            data[name] = pd.read_csv(file)
        else:
            print(f"Error: {file} not found. Please run the tests first.")
            return
            
    # Calculate Metrics
    results = {}
    for name, df in data.items():
        results[name] = calculate_metrics(df)
        
    results_df = pd.DataFrame(results).T
    print("\n=== PID Performance Comparison ===")
    print(results_df.to_string())
    
    import datetime
    import shutil
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"test_results_{timestamp}"
    os.makedirs(folder_name, exist_ok=True)
    
    metrics_file = os.path.join(folder_name, "performance_metrics.txt")
    with open(metrics_file, "w") as f:
        f.write("=== PID Performance Comparison ===\n")
        f.write(results_df.to_string())
        
    # Plotting
    plt.style.use('seaborn-whitegrid')
    
    # 1. Target vs Actual Position
    plt.figure(figsize=(10, 6))
    for name, df in data.items():
        plt.plot(df['Timestamp'].values, df['Actual_X'].values, label=f'{name} Actual')
    
    # Plot Target line (assume all tests have same target)
    target_val = data['PID Controller']['Target_X'].iloc[0]
    plt.axhline(y=target_val, color='r', linestyle='--', label='Target Position')
    
    plt.title('Target Position vs Actual Position', fontsize=14)
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Distance / Position (m)', fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(folder_name, 'target_vs_actual.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Error vs Time
    plt.figure(figsize=(10, 6))
    for name, df in data.items():
        plt.plot(df['Timestamp'].values, df['Error'].values, label=name)
        
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    plt.title('Control Error vs Time', fontsize=14)
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Error (m)', fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(folder_name, 'error_vs_time.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. PWM Output (Velocity) vs Time
    plt.figure(figsize=(10, 6))
    for name, df in data.items():
        plt.plot(df['Timestamp'].values, df['PWM_Command'].values, label=name)
        
    plt.title('Controller Output (Velocity) vs Time', fontsize=14)
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Velocity Command (m/s)', fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(folder_name, 'output_vs_time.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Write README.md with details
    readme_path = os.path.join(folder_name, "README.md")
    with open(readme_path, "w") as f:
        f.write("# PID Test Results\n\n")
        f.write("## Overview\n")
        f.write("This folder contains the results of the AGV PID tuning experiment. The tests compare P, PI, and PID controllers.\n\n")
        f.write("## Files in this Folder\n")
        f.write("- **target_vs_actual.png**: Shows how closely each controller followed the goal distance (2.0m). The ideal line is the red dashed line.\n")
        f.write("- **error_vs_time.png**: Shows the difference between the target and actual position over time. An ideal controller brings this to exactly 0 quickly without oscillating.\n")
        f.write("- **output_vs_time.png**: Shows the velocity commands sent to the robot's motors (PWM/cmd_vel). Helps identify if the motors are being pushed too hard or oscillating.\n")
        f.write("- **performance_metrics.txt**: A text summary of control theory metrics like Rise Time (speed), Overshoot (past the goal), and Steady-State Error (how close it settles).\n")
        f.write("- **.csv files**: The raw data logs containing timestamps, actual positions, errors, and the Kp, Ki, Kd values used for each run.\n\n")
        f.write("## How to Understand the Results\n")
        f.write("1. **Look at `target_vs_actual.png`**: The best controller will quickly reach the red dotted line (Rise Time) and stay precisely on it without bouncing around (Overshoot & Settling Time).\n")
        f.write("2. **Look at `performance_metrics.txt`**: You want the lowest possible **Steady-State Error** and **Max Overshoot**, while having a fast **Rise Time**.\n")
        f.write("3. **Check your PID values**: Open the `.csv` files to see what Kp, Ki, and Kd values resulted in these graphs so you know what to tune next.\n")

    # Move CSV files into the folder
    for name, file in files.items():
        if os.path.exists(file):
            shutil.move(file, os.path.join(folder_name, file))
            
    print(f"\nAll results, graphs, and details have been saved to the folder: {folder_name}")

if __name__ == '__main__':
    main()
