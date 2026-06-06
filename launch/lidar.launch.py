from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rplidar_ros',
            executable='rplidar_node',
            name='rplidar_node',
            parameters=[{
                'channel_type': 'serial',
                'serial_port': '/dev/ttyUSB0',
                'serial_baudrate': 256000,
                'frame_id': 'laser',
                'inverted': False,
                'angle_compensate': True,
                'scan_mode': 'Sensitivity',
            }],
            output='screen',
        ),

        Node(
            package='rf2o_laser_odometry',
            executable='rf2o_laser_odometry_node',
            name='rf2o_laser_odometry',
            parameters=[{
                'laser_scan_topic': '/scan',
                'odom_topic': '/odom',
                'publish_tf': True,
                'base_frame_id': 'base_footprint',
                'odom_frame_id': 'odom',
                'freq': 10.0,
                # Empty => start odometry from pose 0 immediately. Otherwise rf2o
                # waits forever for an initial pose on /base_pose_ground_truth.
                'init_pose_from_topic': '',
            }],
            # rf2o INFO-logs odom every scan; raise threshold to quiet the spam.
            arguments=['--ros-args', '--log-level', 'warn'],
            output='screen',
        ),

        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            parameters=['/ros_ws/config/slam_toolbox_params.yaml'],
            output='screen',
        ),
    ])
