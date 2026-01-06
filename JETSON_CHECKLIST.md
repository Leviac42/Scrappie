# Jetson Deployment Checklist

## Pre-Deployment

### Hardware Preparation
- [ ] Jetson Orin Nano Super with JetPack 5.1.2+ installed
- [ ] 64GB+ NVMe SSD or microSD card
- [ ] 15W power supply for Jetson
- [ ] 24V 50Ah battery for motors
- [ ] 2x Intel RealSense D435i cameras
- [ ] MDDS30 motor driver
- [ ] Wires for GPIO UART connection (3 wires minimum)
- [ ] Heat sink/fan for Jetson (optional but recommended)

### Software Preparation
- [ ] Project transferred to Jetson (`~/scrappie`)
- [ ] SSH access configured
- [ ] Network/WiFi configured
- [ ] Static IP set (optional but recommended)

---

## Initial Setup (One-Time)

### Run Automated Setup
- [ ] `cd ~/scrappie`
- [ ] `chmod +x scripts/setup_jetson.sh`
- [ ] `./scripts/setup_jetson.sh`
- [ ] Review output for any errors
- [ ] Reboot Jetson: `sudo reboot`

### Verify Setup
After reboot:
- [ ] GPIO UART exists: `ls -l /dev/ttyTHS0`
- [ ] User in dialout group: `groups | grep dialout`
- [ ] Docker installed: `docker --version`
- [ ] NVIDIA runtime: `docker info | grep nvidia`
- [ ] jetson-stats: `jtop` (press 'q' to quit)

---

## Hardware Connection

### GPIO UART Wiring
- [ ] Jetson Pin 6 (GND) → MDDS30 GND
- [ ] Jetson Pin 8 (TXD) → MDDS30 RXD
- [ ] Jetson Pin 10 (RXD) → MDDS30 TXD
- [ ] Verify connections with multimeter (optional)
- [ ] Label wires for future reference

### USB Cameras
- [ ] Front RealSense D435i → USB 3.0 port
- [ ] Rear RealSense D435i → USB 3.0 port
- [ ] Verify detection: `lsusb | grep Intel`
- [ ] Test RealSense: `rs-enumerate-devices`

### Power
- [ ] 24V battery → MDDS30 power input
- [ ] Jetson powered separately (5V/12V)
- [ ] **DO NOT** connect 24V to Jetson
- [ ] Check polarity before powering on

---

## Docker Build

### Build Jetson Image
- [ ] `cd ~/scrappie`
- [ ] `docker-compose -f docker/docker-compose.jetson.yml build`
- [ ] Wait ~25 minutes for first build
- [ ] Check for build errors
- [ ] Verify image: `docker images | grep scrappie`

---

## Container Start

### Launch Container
- [ ] `docker-compose -f docker/docker-compose.jetson.yml up -d`
- [ ] Check status: `docker ps`
- [ ] Container name: `scrappie_jetson` should be running
- [ ] Check logs: `docker logs scrappie_jetson`

### Enter Container
- [ ] `docker exec -it scrappie_jetson bash`
- [ ] Verify environment: `echo $ROS_DISTRO` (should show "humble")
- [ ] Check CUDA: `nvidia-smi`

---

## Workspace Build

### Build ROS2 Packages
Inside container:
- [ ] `cd /ws`
- [ ] `source /opt/ros/humble/setup.bash`
- [ ] `colcon build --symlink-install`
- [ ] Check for build errors
- [ ] `source install/setup.bash`
- [ ] Verify packages: `ros2 pkg list | grep scrappie`

Expected packages:
- scrappie_base
- scrappie_bringup
- scrappie_description
- scrappie_nav
- scrappie_sensors
- scrappie_utils

---

## Component Testing

### Test 1: Robot Description
- [ ] `ros2 launch scrappie_description display.launch.py`
- [ ] Verify TF tree: `ros2 run rqt_tf_tree rqt_tf_tree`
- [ ] Check for missing transforms
- [ ] Kill with Ctrl+C

### Test 2: GPIO UART / Base Controller
- [ ] `ros2 launch scrappie_base base_controller_jetson.launch.py`
- [ ] Check for serial connection messages
- [ ] Send test command: `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1}}" --once`
- [ ] **CAUTION**: Motor will move! Ensure robot is elevated or safe
- [ ] Stop: `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{}" --once`
- [ ] Check odometry: `ros2 topic echo /odom`
- [ ] Kill with Ctrl+C

### Test 3: RealSense Cameras
- [ ] `ros2 launch scrappie_sensors dual_realsense.launch.py`
- [ ] Check topics: `ros2 topic list | grep camera`
- [ ] Front scan: `ros2 topic hz /camera_front/scan`
- [ ] Rear scan: `ros2 topic hz /camera_rear/scan`
- [ ] View image: `ros2 run rqt_image_view rqt_image_view`
- [ ] Kill with Ctrl+C

### Test 4: Full System
- [ ] `ros2 launch scrappie_bringup scrappie_bringup_jetson.launch.py slam:=true`
- [ ] Wait for all nodes to start (~30 seconds)
- [ ] Check nodes: `ros2 node list`
- [ ] Check merged scan: `ros2 topic hz /merged_scan`
- [ ] Monitor with jtop in another terminal

