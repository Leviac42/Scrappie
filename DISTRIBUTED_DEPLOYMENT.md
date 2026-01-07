# Distributed Multi-Machine Deployment Guide

## Overview

This guide covers deploying Scrappie Robot as a distributed multi-machine system with compute workload split across three platforms.

### Architecture

```
Scrappie Robot (Internal Network: 192.168.50.0/24)
│
├── Jetson Orin Nano (192.168.50.10) - Sensors & Control
│   ├── Base controller (GPIO UART → MDDS30)
│   ├── 2x RealSense D435i cameras
│   ├── Depth-to-laserscan conversion
│   └── Robot TF tree publishing
│
├── AMD 6800u (192.168.50.20) - Heavy Compute
│   ├── Scan merger
│   ├── SLAM Toolbox (mapping)
│   ├── Nav2 navigation stack
│   └── Future: AI/ML models (person detection)
│
└── Surface Pro 9 (192.168.50.100) - Control Station
    ├── RViz visualization
    ├── rqt monitoring
    ├── Manual control (teleop)
    └── Development/debugging

Communication: ROS2 DDS over WiFi/Ethernet
```

---

## Network Setup

### 1. Configure Robot WiFi Network

**Option A: Dedicated Router on Robot**
- Install WiFi 6 router on robot
- Configure as AP: `SSID: Scrappie-Robot`, `Password: [your-password]`
- Network: `192.168.50.0/24`
- DHCP disabled (use static IPs)

**Option B: External WiFi (simpler for testing)**
- Connect all devices to existing WiFi
- Use static IPs in 192.168.50.x range

### 2. Assign Static IPs

**On Jetson (Ubuntu 22.04):**
```bash
# Edit netplan configuration
sudo nano /etc/netplan/01-netcfg.yaml

# Add:
network:
  version: 2
  wifis:
    wlan0:
      dhcp4: no
      addresses: [192.168.50.10/24]
      gateway4: 192.168.50.1
      nameservers:
        addresses: [8.8.8.8]
      access-points:
        "Scrappie-Robot":
          password: "your-password"

# Apply
sudo netplan apply
```

**On AMD (Windows/Linux):**
- Windows: Network settings → Static IP: `192.168.50.20`
- Linux: Same as Jetson, use `192.168.50.20`

**On Surface Pro (Windows):**
- Network settings → Static IP: `192.168.50.100`

### 3. Test Network Connectivity

```bash
# From any machine
ping 192.168.50.10  # Jetson
ping 192.168.50.20  # AMD
ping 192.168.50.100 # Surface

# Test bandwidth (install iperf3)
# On AMD:
iperf3 -s

# On Jetson:
iperf3 -c 192.168.50.20
# Target: >100 Mbps
```

---

## ROS2 Multi-Machine Configuration

### Environment Setup (All Machines)

Add to `~/.bashrc` or equivalent:

```bash
# ROS2 multi-machine settings
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_LOCALHOST_ONLY=0
export CYCLONEDDS_URI=file:///path/to/cyclonedds.xml

# Machine-specific hostname (for debugging)
export ROS_NAMESPACE=  # Leave empty for global namespace
```

### CycloneDDS Configuration

Copy `docker/cyclonedds.xml` to all machines.

Update if needed for your network:
```xml
<NetworkInterfaceAddress>192.168.50.0/24</NetworkInterfaceAddress>
```

### Verify Multi-Machine Discovery

On each machine:
```bash
# Terminal 1 (Machine A)
ros2 run demo_nodes_cpp talker

# Terminal 2 (Machine B)
ros2 run demo_nodes_cpp listener

# Should see messages being received across network
```

---

## Deployment Instructions

### On Jetson Orin Nano

```bash
# 1. Navigate to project
cd ~/Scrappie

# 2. Start Jetson container
docker-compose -f docker/docker-compose.jetson.yml up -d

# 3. Enter container
docker exec -it scrappie_jetson bash

# 4. Build workspace (first time)
cd /ws
colcon build --symlink-install
source install/setup.bash

# 5. Launch sensor/control stack
ros2 launch scrappie_bringup distributed/jetson_sensors.launch.py

# Keep this terminal open
```

### On AMD 6800u (GPD Win4)

```bash
# 1. Navigate to project
cd ~/Scrappie  # Or C:\coding\Scrappie in Windows

# 2. Start AMD container
docker-compose -f docker/docker-compose.amd.yml up -d

# 3. Enter container
docker exec -it scrappie_amd_compute bash

# 4. Build workspace (first time)
cd /ws
colcon build --symlink-install
source install/setup.bash

# 5. Launch compute stack
ros2 launch scrappie_bringup distributed/amd_compute.launch.py slam:=true

# Keep this terminal open
```

### On Surface Pro 9 (Optional - Control Station)

```bash
# Option A: Native ROS2 (if installed)
ros2 launch scrappie_bringup distributed/surface_viz.launch.py

# Option B: Via Docker (recommended)
docker-compose -f docker/docker-compose.yml up -d
docker exec -it scrappie_core bash
ros2 launch scrappie_bringup distributed/surface_viz.launch.py
```

---

## Startup Sequence

**Recommended order:**

1. **Jetson** (sensors first) - Wait for cameras to initialize (~30 sec)
2. **AMD** (compute second) - Will subscribe to sensor topics
3. **Surface** (visualization last) - Connects when ready

**Wait between launches:** 10-15 seconds for DDS discovery

---

## Verification

