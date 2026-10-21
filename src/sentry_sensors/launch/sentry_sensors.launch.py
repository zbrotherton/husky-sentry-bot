
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
    zed_launch = os.path.join(
        get_package_share_directory("zed_wrapper"),
        "launch",
        "zed_camera.launch.py"
    )

    zed_config = os.path.join(
        get_package_share_directory("sentry_sensors"),
        "config",
        "zed_params.yaml"
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

    return LaunchDescription([zed])
