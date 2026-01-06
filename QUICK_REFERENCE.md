# Scrappie Robot - Quick Reference Card

## Container Management

```bash
# Start container
docker-compose -f docker/docker-compose.yml up -d

# Stop container
docker-compose -f docker/docker-compose.yml down

# Enter container
docker exec -it scrappie_core bash

# View logs
docker logs -f scrappie_core

# Rebuild image
docker-compose -f docker/docker-compose.yml build
```

## Build Workspace

```bash
# Inside container
source /opt/ros/humble/setup.bash
cd /ws
colcon build --symlink-install
source install/setup.bash
```

## Launch Commands

### Full Robot Stack
```bash
# SLAM mode (mapping)
ros2 launch scrappie_bringup scrappie_bringup.launch.py slam:=true

# Navigation mode (with existing map)
ros2 launch scrappie_bringup scrappie_bringup.launch.py slam:=false map:=/ws/src/scrappie_nav/maps/my_map.yaml
```

### Individual Components
```bash
# Robot description (visualization)
ros2 launch scrappie_description display.launch.py

# Base controller only
ros2 launch scrappie_base base_controller.launch.py

# Cameras only
ros2 launch scrappie_sensors dual_realsense.launch.py

# Navigation only
ros2 launch scrappie_nav navigation.launch.py slam:=true
```

## Control & Monitoring

### Manual Control
```bash
# Teleop keyboard
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Send single velocity command
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.3}, angular: {z: 0.0}}"

# Stop robot
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

### Topic Monitoring
```bash
# List all topics
ros2 topic list

# Monitor merged scan
ros2 topic echo /merged_scan

# Monitor odometry
ros2 topic echo /odom

# Check topic frequency
ros2 topic hz /merged_scan
ros2 topic hz /camera_front/scan
ros2 topic hz /camera_rear/scan

# Show topic info
ros2 topic info /cmd_vel
```

### TF Debugging
```bash
# View TF tree
ros2 run rqt_tf_tree rqt_tf_tree

# Save TF frames to PDF
ros2 run tf2_tools view_frames

# Echo specific transform
ros2 run tf2_ros tf2_echo base_footprint camera_front_link
```

## Navigation Commands

### Set Initial Pose (via topic)
```bash
ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "..."
```

### Send Navigation Goal
```bash
ros2 topic pub /goal_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'map'}, pose: {position: {x: 2.0, y: 1.0, z: 0.0}}}"
```

### Save Map
```bash
# After SLAM mapping
ros2 run nav2_map_server map_saver_cli -f /ws/src/scrappie_nav/maps/my_map
```

### Load Map
```bash
# In navigation.launch.py
map:=/ws/src/scrappie_nav/maps/my_map.yaml
```

## Hardware Checks

### Cameras
```bash
# List RealSense devices
rs-enumerate-devices

# Check camera info
ros2 topic echo /camera_front/depth/camera_info
ros2 topic echo /camera_rear/depth/camera_info
```

### Serial Port
```bash
# List USB serial devices
ls -l /dev/ttyUSB*

# Check permissions
sudo chmod 666 /dev/ttyUSB0

# Test serial manually
sudo minicom -D /dev/ttyUSB0 -b 9600
```

### USB Devices
```bash
# List all USB devices
lsusb

# Find RealSense cameras
lsusb | grep Intel

# Find USB-Serial adapter
lsusb | grep -i serial
```

## Visualization

### RViz
```bash
# Launch with default config
ros2 run rviz2 rviz2

# Launch with saved config
ros2 run rviz2 rviz2 -d /ws/src/scrappie_description/rviz/scrappie.rviz
```

### rqt Tools
```bash
# Topic monitor
rqt_topic

# TF tree
rqt_tf_tree

# Robot steering
rqt_robot_steering

# Image view
rqt_image_view
```

## Debugging

### Node Info
```bash
# List running nodes
ros2 node list

# Node info
ros2 node info /base_controller

# Check parameters
ros2 param list /base_controller
ros2 param get /base_controller wheel_separation
```

### Service Calls
```bash
# List services
ros2 service list

# Clear costmap
ros2 service call /local_costmap/clear_entirely_local_costmap nav2_msgs/srv/ClearEntireCostmap
```

### Logging
```bash
# Set logging level
ros2 run rqt_logger_level rqt_logger_level

# View logs
ros2 topic echo /rosout
```

## Common Fixes

### Rebuild Single Package
```bash
colcon build --packages-select scrappie_base
```

### Clean Build
```bash
rm -rf build install log
colcon build --symlink-install
```

### Reset RealSense
```bash
# Unplug and replug USB
# Or reset via software
rs-reset-device
```

### Reset SLAM
```bash
# Clear existing map
ros2 service call /slam_toolbox/clear_changes slam_toolbox/srv/ClearQueue

# Save and reload
ros2 run nav2_map_server map_saver_cli -f backup
```

## Configuration File Locations

```
src/scrappie_base/config/base_controller.yaml    - Motor control params
src/scrappie_nav/config/nav2_params.yaml         - Navigation params
src/scrappie_nav/config/slam_toolbox.yaml        - SLAM params
src/scrappie_description/urdf/scrappie.urdf.xacro - Robot model
```

## Performance Monitoring

```bash
# CPU usage
top

# ROS2 CPU usage per node
ros2 topic hz /rosout
htop

# Memory usage
free -h

# Disk usage
df -h
```

## Network/Multi-Machine

```bash
# Check ROS_DOMAIN_ID
echo $ROS_DOMAIN_ID

# Set domain ID (0-101)
export ROS_DOMAIN_ID=42

# Check network traffic
ros2 topic bw /camera_front/depth/image_raw
```

## Emergency Stop

```bash
# Stop all motion
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}" --once

# Kill all ROS nodes
killall -9 ros2

# Stop container
docker stop scrappie_core
```

---

**Pro Tip**: Source the workspace in every new terminal:
```bash
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash
```

Or add to `.bashrc`:
```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "source /ws/install/setup.bash" >> ~/.bashrc
```
