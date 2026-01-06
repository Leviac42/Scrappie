# Windows + Podman Setup Guide

## Overview

This guide helps you run the Scrappie Robot development environment on Windows using Podman as an alternative to Docker Desktop.

---

## Why Podman on Windows?

✅ **Free & Open Source** - No licensing concerns  
✅ **Rootless** - Better security  
✅ **Docker-compatible** - Most commands work the same  
✅ **No daemon** - Lighter weight  
✅ **Native WSL2 support** - Good Windows integration  

---

## Prerequisites

### 1. Windows Version
- Windows 10/11 (64-bit)
- Version 2004 or higher (Build 19041+)
- WSL2 enabled

### 2. Check WSL Version
```powershell
# In PowerShell
wsl --version
# Should show WSL version 2
```

---

## Installation Steps

### Step 1: Install WSL2

```powershell
# Run in PowerShell as Administrator

# Enable WSL
wsl --install

# Set WSL2 as default
wsl --set-default-version 2

# Install Ubuntu (recommended)
wsl --install -d Ubuntu-22.04

# Reboot if needed
```

### Step 2: Install Podman

**Option A: Podman Desktop (Recommended)**

1. Download from: https://podman-desktop.io/downloads/windows
2. Run installer
3. Podman Desktop will configure WSL2 automatically

**Option B: Manual Installation**

```powershell
# In PowerShell
winget install RedHat.Podman
# Or download from: https://github.com/containers/podman/releases
```

### Step 3: Initialize Podman Machine

```powershell
# In PowerShell
podman machine init
podman machine start

# Verify
podman version
podman info
```

### Step 4: Install USB/IP for USB Devices (Optional)

For RealSense cameras and USB-Serial:

```powershell
# Install usbipd-win
winget install --interactive --exact dorssel.usbipd-win

# Reboot
```

---

## Project Setup

### 1. Clone/Navigate to Project

```bash
# In WSL2 terminal
cd /mnt/c/coding/Scrappie
# Or wherever your project is
```

### 2. Configure Environment

Create `.env` file in project root:

```bash
# Create .env file
cat > .env << 'EOF'
# ROS2 configuration
ROS_DOMAIN_ID=0

# Display for X11 (if using GUI)
DISPLAY=host.docker.internal:0

# Timezone
TZ=America/Los_Angeles
EOF
```

### 3. Build Image

```bash
# Using podman-compose (recommended)
podman-compose -f docker/docker-compose.yml build

# Or using docker-compose with Podman
docker-compose -f docker/docker-compose.yml build
```

**Note:** Podman is Docker-compatible, so `docker-compose` works with Podman.

---

## USB Device Passthrough (Windows)

### For USB-Serial (MDDS30 Motor Driver)

#### Step 1: Find USB Device in Windows

```powershell
# In PowerShell (Administrator)
usbipd list
# Note the BUSID of your USB-Serial adapter
```

#### Step 2: Attach to WSL

```powershell
# Attach USB device to WSL
usbipd bind --busid <BUSID>
usbipd attach --wsl --busid <BUSID>

# Example:
# usbipd attach --wsl --busid 3-2
```

#### Step 3: Verify in WSL

```bash
# In WSL terminal
ls -l /dev/ttyUSB*
# Should show: /dev/ttyUSB0
```

#### Step 4: Update docker-compose if needed

Edit `docker/docker-compose.yml`:
```yaml
devices:
  - /dev/ttyUSB0:/dev/ttyUSB0  # Your serial port
```

### For RealSense Cameras

Same process:
```powershell
# Find camera
usbipd list
# Look for "Intel RealSense"

# Attach
usbipd attach --wsl --busid <BUSID>
```

Verify:
```bash
# In WSL
lsusb | grep Intel
```

---

## GUI/RViz Support (Optional)

### Option 1: VcXsrv (Recommended)

1. **Download VcXsrv**
   - https://sourceforge.net/projects/vcxsrv/

2. **Install and Configure**
   - Run XLaunch
   - Select: "Multiple windows"
   - Select: "Start no client"
   - **Important**: Check "Disable access control"
   - Save configuration

3. **Start VcXsrv**
   - Run saved configuration on Windows startup

4. **Set DISPLAY in WSL**
   ```bash
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
   ```

5. **Test**
   ```bash
   # In container
   podman exec -it scrappie_core bash
   rviz2
   # Should open RViz window
   ```

### Option 2: WSLg (Windows 11 only)

Windows 11 has built-in GUI support:
```bash
# No configuration needed!
# Just set DISPLAY=:0 in .env file
```

---

## Running the Project

### Start Container

```bash
# Start in background
podman-compose -f docker/docker-compose.yml up -d

# Or with docker-compose
docker-compose -f docker/docker-compose.yml up -d

# Check status
podman ps
```

### Enter Container

```bash
# Enter container
podman exec -it scrappie_core bash

# Inside container - build workspace
cd /ws
colcon build --symlink-install
source install/setup.bash
```

### Test ROS2

```bash
# Inside container
ros2 topic list
ros2 run demo_nodes_cpp talker
```

