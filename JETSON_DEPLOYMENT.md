# Jetson Orin Nano Deployment Guide

## Complete deployment guide for Scrappie Robot on Jetson Orin Nano Super

---

## Hardware Requirements

### Jetson Orin Nano Super
- **Model**: NVIDIA Jetson Orin Nano Super Developer Kit
- **JetPack**: 6.0 or later (Ubuntu 22.04, L4T R36.3.0+)
  - Includes CUDA 12.2, cuDNN 8.9, TensorRT 8.6
- **Storage**: 64GB+ NVMe SSD or microSD (NVMe highly recommended)
- **Power**: 15W power supply (25W adapter recommended for peak loads)

### Connections
```
Jetson 40-Pin Header:
  Pin 6  (GND)     → MDDS30 GND
  Pin 8  (TXD)     → MDDS30 RXD  
  Pin 10 (RXD)     → MDDS30 TXD

USB 3.0 Ports:
  Port 1 → Intel RealSense D435i (Front Camera)
  Port 2 → Intel RealSense D435i (Rear Camera)

Power:
  24V Battery → MDDS30 Motor Driver
  Separate 5V/12V → Jetson Orin Nano
```

---

## Installation Steps

### 1. Initial Jetson Setup

Flash JetPack 6.x on your Jetson:
```bash
# Download JetPack 6.0 or later from NVIDIA
# https://developer.nvidia.com/embedded/jetpack

# JetPack 6.0 includes:
# - Ubuntu 22.04 LTS
# - L4T R36.3.0
# - CUDA 12.2
# - cuDNN 8.9
# - TensorRT 8.6

# Complete initial Ubuntu setup
# Username: scrappie (or your choice)
# Enable SSH for remote access
```

### 2. Run Setup Script

Transfer and run the automated setup script:

```bash
# Transfer project to Jetson
scp -r /mnt/c/coding/Scrappie scrappie@jetson-ip:~/

# SSH into Jetson
ssh scrappie@jetson-ip

# Run setup script
cd ~/scrappie
chmod +x scripts/setup_jetson.sh
./scripts/setup_jetson.sh
```

**The setup script will:**
- ✅ Enable GPIO UART (`/dev/ttyTHS0`)
- ✅ Install RealSense USB rules
- ✅ Install Docker with NVIDIA runtime
- ✅ Configure power mode to MAXN
- ✅ Create systemd service for auto-start
- ✅ Set up user permissions

**After setup:** Reboot the Jetson
```bash
sudo reboot
```

### 3. Verify Hardware

After reboot, verify all hardware is accessible:

```bash
# Check GPIO UART
ls -l /dev/ttyTHS0
# Expected: crw-rw-rw- 1 root dialout ... /dev/ttyTHS0

# Check RealSense cameras
lsusb | grep Intel
# Expected: Two Intel RealSense devices

# Check NVIDIA runtime
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.4.0-base-ubuntu20.04 nvidia-smi
# Expected: GPU info displayed

# Monitor Jetson
jtop
# Check: CPU, GPU, power mode (should be MAXN)
```

### 4. Build Docker Image

Build the Jetson-optimized Docker image:

```bash
cd ~/scrappie

# Build (this will take ~20-30 minutes on first build)
docker-compose -f docker/docker-compose.jetson.yml build

# This builds:
# - NVIDIA L4T base image with CUDA/TensorRT
# - RealSense SDK from source (Jetson-optimized)
# - ROS2 Humble with hardware acceleration
# - All Scrappie packages
```

**Build progress:**
- RealSense compilation: ~15 minutes
- ROS2 packages: ~5 minutes
- Total: ~25 minutes

### 5. Start Container

```bash
# Start in background
docker-compose -f docker/docker-compose.jetson.yml up -d

# Check status
docker ps
# Should show: scrappie_jetson container running

# View logs
docker logs -f scrappie_jetson
```

### 6. Build Workspace

Enter container and build ROS2 workspace:

```bash
# Enter container
docker exec -it scrappie_jetson bash

# Inside container - build workspace
cd /ws
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release

# Source workspace
source install/setup.bash

# Verify build
ros2 pkg list | grep scrappie
# Should show all 6 scrappie packages
```

---

## Running the Robot

### Launch Full Stack

```bash
# Inside container
ros2 launch scrappie_bringup scrappie_bringup_jetson.launch.py slam:=true
```

