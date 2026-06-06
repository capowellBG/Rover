from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    slam_mode = LaunchConfiguration('slam_mode').perform(context)

    rplidar_node = Node(
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
    )

    rf2o_node = Node(
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
            'init_pose_from_topic': '',
        }],
        arguments=['--ros-args', '--log-level', 'warn'],
        output='screen',
    )

    if slam_mode == 'localization':
        slam_node = Node(
            package='slam_toolbox',
            executable='localization_slam_toolbox_node',
            name='slam_toolbox',
            parameters=[
                '/ros_ws/config/slam_toolbox_params.yaml',
                {'mode': 'localization', 'map_file_name': '/ros_ws/maps/my_map', 'map_start_at_dock': True},
            ],
            output='screen',
        )
    else:
        slam_node = Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            parameters=['/ros_ws/config/slam_toolbox_params.yaml'],
            output='screen',
        )

    return [rplidar_node, rf2o_node, slam_node]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'slam_mode',
            default_value='mapping',
            description='SLAM mode: mapping or localization',
        ),
        OpaqueFunction(function=launch_setup),
    ])
