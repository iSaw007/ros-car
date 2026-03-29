import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():

    # 1. Setup paths and package name
    package_name = 'my_bot' 
    pkg_path = get_package_share_directory(package_name)
    ros_gz_sim_path = get_package_share_directory('ros_gz_sim')

    # 2. Include Robot State Publisher (RSP)
    # This processes your URDF and publishes the /robot_description topic
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(pkg_path, 'launch', 'rsp.launch.py')]),
        launch_arguments={'use_sim_time': 'true'}.items()
    )

    # 3. Handle World Argument
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='empty.sdf',
        description='World to load (SDF file)'
    )
    world = LaunchConfiguration('world')

    # 4. Include Gazebo Sim Launch
    # Uses the 'ros_gz_sim' package which is the standard for Iron
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(ros_gz_sim_path, 'launch', 'gz_sim.launch.py')]),
        launch_arguments={
            'gz_args': [LaunchConfiguration('world'), ' -r -v4'],
            'on_exit_shutdown': 'true'
        }.items()
    )

    # 5. Spawn the Robot
    # This node takes the /robot_description and puts it in the Gazebo world
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description',
                   '-name', 'my_bot',
                   '-z', '0.1'],
        output='screen'
    )

    # 6. The Bridge (Crucial for Iron/Fortress)
    # This maps Gazebo topics to ROS 2 topics so you can control the car
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist[gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.PoseBundle'
        ],
        output='screen'
    )

    return LaunchDescription([
        rsp,
        world_arg,
        gazebo,
        spawn_entity,
        bridge
    ])