This launches:
- Robot state publisher with TF tree
- Base controller (GPIO UART → MDDS30)
- Dual RealSense cameras with depth-to-laserscan
- Scan merger (360° coverage)
- SLAM Toolbox for mapping
- Nav2 navigation stack

### Individual Component Testing

```bash
# Test GPIO UART / Motors
ros2 launch scrappie_base base_controller_jetson.launch.py

# Test cameras
ros2 launch scrappie_sensors dual_realsense.launch.py

# Send test command
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}}" --once
```

---

## GPIO UART Configuration Details

### Pin Mapping (40-pin Header)

```
Pin Layout:
    3.3V  [1]  [2]  5V
    I2C   [3]  [4]  5V
    I2C   [5]  [6]  GND ← MDDS30 GND
    GPIO  [7]  [8]  TXD ← MDDS30 RXD (receives from MDDS30)
    GND   [9]  [10] RXD ← MDDS30 TXD (sends to MDDS30)
```

### UART Configuration

The Jetson Orin Nano uses **UART1** (`/dev/ttyTHS0`) for GPIO serial:

**Hardware Specifications:**
- Baud Rate: 9600 (configurable)
- Data Bits: 8
- Stop Bits: 1
- Parity: None
- Flow Control: None

**Enable UART (if not auto-enabled):**
```bash
# Method 1: Using jetson-io
sudo /opt/nvidia/jetson-io/jetson-io.py
# Navigate: Configure Jetson 40-pin Header > UART1 > Enable

# Method 2: Manual (requires reboot)
sudo busybox devmem 0x0c302000 32 0x0000C400
```

**Test UART:**
```bash
# Check device exists
ls -l /dev/ttyTHS0

# Test with minicom
sudo apt-get install minicom
sudo minicom -D /dev/ttyTHS0 -b 9600

# Or with Python
python3 -c "import serial; s=serial.Serial('/dev/ttyTHS0',9600); print('UART OK')"
```

---

## Performance Optimization

### Power Modes

Set power mode based on your use case:

```bash
# View current mode
sudo nvpmodel -q

# MAXN (15W, 6 cores, max performance) - Default for robotics
sudo nvpmodel -m 0

# 10W mode (power-saving)
sudo nvpmodel -m 1

# Enable max clocks (recommended for robotics)
sudo jetson_clocks
```

### CPU Governor

```bash
# Set performance governor
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Verify
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

### Monitor Performance

```bash
# Real-time monitoring
jtop

# Key metrics:
# - CPU usage (should be <70% normally)
# - GPU usage (for vision processing)
# - RAM (should have 2GB+ free)
# - Thermal (keep under 80°C)
```

### ROS2 Performance Tuning

Already configured in `docker-compose.jetson.yml`:
- **RMW**: CycloneDDS (fastest on Jetson)
- **Shared Memory**: Enabled for efficient image transport
- **Threading**: Optimized for 6 cores

---

## Auto-Start on Boot

### Enable Systemd Service

```bash
# Enable auto-start
sudo systemctl enable scrappie-robot.service

# Start now
sudo systemctl start scrappie-robot.service

# Check status
sudo systemctl status scrappie-robot.service

# View logs
sudo journalctl -u scrappie-robot.service -f

# Disable auto-start
sudo systemctl disable scrappie-robot.service
```

The robot will now start automatically on boot!

---

## Network Configuration

### WiFi Setup

```bash
# Connect to WiFi
nmcli device wifi connect "SSID" password "PASSWORD"

# Set static IP (optional)
sudo nmcli con mod "SSID" ipv4.addresses 192.168.1.100/24
sudo nmcli con mod "SSID" ipv4.gateway 192.168.1.1
sudo nmcli con mod "SSID" ipv4.dns 8.8.8.8
sudo nmcli con mod "SSID" ipv4.method manual
sudo nmcli con up "SSID"
```

### Remote Development

```bash
# SSH into Jetson
ssh scrappie@jetson-ip

# Optional: VS Code Remote SSH
# Install "Remote - SSH" extension
# Connect to: scrappie@jetson-ip
```

---

## Troubleshooting

### GPIO UART Issues

**Problem:** `/dev/ttyTHS0` not found

**Solutions:**
```bash
# 1. Check if UART is enabled
ls -l /dev/ttyTHS*

