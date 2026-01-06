# Development vs Jetson Deployment - Quick Reference

## Configuration Differences

### Docker Images

| Setup | Base Image | Size | Build Time | Use Case |
|-------|------------|------|------------|----------|
| **Development (x86)** | `ros:humble-perception` | ~2GB | 50s | PC development/testing |
| **Jetson (ARM64)** | `dustynv/ros:humble-pytorch-l4t` | ~5GB | 25min | Production on Jetson |

### Serial Port Configuration

| Setup | Device | Location | Notes |
|-------|--------|----------|-------|
| **Development** | `/dev/ttyUSB0` | USB-Serial adapter | Requires adapter |
| **Jetson** | `/dev/ttyTHS0` | GPIO pins 8,10 | Hardware UART |

### Docker Compose Files

| File | Target | Key Features |
|------|--------|--------------|
| `docker-compose.yml` | Development (x86) | Basic setup, USB serial |
| `docker-compose.jetson.yml` | Jetson (ARM64) | NVIDIA runtime, GPIO, optimizations |

### Launch Files

| Component | Development | Jetson Optimized |
|-----------|-------------|------------------|
| **Bringup** | `scrappie_bringup.launch.py` | `scrappie_bringup_jetson.launch.py` |
| **Base Controller** | `base_controller.launch.py` | `base_controller_jetson.launch.py` |
| **Config** | `base_controller.yaml` | `base_controller_jetson.yaml` |

---

## Command Comparison

### Build Commands

**Development (x86):**
```bash
docker-compose -f docker/docker-compose.yml build
```

**Jetson (ARM64):**
```bash
docker-compose -f docker/docker-compose.jetson.yml build
```

### Start Commands

**Development:**
```bash
docker-compose -f docker/docker-compose.yml up -d
docker exec -it scrappie_core bash
```

**Jetson:**
```bash
docker-compose -f docker/docker-compose.jetson.yml up -d
docker exec -it scrappie_jetson bash
```

### Launch Commands

**Development:**
```bash
ros2 launch scrappie_bringup scrappie_bringup.launch.py
```

**Jetson:**
```bash
ros2 launch scrappie_bringup scrappie_bringup_jetson.launch.py
```

---

## Hardware Connections

### Development Setup
```
PC USB Ports:
  USB 3.0 → RealSense D435i (Front)
  USB 3.0 → RealSense D435i (Rear)
  USB 2.0 → USB-Serial adapter → MDDS30
```

### Jetson Setup
```
Jetson Orin Nano:
  USB 3.0 Port 1 → RealSense D435i (Front)
  USB 3.0 Port 2 → RealSense D435i (Rear)
  
  40-Pin GPIO Header:
    Pin 6  (GND) → MDDS30 GND
    Pin 8  (TXD) → MDDS30 RXD
    Pin 10 (RXD) → MDDS30 TXD
```

---

## Serial Port Testing

**Development (USB Serial):**
```bash
# List devices
ls -l /dev/ttyUSB*

# Test connection
sudo minicom -D /dev/ttyUSB0 -b 9600

# Python test
python3 -c "import serial; s=serial.Serial('/dev/ttyUSB0',9600)"
```

**Jetson (GPIO UART):**
```bash
# List devices
ls -l /dev/ttyTHS*

# Test connection
sudo minicom -D /dev/ttyTHS0 -b 9600

# Python test
python3 -c "import serial; s=serial.Serial('/dev/ttyTHS0',9600)"
```

---

## Performance Expectations

| Metric | Development (PC) | Jetson Orin Nano |
|--------|------------------|------------------|
| **CPU Cores** | Varies (4-16) | 6 cores |
| **GPU** | Optional | Integrated (1024 CUDA cores) |
| **RAM** | 8GB+ | 8GB |
| **SLAM Performance** | Fast | Optimized |
| **Camera FPS** | 30 FPS | 30 FPS (hardware accelerated) |
| **Power Draw** | 50-200W | 10-15W |
| **Thermal** | Active cooling | Passive + small fan |

---

## File Structure

