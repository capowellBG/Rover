import xacro
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    xacro_path = '/ros_ws/urdf/rover.urdf.xacro'
    robot_description = xacro.process_file(xacro_path).toxml()

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
        ),
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
        ),
    ])
