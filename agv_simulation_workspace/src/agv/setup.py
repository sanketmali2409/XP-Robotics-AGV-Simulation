from setuptools import setup
import os
from glob import glob

package_name = 'agv'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
        (os.path.join('share', package_name), glob('*.urdf')),
        (os.path.join('share', package_name), glob('*.xacro')),
        (os.path.join('share', package_name), glob('*.sdf')),
        (os.path.join('share', package_name), glob('*.world')),
        (os.path.join('share', package_name, 'meshes'), glob('meshes/*')),
        (os.path.join('share', package_name, 'maps'), glob('maps/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='AGV control and simulation package',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'goal_pid_controller = agv.goal_pid_controller:main',
            'tf_to_odom = agv.tf_to_odom:main',
            'run_tests = agv.run_tests:main',
            'analyze_results = agv.analyze_results:main',
            'test_orchestrator = agv.test_orchestrator:main',
            'trajectory_visualizer = agv.trajectory_visualizer:main',
            'random_orchestrator = agv.random_orchestrator:main',
            'scan_self_filter = agv.scan_self_filter:main',
            'pose_logger = agv.pose_logger:main'
        ],
    },
)
