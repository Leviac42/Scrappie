#!/usr/bin/env python3
"""
Scan Merger Node
Merges multiple LaserScan messages into a single merged scan.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import math


class ScanMerger(Node):
    """Merges LaserScan messages from multiple sources into a single scan"""
    
    def __init__(self):
        super().__init__('scan_merger')
        
        # Declare parameters
        self.declare_parameter('scan_topics', ['/camera_front/scan', '/camera_rear/scan'])
        self.declare_parameter('merged_scan_topic', '/merged_scan')
        self.declare_parameter('output_frame', 'base_footprint')
        self.declare_parameter('angle_min', -math.pi)
        self.declare_parameter('angle_max', math.pi)
        self.declare_parameter('angle_increment', 0.0087)  # ~0.5 degrees
        self.declare_parameter('range_min', 0.3)
        self.declare_parameter('range_max', 10.0)
        
        # Get parameters
        scan_topics = self.get_parameter('scan_topics').value
        merged_topic = self.get_parameter('merged_scan_topic').value
        self.output_frame = self.get_parameter('output_frame').value
        self.angle_min = self.get_parameter('angle_min').value
        self.angle_max = self.get_parameter('angle_max').value
        self.angle_increment = self.get_parameter('angle_increment').value
        self.range_min = self.get_parameter('range_min').value
        self.range_max = self.get_parameter('range_max').value
        
        # Calculate number of rays
        self.num_rays = int((self.angle_max - self.angle_min) / self.angle_increment) + 1
        
        # Storage for latest scans
        self.latest_scans = {}
        
        # Create subscribers for each scan topic
        self.subscribers = []
        for topic in scan_topics:
            sub = self.create_subscription(
                LaserScan,
                topic,
                lambda msg, t=topic: self.scan_callback(msg, t),
                10
            )
            self.subscribers.append(sub)
            self.latest_scans[topic] = None
            self.get_logger().info(f'Subscribing to {topic}')
        
        # Publisher for merged scan
        self.merged_pub = self.create_publisher(LaserScan, merged_topic, 10)
        
        # Timer to publish merged scans
        self.timer = self.create_timer(0.1, self.merge_and_publish)  # 10 Hz
        
        self.get_logger().info(f'Scan merger started, publishing to {merged_topic}')
        
    def scan_callback(self, msg, topic):
        """Store the latest scan from each topic"""
        self.latest_scans[topic] = msg
        
    def merge_and_publish(self):
        """Merge all available scans and publish"""
        
        # Check if we have at least one scan
        available_scans = [scan for scan in self.latest_scans.values() if scan is not None]
        if not available_scans:
            return
            
        # Initialize merged scan
        merged_scan = LaserScan()
        merged_scan.header.stamp = self.get_clock().now().to_msg()
        merged_scan.header.frame_id = self.output_frame
        merged_scan.angle_min = self.angle_min
        merged_scan.angle_max = self.angle_max
        merged_scan.angle_increment = self.angle_increment
        merged_scan.time_increment = 0.0
        merged_scan.scan_time = 0.1
        merged_scan.range_min = self.range_min
        merged_scan.range_max = self.range_max
        
        # Initialize ranges with max range
        merged_scan.ranges = [self.range_max] * self.num_rays
        merged_scan.intensities = [0.0] * self.num_rays
        
        # Merge scans by taking the minimum range at each angle
        for topic, scan in self.latest_scans.items():
            if scan is None:
                continue
                
            # For each ray in the source scan
            for i, range_val in enumerate(scan.ranges):
                # Skip invalid ranges
                if math.isnan(range_val) or math.isinf(range_val):
                    continue
                if range_val < scan.range_min or range_val > scan.range_max:
                    continue
                    
                # Calculate angle of this ray
                angle = scan.angle_min + i * scan.angle_increment
                
                # Map to merged scan index
                merged_index = int((angle - self.angle_min) / self.angle_increment)
                
                # Check if index is valid
                if 0 <= merged_index < self.num_rays:
                    # Take minimum range (closest obstacle)
                    if range_val < merged_scan.ranges[merged_index]:
                        merged_scan.ranges[merged_index] = range_val
                        if len(scan.intensities) > i:
                            merged_scan.intensities[merged_index] = scan.intensities[i]
        
        # Publish merged scan
        self.merged_pub.publish(merged_scan)


def main(args=None):
    rclpy.init(args=args)
    node = ScanMerger()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
