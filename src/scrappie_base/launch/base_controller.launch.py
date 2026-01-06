#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    
    # Get package directory
    pkg_share = get_package_share_directory('scrappie_base')
    config_file = os.path.join(pkg_share, 'config', 'base_controller.yaml')
    
    # Base controller node
    base_controller_node = Node(
        package='scrappie_base',
        executable='base_controller.py',
        name='base_controller',
        output='screen',
        parameters=[config_file]
    )
    
    return LaunchDescription([
        base_controller_node
    ])
