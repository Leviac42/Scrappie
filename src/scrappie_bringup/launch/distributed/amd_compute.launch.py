#!/usr/bin/env python3
"""
Distributed Launch - AMD Side (Heavy Compute)

Runs on: AMD 6800u (GPD Win4)
Role: SLAM, Navigation, AI/ML processing
Network: 192.168.50.20
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    
    # Package directories
    nav_pkg = get_package_share_directory('scrappie_nav')
    utils_pkg = get_package_share_directory('scrappie_utils')
    
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    slam = LaunchConfiguration('slam', default='true')
    map_yaml_file = LaunchConfiguration('map', default='')
    
    # Scan merger - subscribes to camera scans from Jetson
    scan_merger_node = Node(
        package='scrappie_utils',
        executable='scan_merger.py',
        name='scan_merger',
        output='screen',
        parameters=[{
            'scan_topics': ['/camera_front/scan', '/camera_rear/scan'],
            'merged_scan_topic': '/merged_scan',
            'output_frame': 'base_footprint',
            'angle_min': -3.14159,
            'angle_max': 3.14159,
            'angle_increment': 0.0087,
            'range_min': 0.3,
            'range_max': 10.0,
            'use_sim_time': use_sim_time
        }]
    )
    
    # Navigation stack (SLAM + Nav2)
    # This subscribes to /merged_scan from scan_merger above
    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav_pkg, 'launch', 'navigation.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'slam': slam,
            'map': map_yaml_file
        }.items()
    )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time'
        ),
        DeclareLaunchArgument(
            'slam',
            default_value='true',
            description='Whether to run SLAM (true) or use existing map (false)'
        ),
        DeclareLaunchArgument(
            'map',
            default_value='',
            description='Full path to map yaml file (required if slam:=false)'
        ),
        scan_merger_node,
        navigation,
    ])
