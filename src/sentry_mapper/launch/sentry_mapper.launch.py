import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.substitutions import FindPackageShare, Command
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    
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
    
    sentry_mapper_package = get_package_share_directory('sentry_mapper')
    slam_toolbox_package  = get_package_share_directory('slam_toolbox')
    
    slam_toolbox_launch_path = os.path.join(slam_toolbox_package , 'launch', 'online_async_launch.py')
    config_path = os.path.join(sentry_mapper_package, 'config', 'mapper_params_online_async.yaml')

    mapper = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_toolbox_launch_path),
        launch_arguments={
            'params_file' : config_path
        }.items()
    )
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
        'robot_description': Command([
                'xacro ', os.path.join(sentry_mapper_package, 'urdf/mount.urdf.xacro'),
            ])
        }],
    )

    nodes = [
        rplidar,
        mapper,
        robot_state_publisher
    ]

    return LaunchDescription(nodes)
