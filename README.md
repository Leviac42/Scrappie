# Scrappie Robot - ROS2 Humble Stack

A ROS2-based autonomous mobile robot stack for the Scrappie robot, featuring dual RealSense cameras, SLAM, navigation, and person following capabilities.

## Hardware

- **Computer**: NVIDIA Jetson Orin Nano Super (Development on PC supported)
- **Sensors**: 2x Intel RealSense D435i (Front & Rear)
- **Motors**: 2x 24V 250W with MDDS30 motor driver
- **Chassis**: Jazzy Elite ES power wheelchair base
- **Battery**: 24V 50Ah SLA

## Software Architecture

### ROS2 Packages

1. **scrappie_description** - Robot URDF model with dual cameras
2. **scrappie_base** - Motor control interface for MDDS30 driver
3. **scrappie_sensors** - Dual RealSense camera drivers with depth-to-laserscan
4. **scrappie_nav** - Navigation stack (Nav2 + SLAM Toolbox)
5. **scrappie_bringup** - Main launch files

### Features

- ✅ Dual RealSense D435i cameras (360° coverage)
- ✅ Depth-to-laserscan conversion for both cameras
- ✅ SLAM mapping with SLAM Toolbox
- ✅ Autonomous navigation with Nav2
- ✅ Obstacle avoidance using merged scan data
- ✅ Jetson Orin Nano optimized deployment
- ✅ GPIO UART support for Jetson
- ✅ Docker containerized deployment
- 🚧 Person following (planned)
- 🚧 Visual odometry fusion (planned)

## Deployment Options

This project supports **two deployment targets**:

### 1. Development (x86 PC)
- For development and testing
- Uses USB-Serial adapter for MDDS30
- Standard ROS2 Docker images
- See: [Quick Start](#quick-start) below

### 2. Production (Jetson Orin Nano)
- Optimized for NVIDIA Jetson Orin Nano Super
- Uses GPIO UART (pins 8, 10)
- NVIDIA L4T base with CUDA/TensorRT
- Hardware-accelerated vision processing
- **See: [JETSON_DEPLOYMENT.md](JETSON_DEPLOYMENT.md)**

**Comparison Guide:** [DEV_VS_JETSON.md](DEV_VS_JETSON.md)

## Quick Start

### 1. Build Docker Image

```bash
cd /mnt/c/coding/Scrappie
docker-compose build
```

### 2. Start Development Container

```bash
docker-compose up -d
docker exec -it scrappie_core bash
```

### 3. Build Workspace

Inside the container:

```bash
cd /ws
colcon build --symlink-install
source install/setup.bash
```

### 4. Launch Robot Stack

**Full bringup with SLAM (mapping mode):**
```bash
ros2 launch scrappie_bringup scrappie_bringup.launch.py slam:=true
```

**Bringup with existing map (navigation mode):**
```bash
ros2 launch scrappie_bringup scrappie_bringup.launch.py slam:=false map:=/path/to/map.yaml
```

## Individual Component Testing

### Test Robot Description (Visualization)
```bash
ros2 launch scrappie_description display.launch.py
```

### Test Base Controller Only
```bash
ros2 launch scrappie_base base_controller.launch.py
```

### Test Dual Cameras
```bash
ros2 launch scrappie_sensors dual_realsense.launch.py
```

Check camera topics:
```bash
# Front camera
ros2 topic echo /camera_front/depth/image_raw
ros2 topic echo /camera_front/scan

# Rear camera
ros2 topic echo /camera_rear/depth/image_raw
ros2 topic echo /camera_rear/scan
```

### Test Navigation Stack
```bash
ros2 launch scrappie_nav navigation.launch.py slam:=true
```

## Configuration

### Base Controller Parameters
Edit `src/scrappie_base/config/base_controller.yaml`:
- `serial_port`: Serial port for MDDS30 (default: `/dev/ttyUSB0`)
- `wheel_separation`: Distance between wheels (0.50m)
- `max_linear_speed`: Maximum forward speed (1.0 m/s)
- `max_angular_speed`: Maximum rotation speed (2.0 rad/s)

### Navigation Parameters
Edit `src/scrappie_nav/config/nav2_params.yaml`:
- Costmap settings (local/global)
- DWB controller parameters
- Planner configuration

### Camera Configuration
Edit `src/scrappie_sensors/launch/dual_realsense.launch.py`:
- Update `serial_no` parameters if you have specific camera serials
- Adjust resolution: `depth_module.profile`
- Tune scan parameters in depthimage_to_laserscan nodes

## Hardware Setup

### USB Connections
1. **Front RealSense D435i** → USB 3.0
2. **Rear RealSense D435i** → USB 3.0
3. **MDDS30 Motor Driver** → USB-to-Serial adapter (`/dev/ttyUSB0`)

### MDDS30 Motor Driver
- **Baud Rate**: 9600
- **Mode**: Serial Packet Mode
- **Address**: 0x80 (default)
- Refer to `Hardware/MDDS30 User's Manual.pdf` for wiring

### Power
- Main battery: 24V 50Ah SLA
- Ensure Jetson is powered separately or through appropriate voltage regulator
- Motor driver powered directly from 24V battery

## Development Tips

### Building Individual Packages
```bash
colcon build --packages-select scrappie_base
```

### View TF Tree
```bash
ros2 run rqt_tf_tree rqt_tf_tree
```

### Monitor Topics
```bash
# Velocity commands
ros2 topic echo /cmd_vel

# Odometry
ros2 topic echo /odom

# Merged laser scan
ros2 topic echo /merged_scan
```

### Teleop Control
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Deployment to Jetson

### 1. Copy Workspace to Jetson
```bash
rsync -avz --exclude 'build' --exclude 'install' --exclude 'log' \
  /mnt/c/coding/Scrappie/ jetson@<jetson-ip>:~/scrappie/
```

### 2. Build on Jetson
SSH into Jetson:
```bash
cd ~/scrappie
docker-compose build
docker-compose up -d
docker exec -it scrappie_core bash
cd /ws
colcon build --symlink-install
```

### 3. Auto-start on Boot (Optional)
Create systemd service to launch robot stack on boot.

## Troubleshooting

### Motor Driver Not Responding
- Check serial port: `ls -l /dev/ttyUSB*`
- Verify permissions: `sudo chmod 666 /dev/ttyUSB0`
- Test communication: `sudo minicom -D /dev/ttyUSB0 -b 9600`

### RealSense Cameras Not Detected
- List USB devices: `lsusb | grep Intel`
- Check RealSense: `rs-enumerate-devices`
- Ensure proper USB 3.0 connections

### SLAM Not Working
- Verify merged scan: `ros2 topic hz /merged_scan`
- Check TF tree for missing transforms
- Ensure both cameras are publishing scans

### Build Errors
- Clean workspace: `rm -rf build install log`
- Update rosdep: `rosdep update && rosdep install --from-paths src --ignore-src -r -y`
- Rebuild: `colcon build --symlink-install`

## Next Steps

1. **Encoder Integration**: Add wheel encoders for better odometry
2. **Visual Odometry**: Use RealSense visual odometry instead of dead reckoning
3. **Person Following**: Implement person detection and tracking node
4. **Behavior Trees**: Create custom Nav2 behavior trees for person following
5. **Safety**: Add emergency stop and collision avoidance behaviors

## License

TODO: Add license

## Contributors

- User

## References

- [ROS2 Humble Documentation](https://docs.ros.org/en/humble/)
- [Nav2 Documentation](https://navigation.ros.org/)
- [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox)
- [RealSense ROS](https://github.com/IntelRealSense/realsense-ros)
