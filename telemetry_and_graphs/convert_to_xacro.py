import re
with open("AGV.urdf", "r") as f:
    urdf = f.read()

# Add xacro header
urdf = urdf.replace('<robot name="(Unsaved)">', '<?xml version="1.0"?>\n<robot name="agv" xmlns:xacro="http://ros.org/wiki/xacro">\n    <xacro:arg name="prefix" default=""/>')

# Replace namespaces in plugins
urdf = urdf.replace('<namespace></namespace>', '<namespace>$(arg prefix)</namespace>')
urdf = urdf.replace('<namespace>/imu</namespace>', '<namespace>$(arg prefix)/imu</namespace>')

# Replace TF frames in diff_drive
urdf = urdf.replace('<odometry_frame>odom</odometry_frame>', '<odometry_frame>$(arg prefix)odom</odometry_frame>')
urdf = urdf.replace('<robot_base_frame>base_link</robot_base_frame>', '<robot_base_frame>$(arg prefix)base_link</robot_base_frame>')

# Add IMU frame
urdf = urdf.replace('<initial_orientation_as_reference>false</initial_orientation_as_reference>', '<initial_orientation_as_reference>false</initial_orientation_as_reference>\n                <frame_name>$(arg prefix)base_link</frame_name>')

# Add Lidar to scanner-v2
lidar_xml = """
    <gazebo reference="scanner-v2">
        <sensor type="ray" name="rplidar_sensor">
            <pose>0 0 0 0 0 0</pose>
            <visualize>false</visualize>
            <update_rate>10</update_rate>
            <ray>
                <scan>
                    <horizontal>
                        <samples>360</samples>
                        <resolution>1</resolution>
                        <min_angle>-3.14159</min_angle>
                        <max_angle>3.14159</max_angle>
                    </horizontal>
                </scan>
                <range>
                    <min>0.15</min>
                    <max>12.0</max>
                    <resolution>0.01</resolution>
                </range>
                <noise>
                    <type>gaussian</type>
                    <mean>0.0</mean>
                    <stddev>0.01</stddev>
                </noise>
            </ray>
            <plugin name="gazebo_ros_ray_sensor" filename="libgazebo_ros_ray_sensor.so">
                <ros>
                    <namespace>$(arg prefix)</namespace>
                    <remapping>~/out:=scan</remapping>
                </ros>
                <output_type>sensor_msgs/LaserScan</output_type>
                <frame_name>$(arg prefix)scanner-v2</frame_name>
            </plugin>
        </sensor>
    </gazebo>
"""
urdf = urdf.replace('</robot>', lidar_xml + '\n</robot>')

with open("agv.urdf.xacro", "w") as f:
    f.write(urdf)
print("agv.urdf.xacro created!")
