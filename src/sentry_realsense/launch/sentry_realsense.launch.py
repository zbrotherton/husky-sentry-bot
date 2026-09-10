import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import Command
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    realsense_package = get_package_share_directory('realsense2_camera')
    sentry_realsense_package  = FindPackageShare(package='sentry_realsense_package').find('sentry_realsense')

    realsense_launch_path = os.path.join(realsense_package, 'launch', 'rs_launch.py')
    
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
        'robot_description': Command([
                'xacro ', os.path.join(sentry_realsense_package, 'urdf/mount.urdf.xacro'),
            ])
        }],
    )
    

    imu_filter = Node(
        package='imu_filter_madgwick', 
        executable='imu_filter_madgwick_node',
        output='screen',
        remappings=[
            ('/imu/data_raw', '/camera/camera/imu'),
            ('imu/data', '/rtabmap/imu')
        ],
        parameters=[
            {'use_mag' : False},
            {'publish_tf' : True},
            {'fixed_frame' : 'camera_link'}
        ]
    )

    realsense = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(realsense_launch_path),
        launch_arguments={
            'enable_color' : 'true',
            'enable_depth' : 'true',
            'align_depth.enable' : 'true', 
            'pointcloud.enable' : 'false',
            'enable_sync' : 'false',
            'unite_imu_method' : '2',
            'enable_gyro' : 'true',
            'enable_accel' : 'true',
            'color_fps' : '60',
            'depth_fps' : '60', 
            'gyro_fps' : '200',
            'accel_fps' : '63',
            'publish_tf' : 'true',
	    'tf_prefix' : 'rs_'
        }.items()
    )

    return LaunchDescription([
        robot_state_publisher,
        imu_filter,
        realsense
    ])
