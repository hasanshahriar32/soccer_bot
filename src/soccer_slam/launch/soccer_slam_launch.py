#!/usr/bin/python3
"""
====================================================================
Soccer Bot Real-Time SLAM & Mapping Master Launch Description
====================================================================
Launches:
  1. YDLidar ROS 2 Driver (/scan)
  2. Static TF Publishers (base_link -> laser_frame, odom -> base_link)
  3. SLAM Toolbox Online Async Node (/map, loop closure, graph SLAM)
  4. Real-Time Spatial Coordinate Tracker Node (/robot_map_pose)
  5. RViz2 Live Mapping GUI
====================================================================
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    slam_share = get_package_share_directory('soccer_slam')
    ydlidar_share = get_package_share_directory('ydlidar_ros2_driver')
    slam_toolbox_share = get_package_share_directory('slam_toolbox')

    slam_params_file = os.path.join(slam_share, 'config', 'mapper_params_online_async.yaml')
    ydlidar_params_file = os.path.join(ydlidar_share, 'params', 'ydlidar.yaml')
    rviz_config_file = os.path.join(slam_share, 'config', 'soccer_slam.rviz')

    # 1. LiDAR Hardware Driver Node
    ydlidar_node = Node(
        package='ydlidar_ros2_driver',
        executable='ydlidar_ros2_driver_node',
        name='ydlidar_ros2_driver_node',
        output='screen',
        emulate_tty=True,
        parameters=[ydlidar_params_file],
        namespace='/',
    )

    # 2. Static TF: base_link -> laser_frame
    tf_laser_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_pub_laser',
        arguments=['--x', '0', '--y', '0', '--z', '0.05', '--roll', '0', '--pitch', '0', '--yaw', '0', '--frame-id', 'base_link', '--child-frame-id', 'laser_frame'],
    )

    # 3. Static TF: odom -> base_link (baseline odometry identity frame for scan matcher)
    tf_odom_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_pub_odom',
        arguments=['--x', '0', '--y', '0', '--z', '0', '--roll', '0', '--pitch', '0', '--yaw', '0', '--frame-id', 'odom', '--child-frame-id', 'base_link'],
    )

    # 4. SLAM Toolbox (Online Asynchronous Mapping with Lifecycle Management)
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_toolbox_share, 'launch', 'online_async_launch.py')
        ),
        launch_arguments={
            'slam_params_file': slam_params_file,
            'use_sim_time': 'false',
        }.items(),
    )

    # 5. Real-Time Spatial Coordinate Tracker Node
    tracker_node = Node(
        package='soccer_slam',
        executable='coordinate_tracker',
        name='soccer_coordinate_tracker',
        output='screen',
    )

    # 6. RViz2 Live Mapping Visualization
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
    )

    return LaunchDescription([
        ydlidar_node,
        tf_laser_node,
        tf_odom_node,
        slam_launch,
        tracker_node,
        rviz_node,
    ])
