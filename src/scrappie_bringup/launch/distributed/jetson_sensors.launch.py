#!/usr/bin/env python3
"""
Distributed Launch - Jetson Side (Sensors + Base Control)

Runs on: Jetson Orin Nano
Role: Real-time sensor processing and motor control
Network: 192.168.50.10
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    
    # Package directories
    description_pkg = get_package_share_directory('scrappie_description')
    base_pkg = get_package_share_directory('scrappie_base')
    sensors_pkg = get_package_share_directory('scrappie_sensors')
    utils_pkg = get_package_share_directory('scrappie_utils')
    
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    # Robot description (TF tree publishing)
    robot_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(description_pkg, 'launch', 'display.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )
    
    # Base controller - GPIO UART on Jetson
    base_controller = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(base_pkg, 'launch', 'base_controller_jetson.launch.py')
        )
    )
    
    # Dual RealSense cameras
    sensors = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sensors_pkg, 'launch', 'dual_realsense.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )
    
    # NOTE: Scan merger is optional on Jetson side
    # Can run on AMD side to reduce Jetson load
    # Uncomment if you want Jetson to handle scan merging:
    # from launch_ros.actions import Node
    # scan_merger = Node(
    #     package='scrappie_utils',
    #     executable='scan_merger.py',
    #     name='scan_merger',
    #     output='screen',
    #     parameters=[{...}]
    # )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time'
        ),
        robot_description,
        base_controller,
        sensors,
        # scan_merger,  # Uncomment if running scan merger on Jetson
    ])
