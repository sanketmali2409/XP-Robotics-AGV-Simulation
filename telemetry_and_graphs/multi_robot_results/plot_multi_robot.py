import pandas as pd
import matplotlib.pyplot as plt

try:
    df1 = pd.read_csv('../robot1_ekf_test.csv', on_bad_lines='skip')
except FileNotFoundError:
    df1 = pd.read_csv('robot1_ekf_test.csv', on_bad_lines='skip')

try:
    df2 = pd.read_csv('../robot2_lidar_test.csv', on_bad_lines='skip')
except FileNotFoundError:
    df2 = pd.read_csv('robot2_lidar_test.csv', on_bad_lines='skip')

plt.figure(figsize=(12, 6))

# Plot EKF Robot
plt.plot(df1['Timestamp'].values, df1['Target_X'].values, 'r--', label='Robot 1 Target', linewidth=1)
plt.plot(df1['Timestamp'].values, df1['Actual_X'].values, 'r-', label='Robot 1 Actual (EKF)', linewidth=2)

# Plot LiDAR Robot
plt.plot(df2['Timestamp'].values, df2['Target_X'].values, 'b--', label='Robot 2 Target', linewidth=1)
plt.plot(df2['Timestamp'].values, df2['Actual_X'].values, 'b-', label='Robot 2 Actual (AMCL/LiDAR)', linewidth=2)

plt.title('Performance Comparison: EKF vs LiDAR Localization')
plt.xlabel('Time (s)')
plt.ylabel('Distance (X-Axis) (m)')
plt.legend()
plt.grid(True)
plt.savefig('performance_comparison.png', dpi=300)
plt.close()

print("Generated performance_comparison.png")
