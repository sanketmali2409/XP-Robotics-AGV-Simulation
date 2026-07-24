import xml.etree.ElementTree as ET
import sys

def prefix_urdf(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # We want to prepend $(arg prefix) to all link and joint names,
    # as well as parent/child links and gazebo references.
    
    # We shouldn't prefix if it already has $(arg prefix)
    prefix_str = "$(arg prefix)"

    for link in root.findall('.//link'):
        name = link.get('name')
        if name and not name.startswith(prefix_str):
            link.set('name', prefix_str + name)

    for joint in root.findall('.//joint'):
        name = joint.get('name')
        if name and not name.startswith(prefix_str):
            joint.set('name', prefix_str + name)
        
        parent = joint.find('parent')
        if parent is not None:
            plink = parent.get('link')
            if plink and not plink.startswith(prefix_str):
                parent.set('link', prefix_str + plink)
                
        child = joint.find('child')
        if child is not None:
            clink = child.get('link')
            if clink and not clink.startswith(prefix_str):
                child.set('link', prefix_str + clink)

    for gazebo in root.findall('.//gazebo'):
        ref = gazebo.get('reference')
        if ref and not ref.startswith(prefix_str):
            gazebo.set('reference', prefix_str + ref)

    # Some gazebo plugins might also reference joints/links
    # For diff_drive:
    for plugin in root.findall('.//plugin[@name="diff_drive"]'):
        for tag in ['left_joint', 'right_joint', 'odometry_frame', 'robot_base_frame']:
            elem = plugin.find(tag)
            if elem is not None and elem.text and not elem.text.startswith(prefix_str):
                elem.text = prefix_str + elem.text

    for plugin in root.findall('.//plugin[@name="joint_state"]'):
        for elem in plugin.findall('joint_name'):
            if elem is not None and elem.text and not elem.text.startswith(prefix_str):
                elem.text = prefix_str + elem.text
                
    for plugin in root.findall('.//plugin[@name="imu_plugin"]'):
        frame_name = plugin.find('frame_name')
        if frame_name is not None and frame_name.text and not frame_name.text.startswith(prefix_str):
            frame_name.text = prefix_str + frame_name.text

    for plugin in root.findall('.//plugin[@name="gazebo_ros_ray_sensor"]'):
        frame_name = plugin.find('frame_name')
        if frame_name is not None and frame_name.text and not frame_name.text.startswith(prefix_str):
            frame_name.text = prefix_str + frame_name.text

    # Write back
    tree.write(file_path, xml_declaration=True, encoding='utf-8')

if __name__ == '__main__':
    prefix_urdf(sys.argv[1])
