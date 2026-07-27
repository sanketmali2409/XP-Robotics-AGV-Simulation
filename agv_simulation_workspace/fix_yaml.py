import sys
import yaml

with open('src/agv/config/nav2_params.yaml', 'r') as f:
    lines = f.readlines()

new_lines = ["robot3:\n"]
for line in lines:
    new_lines.append("  " + line)

content = "".join(new_lines)
content = content.replace(': "base_footprint"', ': "robot3/base_footprint"')
content = content.replace(': "odom"', ': "robot3/odom"')
content = content.replace('robot_base_frame: base_link', 'robot_base_frame: robot3/base_link')
content = content.replace('global_frame: odom', 'global_frame: robot3/odom')
content = content.replace('odom_topic: odom', 'odom_topic: robot3/odom')
content = content.replace('topic: scan', 'topic: robot3/scan')
content = content.replace('observation_sources: scan', 'observation_sources: robot3/scan')
content = content.replace('scan_topic: scan', 'scan_topic: robot3/scan')

with open('src/agv/config/nav2_params.yaml', 'w') as f:
    f.write(content)
