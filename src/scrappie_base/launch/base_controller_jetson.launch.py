#!/usr/bin/env python3
"""
Jetson-Optimized Base Controller Launch
Uses GPIO UART and optimized settings for Jetson Orin Nano
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    
    # Get package directory
    pkg_share = get_package_share_directory('scrappie_base')
    
    # Use Jetson-specific config
    config_file = os.path.join(pkg_share, 'config', 'base_controller_jetson.yaml')
    
    # Base controller node with Jetson optimizations
    base_controller_node = Node(
        package='scrappie_base',
        executable='base_controller.py',
        name='base_controller',
        output='screen',
        parameters=[config_file],
        # Set CPU affinity for better performance on Jetson
        # Run on performance cores (0-5 on Orin Nano)
        # prefix=['taskset -c 0-3'],  # Uncomment for CPU pinning
    )
    
    return LaunchDescription([
        base_controller_node
    ])