# 2. Enable via jetson-io
sudo /opt/nvidia/jetson-io/jetson-io.py

# 3. Check device tree
dmesg | grep ttyTHS

# 4. Verify pin configuration
sudo cat /sys/kernel/debug/tegra_gpio
```

**Problem:** Permission denied on UART

**Solutions:**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Set permissions
sudo chmod 666 /dev/ttyTHS0

# Re-login or reboot
```

### RealSense Camera Issues

**Problem:** Cameras not detected

**Solutions:**
```bash
# Check USB connection
lsusb | grep Intel

# Check RealSense library
rs-enumerate-devices

# Rebuild RealSense in container
docker exec -it scrappie_jetson bash
cd /tmp/librealsense/build
make install

# Check USB power
# RealSense needs USB 3.0 with adequate power
# Use powered USB hub if needed
```

### Performance Issues

**Problem:** High CPU usage / thermal throttling

**Solutions:**
```bash
# Check thermal
jtop
# If CPU temp > 80°C, add cooling

# Reduce camera resolution
# Edit: src/scrappie_sensors/launch/dual_realsense.launch.py
# Change: depth_module.profile: '640x480x15'  # Lower FPS

# Disable features
# Turn off: enable_infra1, enable_infra2 if not needed
```

### Memory Issues

**Problem:** Out of memory errors

**Solutions:**
```bash
# Check memory
free -h

# Increase swap
sudo systemctl disable nvzramconfig
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Maintenance

### Update System

```bash
# Update Jetson packages
sudo apt update && sudo apt upgrade -y

# Rebuild Docker image (after updates)
cd ~/scrappie
docker-compose -f docker/docker-compose.jetson.yml build --no-cache
```

### Backup Configuration

```bash
# Backup maps
cp -r src/scrappie_nav/maps ~/backup/

# Backup custom configs
tar -czf ~/backup/scrappie_config.tar.gz src/*/config/
```

### Monitor Health

```bash
# Create alias for quick check
echo 'alias robot-status="jtop && docker ps && ros2 node list"' >> ~/.bashrc

# Check daily
robot-status
```

---

## Specifications

### Optimizations Applied

✅ **NVIDIA L4T Base Image**: Hardware-accelerated ROS2
✅ **CUDA/TensorRT**: GPU acceleration for vision
✅ **RealSense from Source**: Jetson-optimized builds
✅ **CycloneDDS**: Fastest RMW for Jetson
✅ **GPIO UART**: Direct hardware serial (no USB overhead)
✅ **Power Mode MAXN**: Maximum performance (15W)
✅ **Shared Memory**: Zero-copy image transport

### Expected Performance

| Component | CPU Usage | GPU Usage | Notes |
|-----------|-----------|-----------|-------|
| Robot State Publisher | 5% | 0% | TF broadcasting |
| Base Controller | 8% | 0% | Motor control |
| RealSense (2x) | 30% | 15% | @ 640x480x30 |
| SLAM Toolbox | 15% | 5% | Mapping |
| Nav2 Stack | 20% | 10% | Navigation |
| **Total** | **~70%** | **~30%** | Leaves headroom |

**Thermal**: 60-75°C under normal operation

---

## What's Next?

After successful deployment:

1. **Map Your Environment**
   ```bash
   ros2 launch scrappie_bringup scrappie_bringup_jetson.launch.py slam:=true
   # Drive around, then save map
   ros2 run nav2_map_server map_saver_cli -f ~/scrappie/maps/home
   ```

2. **Test Navigation**
   ```bash
   ros2 launch scrappie_bringup scrappie_bringup_jetson.launch.py \
     slam:=false map:=~/scrappie/maps/home.yaml
   ```

3. **Implement Person Following** (Next phase)

---

## Support

**Jetson Resources:**
- [NVIDIA Jetson Forums](https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/)
- [JetsonHacks](https://jetsonhacks.com/)
- [Jetson Zoo (Pre-built containers)](https://elinux.org/Jetson_Zoo)

**ROS2 on Jetson:**
- [ROS2 Humble Docs](https://docs.ros.org/en/humble/)
- [Nav2 Documentation](https://navigation.ros.org/)

**Hardware:**
- Jetson Orin Nano Pinout: [JetsonHacks GPIO](https://jetsonhacks.com/nvidia-jetson-orin-nano-gpio-header-pinout/)

---

**Ready to deploy! 🚀**
