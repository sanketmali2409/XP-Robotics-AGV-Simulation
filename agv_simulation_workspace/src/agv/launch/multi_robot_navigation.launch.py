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
    doc1 = xacro.process_file(xacro_file, mappings={
        'prefix': 'robot1/',
        'publish_odom_tf': 'false',
        'gazebo_body_material': 'Gazebo/Grey',
        'gazebo_lidar_material': 'Gazebo/Blue'
    })
    robot_desc1 = doc1.toxml()
    doc2 = xacro.process_file(xacro_file, mappings={
        'prefix': 'robot2/',
        'publish_odom_tf': 'true',
        'gazebo_body_material': 'Gazebo/Green',
        'gazebo_lidar_material': 'Gazebo/Yellow'
    })
    robot_desc2 = doc2.toxml()
    doc3 = xacro.process_file(xacro_file, mappings={
        'prefix': 'robot3/',
        'publish_odom_tf': 'false',
        'gazebo_body_material': 'Gazebo/Grey',
        'gazebo_lidar_material': 'Gazebo/Blue'
    })
    robot_desc3 = doc3.toxml()

    # Gazebo & RViz
    gazebo_server = ExecuteProcess(cmd=['gzserver', '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so', world_file], output='screen')
    gazebo_client = ExecuteProcess(cmd=['gzclient'], output='screen')
    rviz = Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_config_file], parameters=[{'use_sim_time': True}], output='screen')

    # Robot 1 (EKF only)
    rsp1 = Node(package='robot_state_publisher', executable='robot_state_publisher', namespace='robot1', parameters=[{'use_sim_time': True, 'robot_description': robot_desc1}])
    spawn1 = Node(package='gazebo_ros', executable='spawn_entity.py', arguments=['-entity', 'robot1', '-topic', '/robot1/robot_description', '-robot_namespace', 'robot1', '-y', '1.0'])
    ekf1 = Node(package='robot_localization', executable='ekf_node', namespace='robot1', parameters=[ekf_config_file, {'use_sim_time': True, 'odom_frame': 'robot1/odom', 'base_link_frame': 'robot1/base_link', 'world_frame': 'robot1/odom'}], remappings=[('odometry/filtered', 'odometry/local')])
    pid1 = Node(package='agv', executable='goal_pid_controller', namespace='robot1', parameters=[{'use_sim_time': True, 'test_name': 'robot1_ekf_test', 'kp': 1.0, 'ki': 0.05, 'kd': 0.2}])
    map_to_odom1 = Node(package='tf2_ros', executable='static_transform_publisher', namespace='robot1', arguments=['0', '1.0', '0', '0', '0', '0', 'map', 'robot1/odom'])
    traj1 = Node(package='agv', executable='trajectory_visualizer', namespace='robot1', parameters=[{'use_sim_time': True, 'robot_name': 'robot1', 'odom_topic': 'odometry/local'}])

    # Robot 2 (localize on saved map using LiDAR only)
    rsp2 = Node(package='robot_state_publisher', executable='robot_state_publisher', namespace='robot2', parameters=[{'use_sim_time': True, 'robot_description': robot_desc2}])
    spawn2 = Node(package='gazebo_ros', executable='spawn_entity.py', arguments=['-entity', 'robot2', '-topic', '/robot2/robot_description', '-robot_namespace', 'robot2', '-y', '-1.0'])
    ekf2 = Node(package='robot_localization', executable='ekf_node', namespace='robot2', parameters=[ekf_config_file, {'use_sim_time': True, 'odom_frame': 'robot2/odom', 'base_link_frame': 'robot2/base_link', 'world_frame': 'robot2/odom'}])
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        remappings=[
            ('scan', '/robot2/scan_filtered'),
            ('initialpose', '/robot2/initialpose'),
            ('amcl_pose', '/robot2/amcl_pose'),
            ('particle_cloud', '/robot2/particle_cloud')
        ],
        parameters=[{
            'use_sim_time': True,
            'odom_frame_id': 'robot2/odom',
            'base_frame_id': 'robot2/base_link',
            'global_frame_id': 'map',
            'scan_topic': '/robot2/scan_filtered',
            'set_initial_pose': True,
            'initial_pose.x': 0.0,
            'initial_pose.y': -1.0,
            'initial_pose.z': 0.0,
            'initial_pose.yaw': 0.0
        }]
    )
    scan_filter2 = Node(
        package='agv', executable='scan_self_filter',
        namespace='robot2', name='scan_self_filter',
        parameters=[{'use_sim_time': True, 'input_topic': 'scan', 'output_topic': 'scan_filtered'}]
    )
    pose_logger2 = Node(
        package='agv', executable='pose_logger', name='pose_logger2',
        parameters=[{
            'use_sim_time': True,
            'robot_name': 'robot2',
            'odom_topic': 'odometry/global_amcl',
            'csv_path': '/home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/agv_simulation_workspace/robot2_lidar_test.csv',
        }]
    )
    
    # Map Server
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{'use_sim_time': True, 'yaml_filename': map_yaml_file}]
    )
    
    # Lifecycle Manager to activate Map Server and AMCL localization
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
    
    # Nav2 Path Planner for Robot 2
    nav2_robot2 = ExecuteProcess(
        cmd=['ros2', 'launch', 'agv', 'nav2_robot2_launch.py'],
        output='screen'
    )
    traj2 = Node(package='agv', executable='trajectory_visualizer', namespace='robot2', parameters=[{'use_sim_time': True, 'robot_name': 'robot2', 'odom_topic': 'odometry/global_amcl'}])

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
            ('scan', '/robot3/scan_filtered'),
            ('initialpose', '/robot3/initialpose'),
            ('amcl_pose', '/robot3/amcl_pose'),
            ('particle_cloud', '/robot3/particle_cloud')
        ],
        parameters=[{
            'use_sim_time': True,
            'odom_frame_id': 'robot3/odom',
            'base_frame_id': 'robot3/base_link',
            'global_frame_id': 'map',
            'scan_topic': '/robot3/scan_filtered',
            'set_initial_pose': True,
            'initial_pose.x': 0.0,
            'initial_pose.y': 3.0,
            'initial_pose.z': 0.0,
            'initial_pose.yaw': 0.0
        }]
    )
    scan_filter3 = Node(
        package='agv', executable='scan_self_filter',
        namespace='robot3', name='scan_self_filter',
        parameters=[{'use_sim_time': True, 'input_topic': 'scan', 'output_topic': 'scan_filtered'}]
    )
    pose_logger3 = Node(
        package='agv', executable='pose_logger', name='pose_logger3',
        parameters=[{
            'use_sim_time': True,
            'robot_name': 'robot3',
            'odom_topic': 'odometry/global_amcl',
            'csv_path': '/home/sanket/Documents/XP_Robotics/StepFile_gazebo/AGV/agv_simulation_workspace/robot3_lidar_test.csv',
        }]
    )
    
    tf_odom3 = Node(package='agv', executable='tf_to_odom', namespace='robot3', parameters=[{'base_frame': 'robot3/base_link', 'odom_frame': 'map', 'use_sim_time': True}])
    
    nav2_robot3 = ExecuteProcess(
        cmd=['ros2', 'launch', 'agv', 'nav2_robot3_launch.py'],
        output='screen'
    )
    traj3 = Node(package='agv', executable='trajectory_visualizer', namespace='robot3', parameters=[{'use_sim_time': True, 'robot_name': 'robot3', 'odom_topic': 'odometry/global_amcl'}])



    return LaunchDescription([
        gazebo_server, gazebo_client, rviz,
        rsp1, spawn1, ekf1, pid1, map_to_odom1, traj1,
        rsp2, spawn2, ekf2, scan_filter2, amcl, tf_odom2,
        nav2_robot2, traj2, pose_logger2,
        map_server, lifecycle_manager,
        rsp3, spawn3, ekf3, scan_filter3, amcl3, tf_odom3, nav2_robot3, traj3, pose_logger3
    ])
