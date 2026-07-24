import pandas as pd
import matplotlib.pyplot as plt
import os
import shutil

csv_file = 'manual_controller.csv'

if not os.path.exists(csv_file):
    print(f"Error: {csv_file} not found. Make sure you have sent a goal in RViz first!")
    exit(1)

# Read the CSV data
df = pd.read_csv(csv_file)

# Extract important metrics
target = df['Target_X'].iloc[0]
final_actual = df['Actual_X'].iloc[-1]
final_error = df['Error'].iloc[-1]

# Create the plot
plt.figure(figsize=(10, 5))
plt.plot(df['Timestamp'].values, df['Target_X'].values, 'r--', label='Target Goal', linewidth=2)
plt.plot(df['Timestamp'].values, df['Actual_X'].values, 'b-', label='Actual Robot Path', linewidth=2)
plt.title(f'Custom RViz Goal: Target vs Actual (Error: {final_error:.3f}m)')
plt.xlabel('Time (s)')
plt.ylabel('Distance (m)')
plt.legend()
plt.grid(True)

# Generate folder name
folder_name = f"custom_goal_results_{target:.2f}m"
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

# Save graph
graph_filename = os.path.join(folder_name, 'custom_goal_graph.png')
plt.savefig(graph_filename)
plt.close()

# Move CSV into the new folder
new_csv_path = os.path.join(folder_name, csv_file)
shutil.move(csv_file, new_csv_path)

print("=======================================")
print(f"SUCCESS! Graph and Data saved automatically.")
print(f"Target Distance: {target:.2f} m")
print(f"Final Position:  {final_actual:.2f} m")
print(f"Final Error:     {final_error:.3f} m")
print(f"Files saved to:  {folder_name}/")
print("=======================================")
