from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # D455 publishes raw accel+gyro only (orientation_covariance[0] = -1), so the
    # raw /camera/camera/imu has no usable orientation. Madgwick fuses it into an
    # oriented /imu/data that rgbd_odometry can use to constrain rotation/gravity.
    imu_filter = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter',
        parameters=[{
            'use_mag': False,
            'world_frame': 'enu',
            'publish_tf': False,
        }],
        remappings=[
            ('imu/data_raw', '/camera/camera/imu'),
            ('imu/data', '/imu/data'),
        ],
        output='screen',
    )

    # Visual-inertial odometry: owns odom -> base_footprint. No mapping here; the
    # LiDAR + slam_toolbox own map -> odom. Depth must be aligned to color
    # (align_depth.enable: true in camera_config.yaml).
    rgbd_odometry = Node(
        package='rtabmap_odom',
        executable='rgbd_odometry',
        name='rgbd_odometry',
        parameters=[{
            'frame_id': 'base_footprint',
            'odom_frame_id': 'odom',
            'publish_tf': True,
            'approx_sync': True,
            'wait_imu_to_init': True,
            'guess_frame_id': 'base_footprint',
            'wait_for_transform': 0.2,
        }],
        remappings=[
            ('rgb/image', '/camera/camera/color/image_raw'),
            ('depth/image', '/camera/camera/aligned_depth_to_color/image_raw'),
            ('rgb/camera_info', '/camera/camera/color/camera_info'),
            ('imu', '/imu/data'),
        ],
        arguments=['--ros-args', '--log-level', 'warn'],
        output='screen',
    )

    return LaunchDescription([imu_filter, rgbd_odometry])