### Check Node Discovery

On any machine:
```bash
# List all nodes (should see nodes from all machines)
ros2 node list

# Expected nodes:
# /base_controller (Jetson)
# /robot_state_publisher (Jetson)
# /camera_front/realsense2_camera (Jetson)
# /camera_rear/realsense2_camera (Jetson)
# /scan_merger (AMD)
# /slam_toolbox (AMD)
# /bt_navigator (AMD)
# /controller_server (AMD)
# ... etc
```

### Check Topic Flow

```bash
# Camera data from Jetson
ros2 topic hz /camera_front/scan
# Target: 30 Hz

# Merged scan on AMD
ros2 topic hz /merged_scan  
# Target: 10-15 Hz

# Odometry from Jetson
ros2 topic hz /odom
# Target: 50 Hz
```

### Check Latency

```bash
# Measure end-to-end latency
ros2 topic delay /merged_scan
# Target: <100ms
```

### Monitor Resources

**On Jetson:**
```bash
jtop
# CPU: <80%
# RAM: <6GB
# Power: ~12W
```

**On AMD:**
```bash
htop
# CPU: <60%
# RAM: <20GB (of 64GB)
```

---

## Troubleshooting

### Nodes Can't See Each Other

**Problem:** `ros2 node list` only shows local nodes

**Solutions:**
1. Check `ROS_DOMAIN_ID` is same on all machines (42)
2. Check `ROS_LOCALHOST_ONLY=0` on all machines
3. Verify network connectivity: `ping 192.168.50.x`
4. Check firewall isn't blocking UDP ports 7400-7500
5. Enable CycloneDDS verbose logging for debugging

### High Network Latency

**Problem:** `ros2 topic delay` shows >200ms

**Solutions:**
1. Use 5GHz WiFi instead of 2.4GHz
2. Use ethernet for Jetson ↔ AMD if possible
3. Reduce camera resolution in launch files
4. Check network bandwidth: `iperf3`
5. Reduce SLAM update rate

### Topics Missing

**Problem:** Camera topics not visible on AMD

**Solutions:**
1. Wait longer for DDS discovery (30-60 seconds)
2. Check Jetson camera launch is running
3. Restart DDS: `unset ROS_DOMAIN_ID; export ROS_DOMAIN_ID=42`
4. Check topic: `ros2 topic list | grep camera`

### One Machine Crashes

**Problem:** AMD crashes, robot behavior?

**Expected Behavior:**
- Jetson continues running (base control, odometry)
- Robot can be manually stopped via /cmd_vel
- Navigation stops (AMD was running Nav2)

**Recovery:**
1. Restart AMD container
2. Re-launch AMD stack
3. Robot resumes navigation after ~30 seconds

---

## Performance Optimization

### WiFi Optimization

```bash
# On Linux machines, set WiFi power management off
sudo iwconfig wlan0 power off

# Prefer 5GHz band
sudo iwconfig wlan0 channel 36  # Or other 5GHz channel
```

### Buffer Sizes

Already configured in `cyclonedds.xml`:
```xml
<MinimumSocketReceiveBufferSize>10MB</MinimumSocketReceiveBufferSize>
<MinimumSocketSendBufferSize>10MB</MinimumSocketSendBufferSize>
```

### Quality of Service (QoS)

For critical topics, use RELIABLE:
```python
from rclpy.qos import QoSProfile, ReliabilityPolicy

qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    depth=10
)
```

---

## Power Consumption

**Expected Draw:**
- Jetson: 12W
- AMD 6800u: 20W (average), 28W (peak)
- Surface Pro: 12W
- Motors: 10-50W (variable)
- Cameras: 5W
- Accessories: 3W

**Total Average: ~47W**
**Battery Life: ~6 hours** (1200Wh / 200W peak)

### Power Saving Tips

1. **Reduce camera FPS** to 15 when not needed
2. **Use conservative power mode** on AMD when idle
3. **Suspend Surface** when not visualizing
4. **Enable motor sleep** when stationary

---

## Maintenance

### Daily
- Check network connectivity
- Monitor CPU/RAM usage
- Check ROS2 topic rates

### Weekly
- Update software on all platforms
- Check battery health
- Clean camera lenses
- Verify cooling fans working

### Monthly
- Backup maps
- Update Docker images
- Test failover scenarios

---

## Advanced: Adding More Machines

To add another machine (e.g., for additional sensors):

1. Assign static IP: `192.168.50.x`
2. Install ROS2 Humble
3. Set env variables (ROS_DOMAIN_ID=42, etc.)
4. Create launch file for new functionality
5. No changes needed to existing machines!

---

## Quick Reference

### Start All Systems
```bash
# Jetson
docker-compose -f docker/docker-compose.jetson.yml up -d && \
  docker exec scrappie_jetson bash -c \
  "source /ws/install/setup.bash && \
   ros2 launch scrappie_bringup distributed/jetson_sensors.launch.py"

# AMD
docker-compose -f docker/docker-compose.amd.yml up -d && \
  docker exec scrappie_amd_compute bash -c \
  "source /ws/install/setup.bash && \
   ros2 launch scrappie_bringup distributed/amd_compute.launch.py"
```

### Stop All Systems
```bash
# Jetson
docker-compose -f docker/docker-compose.jetson.yml down

# AMD
docker-compose -f docker/docker-compose.amd.yml down
```

### Emergency Stop
```bash
# From any machine
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{}" --once
```

---

**Distributed deployment complete! 🚀**