Expected nodes:
- /base_controller
- /robot_state_publisher
- /camera_front/realsense2_camera
- /camera_rear/realsense2_camera
- /scan_merger
- /slam_toolbox
- /bt_navigator
- /controller_server
- ...and others

---

## Performance Verification

### Check System Load
While full system running:
- [ ] Open new terminal: `ssh jetson-ip`
- [ ] Run: `jtop`
- [ ] CPU usage: Should be 60-80%
- [ ] GPU usage: Should be 20-40%
- [ ] RAM: Should have 2GB+ free
- [ ] Temperature: Should be <80°C
- [ ] Power: Should be 10-15W

### Check ROS2 Performance
- [ ] Scan rate: `ros2 topic hz /merged_scan` (should be >10 Hz)
- [ ] Odom rate: `ros2 topic hz /odom` (should be ~50 Hz)
- [ ] TF rate: No warnings about TF delays

---

## Testing Robot Operation

### Teleop Control
- [ ] Install teleop: `apt-get update && apt-get install ros-humble-teleop-twist-keyboard`
- [ ] Run: `ros2 run teleop_twist_keyboard teleop_twist_keyboard`
- [ ] Test forward/backward (i/k keys)
- [ ] Test rotation (j/l keys)
- [ ] Test stop (k key)
- [ ] **Monitor for obstacles!**

### SLAM Mapping
- [ ] Full system running with slam:=true
- [ ] Drive robot around slowly
- [ ] Visualize in RViz (if GUI available)
- [ ] Save map: `ros2 run nav2_map_server map_saver_cli -f ~/maps/test`
- [ ] Check map files created

---

## Auto-Start Configuration (Optional)

### Enable Systemd Service
- [ ] `sudo systemctl enable scrappie-robot.service`
- [ ] `sudo systemctl start scrappie-robot.service`
- [ ] Check status: `sudo systemctl status scrappie-robot.service`
- [ ] Test reboot: `sudo reboot`
- [ ] After reboot, check: `docker ps` (should see scrappie_jetson)

### Disable Auto-Start (if needed)
- [ ] `sudo systemctl disable scrappie-robot.service`
- [ ] `sudo systemctl stop scrappie-robot.service`

---

## Troubleshooting

### If GPIO UART fails:
- [ ] Check: `ls -l /dev/ttyTHS0`
- [ ] Enable manually: `sudo /opt/nvidia/jetson-io/jetson-io.py`
- [ ] Reboot after enabling
- [ ] Check wiring with multimeter

### If RealSense fails:
- [ ] Check USB: `lsusb | grep Intel`
- [ ] Try different USB port
- [ ] Check power supply (USB 3.0 needs power)
- [ ] Reinstall rules: `sudo udevadm control --reload-rules`

### If Docker fails:
- [ ] Check NVIDIA runtime: `docker info | grep nvidia`
- [ ] Reinstall: See `scripts/setup_jetson.sh` Docker section
- [ ] Check logs: `docker logs scrappie_jetson`

### If build fails:
- [ ] Clean: `rm -rf build install log`
- [ ] Re-source: `source /opt/ros/humble/setup.bash`
- [ ] Rebuild: `colcon build --symlink-install`

### If performance is poor:
- [ ] Check power mode: `sudo nvpmodel -q` (should be mode 0)
- [ ] Enable clocks: `sudo jetson_clocks`
- [ ] Check thermal: `jtop` (if >80°C, add cooling)
- [ ] Reduce camera resolution in launch file

---

## Maintenance Checklist

### Weekly
- [ ] Check system health with `jtop`
- [ ] Review Docker logs: `docker logs scrappie_jetson`
- [ ] Check ROS2 nodes: `ros2 node list`

### Monthly
- [ ] Update Jetson: `sudo apt update && sudo apt upgrade`
- [ ] Check GPIO connections (look for loose wires)
- [ ] Clean camera lenses
- [ ] Verify battery voltage (24V battery)

### Before Operation
- [ ] Battery charged
- [ ] No loose connections
- [ ] Clear operating area
- [ ] Emergency stop accessible
- [ ] Check system status with `jtop`

---

## Production Deployment Complete! ✅

When all items are checked:
- [ ] Full system tested and working
- [ ] Performance verified
- [ ] Auto-start configured (optional)
- [ ] Documentation reviewed
- [ ] Ready for autonomous operation

**Next Phase**: Implement person following and advanced behaviors!

---

## Quick Reference

**Start Robot:**
```bash
docker-compose -f docker/docker-compose.jetson.yml up -d
docker exec -it scrappie_jetson bash
ros2 launch scrappie_bringup scrappie_bringup_jetson.launch.py
```

**Stop Robot:**
```bash
# Inside container: Ctrl+C
# Outside: docker stop scrappie_jetson
```

**Monitor:**
```bash
jtop                                    # System stats
docker logs -f scrappie_jetson          # Container logs
ros2 node list                          # ROS2 nodes
ros2 topic list                         # Active topics
```

**Emergency Stop:**
```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{}" --once
# Or: Ctrl+C in terminal running robot
# Or: docker stop scrappie_jetson
```

---

**Status: Production Ready! 🚀**
