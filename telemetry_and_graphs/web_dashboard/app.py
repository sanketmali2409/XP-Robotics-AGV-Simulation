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

import subprocess
import shlex

# Path to workspace so we can auto-source ROS + overlay if Flask was launched
# from a plain shell.
WORKSPACE_DIR = '/home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/agv_simulation_workspace'
NAV_LOG_DIR = '/tmp/dashboard_nav_logs'
os.makedirs(NAV_LOG_DIR, exist_ok=True)

@app.route('/api/navigate_to_node', methods=['POST'])
def navigate_to_node():
    data = request.json
    robot_name = data.get('robot', 'robot3')
    target_node = data.get('node', 'N1')

    if robot_name == 'robot1':
        return jsonify({'success': False, 'error': 'Robot 1 uses basic PID and does not support Nav2 Node Grid navigation.'}), 400

    # Always source ROS + workspace overlay so subprocess works even when Flask
    # was started from an un-sourced terminal.
    inner_cmd = (
        f"ros2 run grid_navigation go_to_node "
        f"--ros-args -p robot_name:={shlex.quote(robot_name)} "
        f"-p dest_node:={shlex.quote(target_node)}"
    )
    bash_cmd = (
        f"source /opt/ros/humble/setup.bash && "
        f"source {shlex.quote(WORKSPACE_DIR)}/install/setup.bash && "
        f"{inner_cmd}"
    )

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(NAV_LOG_DIR, f'{robot_name}_{target_node}_{timestamp}.log')

    try:
        print(f"[nav] {robot_name} -> {target_node}  (log: {log_path})")
        log_file = open(log_path, 'w')
        log_file.write(f"CMD: {bash_cmd}\n\n")
        log_file.flush()
        subprocess.Popen(
            ['bash', '-lc', bash_cmd],
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        return jsonify({
            'success': True,
            'message': f'Command sent to {robot_name} for destination {target_node}.',
            'log': log_path,
        })
    except Exception as e:
        print(f"Error sending command: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Run the server on all interfaces, port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
