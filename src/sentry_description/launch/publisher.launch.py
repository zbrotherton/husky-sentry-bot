import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

  # Set the path to this package.
  sentry_description_package  = FindPackageShare(package='sentry_description').find('sentry_description')

  # Set the path to the URDF file
  default_urdf_model_path = os.path.join(sentry_description_package, 'urdf/sentry.urdf.xacro')

  # Launch configuration variables specific to simulation
  joint_state_publisher_gui = LaunchConfiguration('joint_state_publisher_gui')
  joint_state_publisher = LaunchConfiguration('joint_state_publisher')
  urdf_model = LaunchConfiguration('urdf_model')
  use_robot_state_pub = LaunchConfiguration('use_robot_state_pub')
  use_sim = LaunchConfiguration('use_sim')
  use_mock_hardware = LaunchConfiguration('use_mock_hardware')

  # Declare the launch arguments  
  declare_urdf_model_path_cmd = DeclareLaunchArgument(
    name='urdf_model', 
    default_value=default_urdf_model_path, 
    description='Absolute path to robot urdf file')
  
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
   
  # Specify the actions
  
  # Publish the joint state values for the non-fixed joints in the URDF file.
  start_joint_state_publisher_cmd = Node(
    condition=IfCondition(joint_state_publisher),
    package='joint_state_publisher',
    executable='joint_state_publisher',
    name='joint_state_publisher')
  
  # A GUI to manipulate the joint state values
  start_joint_state_publisher_gui_node = Node(
    condition=IfCondition(joint_state_publisher_gui),
    package='joint_state_publisher_gui',
    executable='joint_state_publisher_gui',
    name='joint_state_publisher_gui')
  # Subscribe to the joint states of the robot, and publish the 3D pose of each link.
  start_robot_state_publisher_cmd = Node(
    condition=IfCondition(use_robot_state_pub),
    package='robot_state_publisher',
    executable='robot_state_publisher',
    parameters=[{'use_sim_time': use_sim, 
    'robot_description': Command(
      [
        'xacro ', urdf_model,
        ' use_sim:=', use_sim,
        ' use_mock_hardware:=', use_mock_hardware
       ]
      ),
    }],
    )
  
  # Create foxglove bridge
  start_foxglove_bridge_cmd = Node(
    package='foxglove_bridge',
    executable='foxglove_bridge'
  )

  # Create the launch description and populate
  launch_description = LaunchDescription()

  # Declare the launch options
  launch_description.add_action(declare_urdf_model_path_cmd)
  launch_description.add_action(declare_use_joint_state_publisher_gui_cmd)
  launch_description.add_action(declare_use_joint_state_publisher_cmd)
  launch_description.add_action(declare_use_robot_state_pub_cmd)  
  launch_description.add_action(declare_use_sim_cmd)
  launch_description.add_action(declare_use_mock_hardware_cmd)

  # Add any actions
  launch_description.add_action(start_foxglove_bridge_cmd)
  launch_description.add_action(start_joint_state_publisher_cmd)
  launch_description.add_action(start_joint_state_publisher_gui_node)
  launch_description.add_action(start_robot_state_publisher_cmd)

  return launch_description