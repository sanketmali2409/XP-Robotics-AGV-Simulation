import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os
import signal
import sys
from datetime import datetime

# Global figure and axes
fig, ax = plt.subplots(figsize=(12, 6))

files = {
    'Robot 1 (EKF)': 'robot1_ekf_test.csv',
    'Robot 2 (AMCL/LiDAR)': 'robot2_lidar_test.csv'
}
colors = {'Robot 1 (EKF)': 'r', 'Robot 2 (AMCL/LiDAR)': 'b'}

def save_and_exit(signum=None, frame=None):
    print("\nSaving final graph and exiting...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"realtime_comparison_{timestamp}.png"
    plt.savefig(filename, dpi=300)
    print(f"Final graph saved as {filename}")
    sys.exit(0)

# Register signal handler for graceful exit on Ctrl+C
signal.signal(signal.SIGINT, save_and_exit)

def animate(i):
    ax.clear()
    
    plotted = False
    for label, filename in files.items():
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            try:
                # Use on_bad_lines='skip' to avoid crashes during partial file writes
                df = pd.read_csv(filename, on_bad_lines='skip')
                
                # Check if required columns exist before plotting
                if 'Timestamp' in df.columns and 'Actual_X' in df.columns and 'Target_X' in df.columns:
                    ax.plot(df['Timestamp'].values, df['Target_X'].values, 
                            color=colors[label], linestyle='--', label=f'{label} Target X', linewidth=1)
                    ax.plot(df['Timestamp'].values, df['Actual_X'].values, 
                            color=colors[label], linestyle='-', label=f'{label} Actual X', linewidth=2)
                    plotted = True
            except Exception as e:
                pass # Fail silently for partial writes/parse errors
                
    ax.set_title('Real-Time Performance: EKF vs LiDAR Localization')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Distance (X-Axis) (m)')
    
    if plotted:
        ax.legend(loc='upper right')
    ax.grid(True)

print("Starting real-time plotter...")
print("Close the graph window or press Ctrl+C in the terminal to save the final graph and exit.")

# Run animation, updating every 500 milliseconds
ani = animation.FuncAnimation(fig, animate, interval=500, cache_frame_data=False)

# Register close event to save when the GUI window is closed by the user
fig.canvas.mpl_connect('close_event', lambda evt: save_and_exit())

plt.show()
