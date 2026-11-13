import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    sentry_sensors_package = get_package_share_directory(
        'sentry_sensors'
    )

    zed_launch = os.path.join(
        get_package_share_directory('zed_wrapper'),
        'launch',
        'zed_camera.launch.py'
    )

    zed_config = os.path.join(
        sentry_sensors_package,
        'config',
        'zed_params.yaml'
    )

    zed = GroupAction(
        scoped=True,
        forwarding=False,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(zed_launch),
                launch_arguments={
                    'camera_model': 'zed2i',
                    'publish_tf': 'false',
                    'publish_map_tf': 'false',
                    'ros_params_override_path': zed_config,
                }.items()
            )
        ]
    )

    rplidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("rplidar_ros"),
             '/launch',
             '/rplidar_s2e_launch.py']
        ),
        launch_arguments={
            'udp_ip' : '192.168.131.20',
            'frame_id' : 'laser_frame'
        }.items()
    )

    return LaunchDescription([
        zed,
        rplidar
    ])