#!/usr/bin/env python3
"""
Scrappie Base Controller Node
Interfaces with MDDS30 motor driver via serial for differential drive control.
Subscribes to cmd_vel and publishes odometry.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Header
import serial
import struct
import math
from tf2_ros import TransformBroadcaster


class MDDS30Driver:
    """
    Driver for MDDS30 motor controller using Serial Packet mode.
    Based on MDDS30 User Manual - Serial Packet Mode protocol.
    """
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, address=0x80):
        self.ser = serial.Serial(port, baudrate, timeout=0.1)
        self.address = address
        
    def _calculate_checksum(self, data):
        """Calculate checksum for MDDS30 packet"""
        return sum(data) & 0xFF
        
    def send_command(self, left_speed, right_speed):
        """
        Send speed command to MDDS30
        left_speed, right_speed: -127 to 127 (signed 8-bit)
        """
        # Convert to signed bytes
        left_byte = int(max(-127, min(127, left_speed))) & 0xFF
        right_byte = int(max(-127, min(127, right_speed))) & 0xFF
        
        # Build packet: [Address, Left Motor, Right Motor, Checksum]
        packet = [self.address, left_byte, right_byte]
        checksum = self._calculate_checksum(packet)
        packet.append(checksum)
        
        self.ser.write(bytearray(packet))
        
    def stop(self):
        """Emergency stop"""
        self.send_command(0, 0)
        
    def close(self):
        """Close serial connection"""
        self.stop()
        self.ser.close()


class BaseControllerNode(Node):
    """
    ROS2 Node for Scrappie base control
    - Subscribes to /cmd_vel (Twist)
    - Controls MDDS30 motor driver
    - Publishes /odom (Odometry) based on dead reckoning
    """
    
    def __init__(self):
        super().__init__('base_controller')
        
        # Declare parameters
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 9600)
        self.declare_parameter('wheel_separation', 0.50)  # meters (from URDF)
        self.declare_parameter('wheel_radius', 0.1143)     # meters (from URDF)
        self.declare_parameter('max_linear_speed', 1.0)    # m/s
        self.declare_parameter('max_angular_speed', 2.0)   # rad/s
        self.declare_parameter('publish_odom_tf', True)
        
        # Get parameters
        serial_port = self.get_parameter('serial_port').value
        baudrate = self.get_parameter('baudrate').value
        self.wheel_separation = self.get_parameter('wheel_separation').value
        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.max_linear_speed = self.get_parameter('max_linear_speed').value
        self.max_angular_speed = self.get_parameter('max_angular_speed').value
        self.publish_tf = self.get_parameter('publish_odom_tf').value
        
        # Initialize motor driver
        try:
            self.driver = MDDS30Driver(port=serial_port, baudrate=baudrate)
            self.get_logger().info(f'Connected to MDDS30 on {serial_port}')
        except Exception as e:
            self.get_logger().error(f'Failed to connect to MDDS30: {e}')
            self.driver = None
            
        # Odometry state
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_time = self.get_clock().now()
        self.last_left_speed = 0.0
        self.last_right_speed = 0.0
        
        # Publishers
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        
        # TF Broadcaster
        if self.publish_tf:
            self.tf_broadcaster = TransformBroadcaster(self)
        
        # Subscribers
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        # Timer for odometry updates (50Hz)
        self.odom_timer = self.create_timer(0.02, self.update_odometry)
        
        self.get_logger().info('Base controller node started')
        
    def cmd_vel_callback(self, msg):
        """
        Convert cmd_vel (linear.x, angular.z) to differential drive speeds
        """
        if self.driver is None:
            return
            
        linear_vel = msg.linear.x
        angular_vel = msg.angular.z
        
        # Clamp velocities
        linear_vel = max(-self.max_linear_speed, min(self.max_linear_speed, linear_vel))
        angular_vel = max(-self.max_angular_speed, min(self.max_angular_speed, angular_vel))
        
        # Differential drive kinematics
        # v_left = v - (w * L) / 2
        # v_right = v + (w * L) / 2
        left_vel = linear_vel - (angular_vel * self.wheel_separation) / 2.0
        right_vel = linear_vel + (angular_vel * self.wheel_separation) / 2.0
        
        # Convert m/s to motor commands (-127 to 127)
        # Assuming max motor command corresponds to max_linear_speed
        left_cmd = int((left_vel / self.max_linear_speed) * 127)
        right_cmd = int((right_vel / self.max_linear_speed) * 127)
        
        # Store for odometry
        self.last_left_speed = left_vel
        self.last_right_speed = right_vel
        
        # Send to motor driver
        self.driver.send_command(left_cmd, right_cmd)
        
    def update_odometry(self):
        """
        Update odometry based on commanded velocities (dead reckoning)
        In a real system, this would use encoder feedback
        """
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time
        
        # Dead reckoning using last commanded speeds
        # This is a simplification - real system should use encoder feedback
        left_vel = self.last_left_speed
        right_vel = self.last_right_speed
        
        # Calculate velocity and angular velocity
        linear_vel = (left_vel + right_vel) / 2.0
        angular_vel = (right_vel - left_vel) / self.wheel_separation
        
        # Update pose
        delta_theta = angular_vel * dt
        delta_x = linear_vel * math.cos(self.theta + delta_theta / 2.0) * dt
        delta_y = linear_vel * math.sin(self.theta + delta_theta / 2.0) * dt
        
        self.x += delta_x
        self.y += delta_y
        self.theta += delta_theta
        
        # Normalize theta to [-pi, pi]
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
        
        # Publish odometry
        self.publish_odometry(current_time, linear_vel, angular_vel)
        
    def publish_odometry(self, current_time, linear_vel, angular_vel):
        """Publish odometry message and optionally TF"""
        
        # Create quaternion from yaw
        q = self.quaternion_from_euler(0, 0, self.theta)
        
        # Odometry message
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_footprint'
        
        # Position
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.x = q[0]
        odom.pose.pose.orientation.y = q[1]
        odom.pose.pose.orientation.z = q[2]
        odom.pose.pose.orientation.w = q[3]
        
        # Velocity
        odom.twist.twist.linear.x = linear_vel
        odom.twist.twist.linear.y = 0.0
        odom.twist.twist.angular.z = angular_vel
        
        self.odom_pub.publish(odom)
        
        # Publish TF
        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = current_time.to_msg()
            t.header.frame_id = 'odom'
            t.child_frame_id = 'base_footprint'
            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.translation.z = 0.0
            t.transform.rotation.x = q[0]
            t.transform.rotation.y = q[1]
            t.transform.rotation.z = q[2]
            t.transform.rotation.w = q[3]
            self.tf_broadcaster.sendTransform(t)
            
    def quaternion_from_euler(self, roll, pitch, yaw):
        """Convert Euler angles to quaternion"""
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        q = [0] * 4
        q[0] = sr * cp * cy - cr * sp * sy  # x
        q[1] = cr * sp * cy + sr * cp * sy  # y
        q[2] = cr * cp * sy - sr * sp * cy  # z
        q[3] = cr * cp * cy + sr * sp * sy  # w
        
        return q
        
    def destroy_node(self):
        """Cleanup on shutdown"""
        if self.driver:
            self.driver.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = BaseControllerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
