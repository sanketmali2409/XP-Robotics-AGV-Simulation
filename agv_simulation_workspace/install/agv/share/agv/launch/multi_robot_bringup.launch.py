import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import xacro

def generate_launch_description():
    pkg_share = get_package_share_directory('agv')
    xacro_file = os.path.join(pkg_share, 'agv.urdf.xacro')
    world_file = os.path.join(pkg_share, 'AGV.world')
    rviz_config_file = os.path.join(pkg_share, 'config', 'agv.rviz')
    ekf_config_file = os.path.join(pkg_share, 'config', 'ekf.yaml')

    # Parse Xacro for Robot 1 (EKF)
    doc1 = xacro.process_file(xacro_file, mappings={'prefix': 'robot1/'})
    robot_desc1 = doc1.toxml()

    # Parse Xacro for Robot 2 (LiDAR)
    doc2 = xacro.process_file(xacro_file, mappings={'prefix': 'robot2/'})
    robot_desc2 = doc2.toxml()

    # Parse Xacro for Robot 3 (LiDAR - SLAM)
    doc3 = xacro.process_file(xacro_file, mappings={'prefix': 'robot3/'})
    robot_desc3 = doc3.toxml()

    # Common Nodes
    gazebo_server = ExecuteProcess(cmd=['gzserver', '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so', world_file], output='screen')
    gazebo_client = ExecuteProcess(cmd=['gzclient'], output='screen')
    rviz = Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_config_file], parameters=[{'use_sim_time': True}], output='screen')

    # Robot 1 (EKF)
    rsp1 = Node(package='robot_state_publisher', executable='robot_state_publisher', namespace='robot1', parameters=[{'use_sim_time': True, 'robot_description': robot_desc1}])
    spawn1 = Node(package='gazebo_ros', executable='spawn_entity.py', arguments=['-entity', 'robot1', '-topic', '/robot1/robot_description', '-robot_namespace', 'robot1', '-y', '1.0'])
    ekf1 = Node(
        package='robot_localization', executable='ekf_node', namespace='robot1',
        parameters=[ekf_config_file, {'use_sim_time': True, 'odom_frame': 'robot1/odom', 'base_link_frame': 'robot1/base_link', 'world_frame': 'robot1/odom'}],
        remappings=[('imu', 'imu/data')]
    )
    pid1 = Node(package='agv', executable='goal_pid_controller', namespace='robot1', parameters=[{'use_sim_time': True, 'test_name': 'robot1_ekf_test'}])

    # Robot 2 (LiDAR)
    rsp2 = Node(package='robot_state_publisher', executable='robot_state_publisher', namespace='robot2', parameters=[{'use_sim_time': True, 'robot_description': robot_desc2}])
    spawn2 = Node(package='gazebo_ros', executable='spawn_entity.py', arguments=['-entity', 'robot2', '-topic', '/robot2/robot_description', '-robot_namespace', 'robot2', '-y', '-1.0'])
    
    ekf2 = Node(
        package='robot_localization', executable='ekf_node', namespace='robot2',
        parameters=[ekf_config_file, {'use_sim_time': True, 'odom_frame': 'robot2/odom', 'base_link_frame': 'robot2/base_link', 'world_frame': 'robot2/odom'}],
        remappings=[('imu', 'imu/data')]
    )

    tf_odom2 = Node(package='agv', executable='tf_to_odom', namespace='robot2', parameters=[{'base_frame': 'robot2/base_link', 'odom_frame': 'robot2/odom', 'use_sim_time': True}])
    pid2 = Node(package='agv', executable='goal_pid_controller', namespace='robot2', parameters=[{'test_name': 'robot2_lidar_test', 'use_sim_time': True}])

    # Robot 3 (LiDAR - Mapper)
    rsp3 = Node(package='robot_state_publisher', executable='robot_state_publisher', namespace='robot3', parameters=[{'use_sim_time': True, 'robot_description': robot_desc3}])
    spawn3 = Node(package='gazebo_ros', executable='spawn_entity.py', arguments=['-entity', 'robot3', '-topic', '/robot3/robot_description', '-robot_namespace', 'robot3', '-y', '3.0'])
    
    ekf3 = Node(
        package='robot_localization', executable='ekf_node', namespace='robot3',
        parameters=[ekf_config_file, {'use_sim_time': True, 'odom_frame': 'robot3/odom', 'base_link_frame': 'robot3/base_link', 'world_frame': 'robot3/odom'}],
        remappings=[('odometry/filtered', 'odometry/local'), ('imu', 'imu/data')]
    )

    slam3 = Node(
        package='slam_toolbox', executable='async_slam_toolbox_node', namespace='robot3',
        parameters=[{
            'use_sim_time': True,
            'odom_frame': 'robot3/odom',
            'base_frame': 'robot3/base_link',
            'map_frame': 'map',
            'scan_topic': '/robot3/scan',
            'resolution': 0.05
        }]
    )
    # Convert TF back to odometry for the PID controller
    tf_odom3 = Node(package='agv', executable='tf_to_odom', namespace='robot3', parameters=[{'base_frame': 'robot3/base_link', 'odom_frame': 'map', 'use_sim_time': True}])
    pid3 = Node(package='agv', executable='goal_pid_controller', namespace='robot3', parameters=[{'test_name': 'robot3_lidar_test', 'use_sim_time': True}])

    # Static TF map -> robot1/odom
    map_to_odom1 = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '1.0', '0', '0', '0', '0', 'map', 'robot1/odom'],
        parameters=[{'use_sim_time': True}]
    )

    # Static TF map -> robot2/odom
    map_to_odom2 = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '-1.0', '0', '0', '0', '0', 'map', 'robot2/odom'],
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        SetEnvironmentVariable('DISPLAY', ':1'),
        gazebo_server, gazebo_client, rviz,
        rsp1, spawn1, ekf1, pid1, map_to_odom1,
        rsp2, spawn2, ekf2, tf_odom2, pid2, map_to_odom2,
        rsp3, spawn3, ekf3, slam3, tf_odom3, pid3
    ])
