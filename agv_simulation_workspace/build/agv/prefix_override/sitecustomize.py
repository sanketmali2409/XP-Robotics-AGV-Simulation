import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/agv_simulation_workspace/install/agv'
