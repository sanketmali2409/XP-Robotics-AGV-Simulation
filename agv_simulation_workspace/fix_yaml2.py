import sys

with open('src/agv/config/nav2_params.yaml', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('robot3:\n'):
        continue
    if line.startswith('  '):
        new_lines.append(line[2:])
    else:
        new_lines.append(line)

with open('src/agv/config/nav2_params.yaml', 'w') as f:
    f.writelines(new_lines)
