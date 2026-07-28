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
    
    map_yaml_file = os.path.join(pkg_share, 'maps', 'my_new_map.yaml')

    # Parse Xacro
    doc1 = xacro.process_file(xacro_file, mappings={'prefix': 'robot1/'})
    robot_desc1 = doc1.toxml()
    doc2 = xacro.process_file(xacro_file, mappings={'prefix': 'robot2/'})
    robot_desc2 = doc2.toxml()
    doc3 = xacro.process_file(xacro_file, mappings={'prefix': 'robot3/'})
    robot_desc3 = doc3.toxml()

    # Gazebo & RViz
    gazebo_server = ExecuteProcess(cmd=['gzserver', '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so', world_file], output='screen')
    gazebo_client = ExecuteProcess(cmd=['gzclient'], output='screen')
    rviz = Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_config_file], parameters=[{'use_sim_time': True}], output='screen')

    # Robot 1 (EKF only)
    rsp1 = Node(package='robot_state_publisher', executable='robot_state_publisher', namespace='robot1', parameters=[{'use_sim_time': True, 'robot_description': robot_desc1}])
    spawn1 = Node(package='gazebo_ros', executable='spawn_entity.py', arguments=['-entity', 'robot1', '-topic', '/robot1/robot_description', '-robot_namespace', 'robot1', '-y', '1.0'])
    ekf1 = Node(package='robot_localization', executable='ekf_node', namespace='robot1', parameters=[ekf_config_file, {'use_sim_time': True, 'odom_frame': 'robot1/odom', 'base_link_frame': 'robot1/base_link', 'world_frame': 'robot1/odom'}])
    pid1 = Node(package='agv', executable='goal_pid_controller', namespace='robot1', parameters=[{'use_sim_time': True, 'test_name': 'robot1_ekf_test', 'kp': 1.2, 'kd': 0.2, 'odom_topic': 'odometry/filtered'}])
    map_to_odom1 = Node(package='tf2_ros', executable='static_transform_publisher', arguments=['0', '1.0', '0', '0', '0', '0', 'map', 'robot1/odom'], parameters=[{'use_sim_time': True}])

    # Robot 2 (Navigating on Saved Map)
    rsp2 = Node(package='robot_state_publisher', executable='robot_state_publisher', namespace='robot2', parameters=[{'use_sim_time': True, 'robot_description': robot_desc2}])
    spawn2 = Node(package='gazebo_ros', executable='spawn_entity.py', arguments=['-entity', 'robot2', '-topic', '/robot2/robot_description', '-robot_namespace', 'robot2', '-y', '-1.0'])
    ekf2 = Node(package='robot_localization', executable='ekf_node', namespace='robot2', parameters=[ekf_config_file, {'use_sim_time': True, 'odom_frame': 'robot2/odom', 'base_link_frame': 'robot2/base_link', 'world_frame': 'robot2/odom'}], remappings=[('odometry/filtered', 'odometry/local')])
    
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
        output='screen',
        remappings=[
            ('scan', '/robot2/scan'),
            ('initialpose', '/robot2/initialpose'),
            ('amcl_pose', '/robot2/amcl_pose'),
            ('particle_cloud', '/robot2/particle_cloud')
        ],
        parameters=[{
            'use_sim_time': True,
            'odom_frame_id': 'robot2/odom',
            'base_frame_id': 'robot2/base_link',
            'global_frame_id': 'map',
            'set_initial_pose': True,
            'initial_pose.x': 0.0,
            'initial_pose.y': -1.0,
            'initial_pose.z': 0.0,
            'initial_pose.yaw': 0.0
        }]
    )
    
    # Lifecycle Manager to activate Map Server and AMCLs
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{'use_sim_time': True},
                    {'autostart': True},
                    {'node_names': ['map_server', 'amcl', 'amcl3']}]
    )

    tf_odom2 = Node(package='agv', executable='tf_to_odom', namespace='robot2', parameters=[{'base_frame': 'robot2/base_link', 'odom_frame': 'map', 'use_sim_time': True}])
    pid2 = Node(package='agv', executable='goal_pid_controller', namespace='robot2', parameters=[{'use_sim_time': True, 'test_name': 'robot2_lidar_test', 'kp': 0.5, 'ki': 0.01, 'kd': 0.1}])

    # Robot 3 (Navigating on Saved Map)
    rsp3 = Node(package='robot_state_publisher', executable='robot_state_publisher', namespace='robot3', parameters=[{'use_sim_time': True, 'robot_description': robot_desc3}])
    spawn3 = Node(package='gazebo_ros', executable='spawn_entity.py', arguments=['-entity', 'robot3', '-topic', '/robot3/robot_description', '-robot_namespace', 'robot3', '-y', '3.0'])
    ekf3 = Node(package='robot_localization', executable='ekf_node', namespace='robot3', parameters=[ekf_config_file, {'use_sim_time': True, 'odom_frame': 'robot3/odom', 'base_link_frame': 'robot3/base_link', 'world_frame': 'robot3/odom'}], remappings=[('odometry/filtered', 'odometry/local')])
    
    amcl3 = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl3',
        output='screen',
        arguments=['--ros-args', '-p', 'use_sim_time:=true'],
        remappings=[
            ('scan', '/robot3/scan'),
            ('initialpose', '/robot3/initialpose'),
            ('amcl_pose', '/robot3/amcl_pose'),
            ('particle_cloud', '/robot3/particle_cloud')
        ],
        parameters=[{
            'use_sim_time': True,
            'odom_frame_id': 'robot3/odom',
            'base_frame_id': 'robot3/base_link',
            'global_frame_id': 'map',
            'set_initial_pose': True,
            'initial_pose.x': 0.0,
            'initial_pose.y': 3.0,
            'initial_pose.z': 0.0,
            'initial_pose.yaw': 0.0
        }]
    )
    
    tf_odom3 = Node(package='agv', executable='tf_to_odom', namespace='robot3', parameters=[{'base_frame': 'robot3/base_link', 'odom_frame': 'map', 'use_sim_time': True}])
    
    nav2_robot3 = ExecuteProcess(
        cmd=['ros2', 'launch', 'agv', 'nav2_robot3_launch.py'],
        output='screen'
    )



    return LaunchDescription([
        gazebo_server, gazebo_client, rviz,
        rsp1, spawn1, ekf1, pid1, map_to_odom1,
        rsp2, spawn2, ekf2, amcl, tf_odom2, pid2,
        map_server, lifecycle_manager,
        rsp3, spawn3, ekf3, amcl3, tf_odom3, nav2_robot3
    ])