```
/mnt/c/coding/Scrappie/
├── docker/
│   ├── Dockerfile                      # Development (x86)
│   ├── Dockerfile.jetson               # Production (Jetson)
│   ├── docker-compose.yml              # Development compose
│   ├── docker-compose.jetson.yml       # Jetson compose
│   ├── ros_entrypoint.sh               # Development entrypoint
│   └── ros_entrypoint_jetson.sh        # Jetson entrypoint
├── src/
│   ├── scrappie_base/
│   │   ├── config/
│   │   │   ├── base_controller.yaml            # Dev config (USB)
│   │   │   └── base_controller_jetson.yaml     # Jetson config (GPIO)
│   │   └── launch/
│   │       ├── base_controller.launch.py       # Dev launch
│   │       └── base_controller_jetson.launch.py # Jetson launch
│   └── scrappie_bringup/
│       └── launch/
│           ├── scrappie_bringup.launch.py      # Dev bringup
│           └── scrappie_bringup_jetson.launch.py # Jetson bringup
└── scripts/
    └── setup_jetson.sh                 # Jetson setup script
```

---

## Migration Workflow

### From Development to Jetson

1. **Develop on PC:**
   ```bash
   # Develop and test on x86
   docker-compose -f docker/docker-compose.yml up -d
   ```

2. **Transfer to Jetson:**
   ```bash
   # From development machine
   rsync -avz --exclude 'build' --exclude 'install' --exclude 'log' \
     /mnt/c/coding/Scrappie/ scrappie@jetson-ip:~/scrappie/
   ```

3. **Build on Jetson:**
   ```bash
   # SSH into Jetson
   ssh scrappie@jetson-ip
   cd ~/scrappie
   
   # Run setup (first time only)
   ./scripts/setup_jetson.sh
   sudo reboot
   
   # Build Docker image
   docker-compose -f docker/docker-compose.jetson.yml build
   
   # Start robot
   docker-compose -f docker/docker-compose.jetson.yml up -d
   ```

---

## Configuration Changes Needed

### Switching from Dev to Jetson

**Automatic (via launch files):**
- Launch files automatically load correct configs
- No code changes needed!

**Hardware-specific:**
- Connect to GPIO UART instead of USB
- Use jetson compose file
- Ensure cameras on USB 3.0

### Common Pitfalls

❌ **Using wrong compose file**
```bash
# Wrong (on Jetson)
docker-compose up  # Uses dev config!

# Correct
docker-compose -f docker/docker-compose.jetson.yml up
```

❌ **Serial port mismatch**
```bash
# Check which port your system uses
ls -l /dev/tty*

# Dev: /dev/ttyUSB0
# Jetson: /dev/ttyTHS0
```

❌ **Not sourcing workspace**
```bash
# Always source after build
source /opt/ros/humble/setup.bash
source install/setup.bash
```

---

## Testing Checklist

### Development Testing
- [ ] Docker builds successfully
- [ ] ROS2 packages compile
- [ ] Can visualize in RViz
- [ ] Serial port accessible (USB)
- [ ] Cameras detected
- [ ] Can send velocity commands

### Jetson Production Testing
- [ ] GPIO UART configured (`/dev/ttyTHS0`)
- [ ] Docker with NVIDIA runtime works
- [ ] RealSense cameras detected
- [ ] SLAM mapping works
- [ ] Navigation works
- [ ] Thermal < 80°C under load
- [ ] Auto-start on boot (optional)

---

## Quick Switch Commands

### Aliases for Easy Switching

Add to `~/.bashrc`:

```bash
# Development
alias dev-build='docker-compose -f docker/docker-compose.yml build'
alias dev-up='docker-compose -f docker/docker-compose.yml up -d'
alias dev-shell='docker exec -it scrappie_core bash'

# Jetson
alias jetson-build='docker-compose -f docker/docker-compose.jetson.yml build'
alias jetson-up='docker-compose -f docker/docker-compose.jetson.yml up -d'
alias jetson-shell='docker exec -it scrappie_jetson bash'

# Common
alias robot-logs='docker logs -f $(docker ps -q --filter name=scrappie)'
```

---

## Summary

| Aspect | Development | Jetson Production |
|--------|-------------|-------------------|
| **Platform** | x86 PC | ARM64 Jetson |
| **Docker Image** | Standard ROS2 | NVIDIA L4T optimized |
| **Serial** | USB adapter | GPIO UART |
| **Compose File** | `docker-compose.yml` | `docker-compose.jetson.yml` |
| **Launch File** | Standard | `*_jetson.launch.py` |
| **Setup** | Docker install | Run `setup_jetson.sh` |
| **Power** | High (50-200W) | Low (10-15W) |
| **Acceleration** | CPU-only | CUDA + TensorRT |
| **Use Case** | Development/Testing | Production/Deployment |

---

**Both setups use the same codebase - just different configs! 🎯**