---

## Common Issues & Solutions

### Issue 1: "Cannot connect to Podman socket"

**Solution:**
```powershell
podman machine stop
podman machine start
```

### Issue 2: "Port already in use"

**Solution:**
```bash
# Check what's using the port
netstat -ano | findstr :7400

# Kill the process or change ports in docker-compose.yml
```

### Issue 3: "USB device not found in container"

**Solution:**
```bash
# Re-attach USB device
usbipd attach --wsl --busid <BUSID>

# Restart container
podman restart scrappie_core
```

### Issue 4: "Permission denied on /dev/ttyUSB0"

**Solution:**
```bash
# In WSL
sudo chmod 666 /dev/ttyUSB0

# Or add user to dialout group
sudo usermod -a -G dialout $USER
# Re-login
```

### Issue 5: "RViz won't start / Display error"

**Solution:**
```bash
# Make sure VcXsrv is running
# Check DISPLAY variable
echo $DISPLAY

# Set correct DISPLAY
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0

# Test with simple X app
podman exec -it scrappie_core xeyes
```

### Issue 6: "ROS2 nodes can't discover each other"

**Solution:**
```bash
# Make sure ROS_DOMAIN_ID is set
echo $ROS_DOMAIN_ID

# Check firewall isn't blocking DDS ports
# Windows Firewall > Allow app > Private networks
```

---

## Podman-Specific Commands

### Podman vs Docker Commands

| Docker Command | Podman Equivalent | Notes |
|----------------|-------------------|-------|
| `docker ps` | `podman ps` | Same |
| `docker build` | `podman build` | Same |
| `docker run` | `podman run` | Same |
| `docker-compose up` | `podman-compose up` | Install podman-compose |
| `docker exec -it` | `podman exec -it` | Same |

### Useful Podman Commands

```bash
# List containers
podman ps -a

# View logs
podman logs scrappie_core

# Stop container
podman stop scrappie_core

# Remove container
podman rm scrappie_core

# List images
podman images

# Clean up
podman system prune -a
```

---

## Performance Tips

### 1. Use WSL2 Native Filesystem

```bash
# DON'T: Access Windows filesystem
cd /mnt/c/coding/Scrappie  # Slower

# DO: Copy to WSL filesystem
cp -r /mnt/c/coding/Scrappie ~/Scrappie
cd ~/Scrappie  # Faster!
```

### 2. Allocate More Resources

Edit `.wslconfig` in Windows home directory:

```ini
# C:\Users\YourName\.wslconfig
[wsl2]
memory=8GB
processors=4
swap=2GB
```

Restart WSL:
```powershell
wsl --shutdown
wsl
```

### 3. Use Podman Volumes

```bash
# Create named volume
podman volume create scrappie_build

# Use in docker-compose.yml
volumes:
  - scrappie_build:/ws/build
```

---

## Testing Checklist

- [ ] WSL2 installed and running
- [ ] Podman installed and machine started
- [ ] Project accessible in WSL
- [ ] `.env` file created
- [ ] Docker image builds successfully
- [ ] Container starts: `podman ps`
- [ ] Can enter container: `podman exec -it scrappie_core bash`
- [ ] ROS2 works: `ros2 topic list`
- [ ] USB devices attached (if testing hardware)
- [ ] GUI works (if using RViz)

---

## Alternative: Docker Desktop

If you have Docker Desktop license:

1. Install Docker Desktop for Windows
2. Enable WSL2 backend
3. Use original `docker-compose.yml` with `network_mode: host` changed to `bridge`

Same configuration applies!

---

## Quick Reference

### Start Development Session

```bash
# 1. Start Podman (if not running)
podman machine start

# 2. Attach USB devices (if needed)
# (In PowerShell)
usbipd attach --wsl --busid <BUSID>

# 3. Start container
cd ~/Scrappie
podman-compose -f docker/docker-compose.yml up -d

# 4. Enter container
podman exec -it scrappie_core bash

# 5. Build and run
cd /ws
colcon build --symlink-install
source install/setup.bash
ros2 launch scrappie_bringup scrappie_bringup.launch.py
```

### Stop Development Session

```bash
# Stop container
podman-compose -f docker/docker-compose.yml down

# Or just stop
podman stop scrappie_core
```

---

## Resources

- **Podman Desktop**: https://podman-desktop.io/
- **WSL Documentation**: https://learn.microsoft.com/en-us/windows/wsl/
- **usbipd-win**: https://github.com/dorssel/usbipd-win
- **VcXsrv**: https://sourceforge.net/projects/vcxsrv/
- **Podman Documentation**: https://docs.podman.io/

---

## Support

**Common Problems:**
1. Check WSL is running: `wsl --status`
2. Check Podman machine: `podman machine list`
3. Check USB attachment: `usbipd list`
4. Check firewall for ROS2 ports (7400-7500 UDP)

**Still having issues?**
- Enable WSL verbose logging
- Check Podman logs: `podman logs scrappie_core`
- Verify network: `podman network inspect bridge`

---

**You're ready to develop on Windows with Podman! 🚀**
