import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('manual_controller.csv')

plt.figure(figsize=(10, 5))
plt.plot(df['Timestamp'].values, df['Target_X'].values, 'r--', label='Target Goal', linewidth=2)
plt.plot(df['Timestamp'].values, df['Actual_X'].values, 'b-', label='Actual Robot Path', linewidth=2)
plt.title('Your Custom RViz Goal: Target vs Actual')
plt.xlabel('Time (s)')
plt.ylabel('Distance (m)')
plt.legend()
plt.grid(True)
plt.savefig('custom_goal_graph.png')
plt.close()

print(f"Graph generated. Target was {df['Target_X'].iloc[0]:.2f}, Final Actual was {df['Actual_X'].iloc[-1]:.2f}, Error was {df['Error'].iloc[-1]:.3f}")
