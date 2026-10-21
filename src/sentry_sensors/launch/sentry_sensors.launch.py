
import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import (
    PythonLaunchDescriptionSource
)
from ament_index_python.packages import (
    get_package_share_directory
)


def generate_launch_description():
    sentry_sensors_package = get_package_share_directory('sentry_sensors')

    zed_launch = os.path.join(
        get_package_share_directory("zed_wrapper"),
        "launch",
        "zed_camera.launch.py"
    )

    zed_config = os.path.join(
        sentry_sensors_package,
        "config",
        "zed_params.yaml"
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
        'robot_description': Command([
                'xacro ', os.path.join(sentry_sensors_package, 'urdf/zed.urdf.xacro'),
            ])
        }],
    )

    zed = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(zed_launch),
        launch_arguments={
            "camera_model": "zed2i",
            "publish_tf": "false",
            "publish_map_tf": "false",
            "ros_params_override_path": zed_config,
        }.items()
    )

    return LaunchDescription([zed, robot_state_publisher])
