import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

  # Set the path to this package.
  sentry_description_package = FindPackageShare(package='sentry_description').find('sentry_description')

  # Set the path to the RViz configuration settings
  default_rviz_config_path = os.path.join(sentry_description_package, 'rviz/rviz_settings.rviz')
  
  # Set the path to the URDF file
  default_urdf_model_path = os.path.join(sentry_description_package, 'urdf/sentry.urdf.xacro')

  # Set the path to the Publisher launch file
  publisher_launch_path = os.path.join(sentry_description_package, 'launch/publisher.launch.py')

  # Launch configuration variables specific to simulation
  joint_state_publisher_gui = LaunchConfiguration('joint_state_publisher_gui')
  joint_state_publisher = LaunchConfiguration('joint_state_publisher')
  urdf_model = LaunchConfiguration('urdf_model')
  rviz_config_file = LaunchConfiguration('rviz_config_file')
  use_robot_state_pub = LaunchConfiguration('use_robot_state_pub')
  use_rviz = LaunchConfiguration('use_rviz')
  use_sim = LaunchConfiguration('use_sim')
  use_mock_hardware = LaunchConfiguration('use_mock_hardware')

  # Declare the launch arguments  
  declare_urdf_model_path_cmd = DeclareLaunchArgument(
    name='urdf_model', 
    default_value=default_urdf_model_path, 
    description='Absolute path to robot urdf file')
    
  declare_rviz_config_file_cmd = DeclareLaunchArgument(
    name='rviz_config_file',
    default_value=default_rviz_config_path,
    description='Full path to the RVIZ config file to use')
    
  declare_use_joint_state_publisher_gui_cmd = DeclareLaunchArgument(
    name='joint_state_publisher_gui',
    default_value='False',
    description='Flag to enable joint_state_publisher_gui')
  
  declare_use_joint_state_publisher_cmd = DeclareLaunchArgument(
    name='joint_state_publisher',
    default_value='False',
    description='Flag to enable joint_state_publisher')
  
  declare_use_robot_state_pub_cmd = DeclareLaunchArgument(
    name='use_robot_state_pub',
    default_value='True',
    description='Whether to start the robot state publisher')

  declare_use_rviz_cmd = DeclareLaunchArgument(
    name='use_rviz',
    default_value='true',
    description='Whether to start RVIZ')
    
  declare_use_sim_cmd = DeclareLaunchArgument(
    'use_sim',
    default_value='false',
    description='Run in simulation'
  )
  
  declare_use_mock_hardware_cmd = DeclareLaunchArgument(
    'use_mock_hardware',
    default_value=use_sim,
    description='Use mock hardware'
  )
   
  # Specify the publisher action
  start_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(publisher_launch_path),
        launch_arguments={
          'urdf_model' : urdf_model,
          'joint_state_publisher_gui' : joint_state_publisher_gui,
          'joint_state_publisher' : joint_state_publisher,
          'use_robot_state_pub' : use_robot_state_pub,
          'use_sim' : use_sim,
          'use_mock_hardware' : use_mock_hardware
        }.items()
    )

  # Launch RViz
  start_rviz_cmd = Node(
    condition=IfCondition(use_rviz),
    package='rviz2',
    executable='rviz2',
    name='rviz2',
    output='screen',
    arguments=['-d', rviz_config_file])
  
  # Create the launch description and populate
  launch_description = LaunchDescription()

  # Declare the launch options
  launch_description.add_action(declare_urdf_model_path_cmd)
  launch_description.add_action(declare_rviz_config_file_cmd)
  launch_description.add_action(declare_use_joint_state_publisher_gui_cmd)
  launch_description.add_action(declare_use_joint_state_publisher_cmd)
  launch_description.add_action(declare_use_robot_state_pub_cmd)  
  launch_description.add_action(declare_use_rviz_cmd) 
  launch_description.add_action(declare_use_sim_cmd)
  launch_description.add_action(declare_use_mock_hardware_cmd)

  # Add any actions
  launch_description.add_action(start_publisher_cmd)
  launch_description.add_action(start_rviz_cmd)

  return launch_description