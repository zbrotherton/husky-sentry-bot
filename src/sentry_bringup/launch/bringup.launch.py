from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim = LaunchConfiguration('use_sim')
    use_mock_hardware = LaunchConfiguration('use_mock_hardware')
    headless_gazebo = LaunchConfiguration('headless_gazebo')
    visualize_pens = LaunchConfiguration('visualize_pens')

    return LaunchDescription([
        # Launch Arguments
        DeclareLaunchArgument(
            'use_sim',
            default_value='false',
            description='Run in Simulation'
        ),
        DeclareLaunchArgument(
            'use_mock_hardware',
            default_value=use_sim,
            description='Use mock hardware'
        ),
        DeclareLaunchArgument(
            'headless_gazebo',
            default_value='false',
            description='Run Gazebo physics only'
        ),
        DeclareLaunchArgument(
            'visualize_pens',
            default_value='true',
            description='Visualize pens in Rviz'
        ),

        # Publishers & URDF
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [FindPackageShare('rai_description'),
                 '/launch',
                 '/publisher.launch.py']
            ),
            launch_arguments={
                'use_sim' : use_sim,
                'use_mock_hardware': use_mock_hardware
            }.items(),
            condition=UnlessCondition(use_sim)
        ),
        
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [FindPackageShare('rai_description'),
                 '/launch',
                 '/rviz.launch.py']
            ),
            launch_arguments={
                'use_sim' : use_sim,
                'use_mock_hardware': use_mock_hardware
            }.items(),
            condition=IfCondition(use_sim)
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [FindPackageShare('rai_gazebo'),
                 '/launch',
                 '/empty_world.launch.py'
                ]
            ),
            launch_arguments={
                'headless_gazebo': headless_gazebo
            }.items(),
            condition=IfCondition(use_sim),
        ),
        
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [FindPackageShare('rai_control'),
                 '/launch',
                 '/control.launch.py'
                ]
            ),
            launch_arguments={
                'use_sim': use_sim
            }.items()
        ),
        
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [FindPackageShare('rai_pen_visualizer'),
                  '/launch',
                  '/pen_visualizer.launch.py'
                ]
            ),
            launch_arguments={
                'use_sim_time' : use_sim
            }.items(),
            condition=IfCondition(visualize_pens),
        )
    ])