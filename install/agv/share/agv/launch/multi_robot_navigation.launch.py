import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_share = get_package_share_directory('agv')
    xacro_file = os.path.join(pkg_share, 'agv.urdf.xacro')
    world_file = os.path.join(pkg_share, 'AGV.world')
    rviz_config_file = os.path.join(pkg_share, 'config', 'agv.rviz')
    ekf_config_file = os.path.join(pkg_share, 'config', 'ekf.yaml')
    
    # The map file we saved earlier
    map_yaml_file = os.path.join(pkg_share, '..', '..', '..', '..', 'maps', 'room_map.yaml')
    # Use absolute path to ensure map_server finds it reliably
    map_yaml_file = '/home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/maps/room_map.yaml'

    # Parse Xacro
    doc1 = xacro.process_file(xacro_file, mappings={'prefix': 'robot1/'})
    robot_desc1 = doc1.toxml()
    doc2 = xacro.process_file(xacro_file, mappings={'prefix': 'robot2/'})
    robot_desc2 = doc2.toxml()

    # Gazebo & RViz
    gazebo_server = ExecuteProcess(cmd=['gzserver', '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so', world_file], output='screen')
    gazebo_client = ExecuteProcess(cmd=['gzclient'], output='screen')
    rviz = Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_config_file], parameters=[{'use_sim_time': True}], output='screen')

    # Robot 1 (EKF only)
    rsp1 = Node(package='robot_state_publisher', executable='robot_state_publisher', namespace='robot1', parameters=[{'use_sim_time': True, 'robot_description': robot_desc1}])
    spawn1 = Node(package='gazebo_ros', executable='spawn_entity.py', arguments=['-entity', 'robot1', '-topic', '/robot1/robot_description', '-robot_namespace', 'robot1', '-y', '1.0'])
    ekf1 = Node(package='robot_localization', executable='ekf_node', namespace='robot1', parameters=[ekf_config_file, {'use_sim_time': True, 'odom_frame': 'robot1/odom', 'base_link_frame': 'robot1/base_link', 'world_frame': 'robot1/odom'}])
    pid1 = Node(package='agv', executable='goal_pid_controller', namespace='robot1', parameters=[{'use_sim_time': True, 'test_name': 'robot1_ekf_test'}])
    map_to_odom1 = Node(package='tf2_ros', executable='static_transform_publisher', arguments=['0', '1.0', '0', '0', '0', '0', 'map', 'robot1/odom'], parameters=[{'use_sim_time': True}])

    # Robot 2 (Navigating on Saved Map)
    rsp2 = Node(package='robot_state_publisher', executable='robot_state_publisher', namespace='robot2', parameters=[{'use_sim_time': True, 'robot_description': robot_desc2}])
    spawn2 = Node(package='gazebo_ros', executable='spawn_entity.py', arguments=['-entity', 'robot2', '-topic', '/robot2/robot_description', '-robot_namespace', 'robot2', '-y', '-1.0'])
    ekf2 = Node(package='robot_localization', executable='ekf_node', namespace='robot2', parameters=[ekf_config_file, {'use_sim_time': True, 'odom_frame': 'robot2/odom', 'base_link_frame': 'robot2/base_link', 'world_frame': 'robot2/odom'}])
    
    # Map Server
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{'use_sim_time': True, 'yaml_filename': map_yaml_file}]
    )
    
    # AMCL for Localization (Replaces SLAM)
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        namespace='robot2',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'odom_frame_id': 'robot2/odom',
            'base_frame_id': 'robot2/base_link',
            'global_frame_id': 'map',
            'scan_topic': '/robot2/scan',
            'set_initial_pose': True,
            'initial_pose': {'x': 0.0, 'y': -1.0, 'z': 0.0, 'yaw': 0.0}
        }]
    )
    
    # Lifecycle Manager to activate Map Server and AMCL
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{'use_sim_time': True},
                    {'autostart': True},
                    {'node_names': ['map_server', 'robot2/amcl']}]
    )

    tf_odom2 = Node(package='agv', executable='tf_to_odom', namespace='robot2', parameters=[{'base_frame': 'robot2/base_link', 'odom_frame': 'map'}])
    pid2 = Node(package='agv', executable='goal_pid_controller', namespace='robot2', parameters=[{'test_name': 'robot2_lidar_test'}])

    return LaunchDescription([
        SetEnvironmentVariable('DISPLAY', ':1'),
        gazebo_server, gazebo_client, rviz,
        rsp1, spawn1, ekf1, pid1, map_to_odom1,
        rsp2, spawn2, ekf2, map_server, amcl, lifecycle_manager, tf_odom2, pid2
    ])
