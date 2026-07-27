import subprocess
print("Starting launch file...")
p = subprocess.Popen('source install/setup.bash && ros2 launch agv multi_robot_navigation.launch.py', shell=True, executable='/bin/bash', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
try:
    outs, errs = p.communicate(timeout=10)
except subprocess.TimeoutExpired:
    p.kill()
    outs, errs = p.communicate()
with open('launch_out.txt', 'wb') as f:
    f.write(outs)
with open('launch_err.txt', 'wb') as f:
    f.write(errs)
print("Done")
