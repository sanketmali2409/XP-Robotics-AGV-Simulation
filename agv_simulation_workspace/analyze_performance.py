import pandas as pd
import numpy as np

def analyze(csv_file):
    try:
        df = pd.read_csv(csv_file)
        df.dropna(inplace=True)
        if len(df) == 0:
            print(f"No data in {csv_file}")
            return
        
        # Calculate Euclidean error for each point
        df['error'] = np.sqrt((df['Target_X'] - df['Actual_X'])**2 + (df['Target_Y'] - df['Actual_Y'])**2)
        
        # Group by Target Waypoint
        df['waypoint_id'] = df['Target_X'].astype(str) + "_" + df['Target_Y'].astype(str)
        
        print(f"--- Performance Analysis for {csv_file} ---")
        overall_rmse = np.sqrt(np.mean(df['error']**2))
        overall_max = df['error'].max()
        overall_mean = df['error'].mean()
        
        print(f"Overall RMSE: {overall_rmse*100:.2f} cm")
        print(f"Overall Mean Error: {overall_mean*100:.2f} cm")
        print(f"Overall Max Error: {overall_max*100:.2f} cm")
        
        print("\n--- Arrival Accuracy per Waypoint (Minimum Error Reached) ---")
        for wp, group in df.groupby('waypoint_id', sort=False):
            # Since we removed the 30s settling time, the "last 10 seconds" are now the departure to the next goal!
            # Instead, we just find the closest the robot got to this goal before advancing.
            min_error = group['error'].min()
            print(f"Waypoint {wp}: Minimum Arrival Error = {min_error*100:.2f} cm")
            
    except Exception as e:
        print(f"Error: {e}")

analyze("robot3_lidar_test.csv")
