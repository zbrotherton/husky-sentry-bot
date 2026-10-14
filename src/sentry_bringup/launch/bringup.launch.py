from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [FindPackageShare('sentry_navigation'),
                 '/launch',
                 '/sentry_navigation.launch.py']
            )
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [FindPackageShare('sentry_mapper'),
                 '/launch',
                 '/sentry_mapper.launch.py']
            )
        ),
        Node(
            package='foxglove_bridge',
            executable='foxglove_bridge'
        )
    ])