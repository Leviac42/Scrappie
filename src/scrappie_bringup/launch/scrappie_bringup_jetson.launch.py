#!/usr/bin/env python3
"""
Scrappie Robot Jetson-Optimized Bringup
Launches all components with Jetson-specific optimizations
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    
    # Get package directories
    description_pkg = get_package_share_directory('scrappie_description')
    base_pkg = get_package_share_directory('scrappie_base')
    sensors_pkg = get_package_share_directory('scrappie_sensors')
    nav_pkg = get_package_share_directory('scrappie_nav')
    
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    slam = LaunchConfiguration('slam', default='true')
    
    # Robot description
    robot_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(description_pkg, 'launch', 'display.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )
    
    # Base controller - Use Jetson-specific launch file
    base_controller = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(base_pkg, 'launch', 'base_controller_jetson.launch.py')
        )
    )
    
    # Sensors (dual RealSense cameras)
    # RealSense is optimized during Docker build for Jetson
    sensors = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sensors_pkg, 'launch', 'dual_realsense.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )
    
    # Navigation (SLAM + Nav2)
    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav_pkg, 'launch', 'navigation.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'slam': slam
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
        robot_description,
        base_controller,
        sensors,
        navigation
    ])
