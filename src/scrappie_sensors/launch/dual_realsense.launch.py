#!/usr/bin/env python3
"""
Dual RealSense D435i Launch File
Launches front and rear cameras with depth-to-laserscan conversion
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace

def generate_launch_description():
    
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    # Front Camera (camera_front)
    front_camera = GroupAction([
        PushRosNamespace('camera_front'),
        
        Node(
            package='realsense2_camera',
            executable='realsense2_camera_node', 
            name='realsense2_camera',
            output='screen',
            parameters=[{
                'serial_no': '',  # Empty for first camera found, or specify serial
                'camera_name': 'camera_front',
                'depth_module.profile': '640x480x30',
                'rgb_camera.profile': '640x480x30',
                'enable_depth': True,
                'enable_color': True,
                'enable_infra1': True,
                'enable_infra2': True,
                'enable_sync': True,
                'align_depth.enable': True,
                'pointcloud.enable': True,
                'use_sim_time': use_sim_time
            }],
            remappings=[
                ('/camera_front/depth/image_rect_raw', '/camera_front/depth/image_raw')
            ]
        ),
        
        # Convert depth to laser scan for front camera
        Node(
            package='depthimage_to_laserscan',
            executable='depthimage_to_laserscan_node',
            name='depthimage_to_laserscan_front',
            output='screen',
            parameters=[{
                'scan_height': 10,
                'range_min': 0.3,
                'range_max': 10.0,
                'output_frame': 'camera_front_depth_optical_frame',
                'use_sim_time': use_sim_time
            }],
            remappings=[
                ('depth', '/camera_front/depth/image_raw'),
                ('depth_camera_info', '/camera_front/depth/camera_info'),
                ('scan', '/camera_front/scan')
            ]
        )
    ])
    
    # Rear Camera (camera_rear)
    rear_camera = GroupAction([
        PushRosNamespace('camera_rear'),
        
        Node(
            package='realsense2_camera',
            executable='realsense2_camera_node',
            name='realsense2_camera',
            output='screen',
            parameters=[{
                'serial_no': '',  # Specify different serial for 2nd camera if needed
                'camera_name': 'camera_rear',
                'depth_module.profile': '640x480x30',
                'rgb_camera.profile': '640x480x30',
                'enable_depth': True,
                'enable_color': True,
                'enable_infra1': True,
                'enable_infra2': True,
                'enable_sync': True,
                'align_depth.enable': True,
                'pointcloud.enable': True,
                'use_sim_time': use_sim_time
            }],
            remappings=[
                ('/camera_rear/depth/image_rect_raw', '/camera_rear/depth/image_raw')
            ]
        ),
        
        # Convert depth to laser scan for rear camera
        Node(
            package='depthimage_to_laserscan',
            executable='depthimage_to_laserscan_node',
            name='depthimage_to_laserscan_rear',
            output='screen',
            parameters=[{
                'scan_height': 10,
                'range_min': 0.3,
                'range_max': 10.0,
                'output_frame': 'camera_rear_depth_optical_frame',
                'use_sim_time': use_sim_time
            }],
            remappings=[
                ('depth', '/camera_rear/depth/image_raw'),
                ('depth_camera_info', '/camera_rear/depth/camera_info'),
                ('scan', '/camera_rear/scan')
            ]
        )
    ])
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time'
        ),
        front_camera,
        rear_camera
    ])
