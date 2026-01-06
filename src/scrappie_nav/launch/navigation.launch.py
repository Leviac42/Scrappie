#!/usr/bin/env python3
"""
SLAM and Navigation Launch File
Launches SLAM Toolbox for mapping or Nav2 for navigation
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    
    # Get package directories
    pkg_share = get_package_share_directory('scrappie_nav')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    
    # Config files
    nav2_params_file = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    slam_params_file = os.path.join(pkg_share, 'config', 'slam_toolbox.yaml')
    
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    slam = LaunchConfiguration('slam', default='true')
    map_yaml_file = LaunchConfiguration('map', default='')
    
    # Laser scan merger - merge front and rear scans
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
    
    # SLAM Toolbox
    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_params_file,
            {'use_sim_time': use_sim_time}
        ],
        condition=IfCondition(slam)
    )
    
    # Nav2 Bringup (only if not using SLAM)
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file': nav2_params_file,
            'map': map_yaml_file
        }.items(),
        condition=UnlessCondition(slam)
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
            description='Whether to run SLAM (true) or localization (false)'
        ),
        DeclareLaunchArgument(
            'map',
            default_value='',
            description='Full path to map yaml file to load (required if slam:=false)'
        ),
        scan_merger_node,
        slam_node,
        nav2_bringup
    ])
