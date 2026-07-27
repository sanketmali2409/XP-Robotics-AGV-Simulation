import pandas as pd
import matplotlib.pyplot as plt
import os
import shutil

csv1 = 'robot1_ekf_test.csv'
csv2 = 'robot2_lidar_test.csv'

if not os.path.exists(csv1) or not os.path.exists(csv2):
    print("Error: Could not find CSV files. Make sure you sent a goal to the drag race!")
    exit(1)

df1 = pd.read_csv(csv1)
df2 = pd.read_csv(csv2)

target = df1['Target_X'].iloc[0]

plt.figure(figsize=(12, 6))
plt.plot(df1['Timestamp'].values, df1['Target_X'].values, 'r--', label='Target Goal', linewidth=2)
plt.plot(df1['Timestamp'].values, df1['Actual_X'].values, 'b-', label=f'Robot 1 (EKF) - Error: {df1["Error"].iloc[-1]:.3f}m', linewidth=2)
plt.plot(df2['Timestamp'].values, df2['Actual_X'].values, 'g-', label=f'Robot 2 (LiDAR) - Error: {df2["Error"].iloc[-1]:.3f}m', linewidth=2)

plt.title('Drag Race Comparison: EKF vs LiDAR SLAM')
plt.xlabel('Time (s)')
plt.ylabel('Distance (m)')
plt.legend()
plt.grid(True)

folder_name = f"drag_race_results_{target:.2f}m"
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

graph_filename = os.path.join(folder_name, 'drag_race_graph.png')
plt.savefig(graph_filename)
plt.close()

shutil.move(csv1, os.path.join(folder_name, csv1))
shutil.move(csv2, os.path.join(folder_name, csv2))

print("=======================================")
print(f"DRAG RACE RESULTS SAVED!")
print(f"Target Distance: {target:.2f} m")
print(f"Robot 1 (EKF) Final Error:   {df1['Error'].iloc[-1]:.3f} m")
print(f"Robot 2 (LiDAR) Final Error: {df2['Error'].iloc[-1]:.3f} m")
print(f"Files saved to:  {folder_name}/")
print("=======================================")
