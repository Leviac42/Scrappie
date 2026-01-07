#!/usr/bin/env python3
"""
Distributed Launch - Control Station (Surface Pro 9)

Runs on: Surface Pro 9 i5
Role: Visualization, monitoring, manual control
Network: 192.168.50.100 (WiFi)

Note: This machine doesn't run robot-critical nodes.
      Robot operates autonomously even if this disconnects.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    rviz_config = LaunchConfiguration('rviz_config', default='')
    
    # RViz2 for visualization
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config] if rviz_config else [],
        parameters=[{'use_sim_time': use_sim_time}]
    )
    
    # Optional: rqt for system monitoring
    # Uncomment if you want rqt to start automatically
    # rqt_node = Node(
    #     package='rqt_gui',
    #     executable='rqt_gui',
    #     name='rqt_gui',
    #     output='screen'
    # )
    
    # Optional: Teleop keyboard for manual control
    # Uncomment to enable keyboard control
    # teleop_node = Node(
    #     package='teleop_twist_keyboard',
    #     executable='teleop_twist_keyboard',
    #     name='teleop',
    #     output='screen',
    #     prefix='xterm -e'  # Run in separate terminal
    # )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time'
        ),
        DeclareLaunchArgument(
            'rviz_config',
            default_value='',
            description='Path to RViz config file'
        ),
        rviz_node,
        # rqt_node,    # Uncomment to auto-start
        # teleop_node, # Uncomment to auto-start
    ])
