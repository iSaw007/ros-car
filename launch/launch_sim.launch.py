import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    package_name = 'ros-car'
    package_share = get_package_share_directory(package_name)
    rviz_config = os.path.join(
        package_share, 'config', 'view_bot.rviz'
    )
    default_world = os.path.join(
        package_share, 'worlds', 'empty.world'
    )

    # Publish the robot description and TF tree using simulation time.
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory(package_name), 'launch', 'rsp.launch.py'
        )]), 
        launch_arguments={
            'use_sim_time': 'true',
            'frame_prefix': 'ros_car/',
        }.items()
    )

    # Bridge Gazebo topics into ROS 2.
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
            '/world/default/model/ros_car/joint_state@sensor_msgs/msg/JointState[ignition.msgs.Model',
            '/model/ros_car/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/model/ros_car/odometry@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            '/model/ros_car/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V',
        ],
        parameters=[{'use_sim_time': True}],
        remappings=[
            ('/world/default/model/ros_car/joint_state', '/joint_states'),
            ('/model/ros_car/cmd_vel', '/cmd_vel'),
            ('/model/ros_car/odometry', '/odom'),
            ('/model/ros_car/tf', '/tf')
        ],
        output='screen'
    )
    
    world_arg = DeclareLaunchArgument(
        'world', default_value=default_world, description='World to load'
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')]),
        launch_arguments={'gz_args': ['-r -v4 ', LaunchConfiguration('world')]} .items()
    )

    spawn_entity = Node(
        package='ros_gz_sim', executable='create',
        arguments=['-topic', 'robot_description', '-name', 'ros_car', '-z', '0.5'],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    return LaunchDescription([
        rsp,
        world_arg,
        gazebo,
        bridge,
        TimerAction(period=5.0, actions=[spawn_entity]),
        rviz,
    ])
