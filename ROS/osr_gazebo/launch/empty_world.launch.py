import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription,
                            RegisterEventHandler)
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

import xacro

# Gazebo Classic isn't available after Humble; newer distros use Gazebo Harmonic.
SIM = 'classic' if os.environ.get('ROS_DISTRO') == 'humble' else 'harmonic'


def generate_launch_description():
    gui = LaunchConfiguration('gui')
    if SIM == 'classic':
        gazebo = [IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('gazebo_ros'), 'launch'), '/gazebo.launch.py']),
            launch_arguments={'gui': gui}.items(),
        )]
    else:
        gz_sim = os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        gazebo = [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(gz_sim),
                launch_arguments={'gz_args': '-r empty.sdf', 'on_exit_shutdown': 'true'}.items(),
                condition=IfCondition(gui),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(gz_sim),
                launch_arguments={'gz_args': '-s -r empty.sdf',
                                  'on_exit_shutdown': 'true'}.items(),
                condition=UnlessCondition(gui),
            ),
            # Sim time for the controllers, and the IMU under the same topic as
            # the Classic plugin.
            Node(
                package='ros_gz_bridge',
                executable='parameter_bridge',
                arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                           '/imu_plugin/out@sensor_msgs/msg/Imu[gz.msgs.IMU'],
                output='screen',
            ),
        ]

    osr_urdf_path = get_package_share_directory('osr_gazebo')
    xacro_file = os.path.join(osr_urdf_path, 'urdf', 'osr.urdf.xacro')

    doc = xacro.parse(open(xacro_file))
    xacro.process_doc(doc, mappings={'sim': SIM})
    params = {'robot_description': doc.toxml()}

    osr_params = os.path.join(
        get_package_share_directory('osr_bringup'),
        'config',
        'osr_params.yaml',
    )

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params],
    )

    rover_node = Node(
        package='osr_control',
        executable='rover',
        name='rover',
        output='screen',
        parameters=[
            osr_params,
            {'enable_odometry': False, 'publish_transform': False},
        ],
    )

    gazebo_adapter = Node(
        package='osr_gazebo',
        executable='gazebo_command_adapter.py',
        name='gazebo_command_adapter',
        output='screen',
    )

    if SIM == 'classic':
        spawn_entity = Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=['-topic', 'robot_description', '-entity', 'rover'],
            output='screen',
        )
    else:
        spawn_entity = Node(
            package='ros_gz_sim',
            executable='create',
            arguments=['-topic', 'robot_description', '-name', 'rover', '-z', '0.05'],
            output='screen',
        )

    load_joint_state_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'joint_state_broadcaster'],
        output='screen',
    )

    rover_wheel_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'wheel_controller'],
        output='screen',
    )

    servo_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'servo_controller'],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true',
                              description='Start the Gazebo GUI (false: server only)'),
        rover_node,
        gazebo_adapter,
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[
                    load_joint_state_controller,
                    rover_wheel_controller,
                    servo_controller,
                ],
            )
        ),
        *gazebo,
        node_robot_state_publisher,
        spawn_entity,
    ])
