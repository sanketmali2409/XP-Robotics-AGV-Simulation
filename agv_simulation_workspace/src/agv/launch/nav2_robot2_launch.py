import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import PushRosNamespace, SetRemap
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_share = get_package_share_directory('agv')

    nav2_params_file = os.path.join(
        pkg_share,
        'config',
        'nav2_params_robot2.yaml'
    )

    return LaunchDescription([
        GroupAction([

            PushRosNamespace('robot2'),

            SetRemap(
                src='map',
                dst='/map'
            ),

            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        pkg_share,
                        'launch',
                        'my_navigation_launch.py'
                    )
                ),

                launch_arguments={
                    'namespace': 'robot2',
                    'use_namespace': 'False',
                    'use_sim_time': 'True',
                    'params_file': nav2_params_file,
                    'autostart': 'True',
                    'use_composition': 'False'
                }.items()
            )
        ])
    ])