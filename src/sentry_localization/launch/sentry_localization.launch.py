import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    sentry_localization_package = get_package_share_directory('sentry_localization')
    param_file = os.path.join(sentry_localization_package, 'config', 'local_ekf_params.yaml')

    ekf_node_local = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_node_local',
        output='screen',
        parameters=[param_file],
        remappings=[('odometry/filtered', '/odometry/local')],
    )

    return LaunchDescription([
        ekf_node_local,
    ])
