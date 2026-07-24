import pandas as pd
import matplotlib.pyplot as plt
import os

files = {
    'Robot 1 (EKF)': 'robot1_ekf_test.csv',
    'Robot 2 (AMCL)': 'robot2_lidar_test.csv'
}

plt.figure(figsize=(12, 6))

colors = {'Robot 1 (EKF)': 'b', 'Robot 2 (AMCL)': 'g'}

for label, filename in files.items():
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename)
            # Remove whitespace from column names if present
            df.columns = [c.strip() for c in df.columns]
            
            # The goals we gave were X=3.0, Y=1.0 or Y=-1.0
            # For simplicity, we can plot the Actual_X vs Timestamp as that's what manual plot did
            
            plt.plot(df['Timestamp'].values, df['Actual_X'].values, 
                     color=colors[label], label=f'{label} Actual X', linewidth=2)
                     
            plt.plot(df['Timestamp'].values, df['Target_X'].values, 
                     color=colors[label], linestyle='--', label=f'{label} Target X', alpha=0.5)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    else:
        print(f"File not found: {filename}")

plt.title('Multi-Robot Navigation Performance (X-Axis)')
plt.xlabel('Time (s)')
plt.ylabel('X Position (m)')
plt.legend()
plt.grid(True)
plt.savefig('multi_robot_comparison.png')
plt.close()

print("Comparison graph generated as multi_robot_comparison.png")
