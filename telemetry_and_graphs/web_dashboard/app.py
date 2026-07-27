from flask import Flask, render_template, jsonify, request
import pandas as pd
import os
import base64
from datetime import datetime

app = Flask(__name__)

# Paths to the CSV files (assuming the simulation is run from ../agv_simulation_workspace)
ROBOT1_CSV = '../../agv_simulation_workspace/robot1_ekf_test.csv'
ROBOT2_CSV = '../../agv_simulation_workspace/robot2_lidar_test.csv'
ROBOT3_CSV = '../../agv_simulation_workspace/robot3_lidar_test.csv'

def parse_csv(filepath):
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return {'timestamp': [], 'actual_x': [], 'target_x': []}
    
    try:
        # Use on_bad_lines='skip' to avoid crashes if Gazebo writes a partial line
        df = pd.read_csv(filepath, on_bad_lines='skip')
        df = df.dropna() # Drop any rows containing NaN to ensure valid JSON serialization
        
        # Ensure we have the required columns
        if 'Timestamp' in df.columns and 'Actual_X' in df.columns and 'Target_X' in df.columns:
            return {
                'timestamp': df['Timestamp'].tolist(),
                'target_x': df['Target_X'].tolist(),
                'target_y': df['Target_Y'].tolist() if 'Target_Y' in df.columns else [0.0]*len(df),
                'actual_x': df['Actual_X'].tolist(),
                'actual_y': df['Actual_Y'].tolist() if 'Actual_Y' in df.columns else [0.0]*len(df)
            }
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        
    return {'timestamp': [], 'actual_x': [], 'target_x': []}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def data():
    robot1_data = parse_csv(ROBOT1_CSV)
    robot2_data = parse_csv(ROBOT2_CSV)
    robot3_data = parse_csv(ROBOT3_CSV)
    
    return jsonify({
        'robot1': robot1_data,
        'robot2': robot2_data,
        'robot3': robot3_data
    })

import shutil

@app.route('/api/save_graph', methods=['POST'])
def save_graph():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'success': False, 'error': 'No image data provided'}), 400
            
        # Extract the base64 part of the data URL
        image_data = data['image'].split(',')[1]
        
        # Save directory
        save_dir = '/home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/saved_results'
        os.makedirs(save_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'dashboard_export_{timestamp}.png'
        filepath = os.path.join(save_dir, filename)
        
        # Decode and save image
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(image_data))
            
        return jsonify({'success': True, 'path': filepath})
    except Exception as e:
        print(f"Error saving graph and CSVs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Run the server on all interfaces, port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
