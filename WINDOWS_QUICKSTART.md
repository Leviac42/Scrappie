# Windows Quick Start

## TL;DR - Get Running in 5 Minutes

### Prerequisites
- Windows 10/11 (Build 19041+)
- WSL2 installed
- Podman Desktop installed

### Quick Commands

```bash
# 1. In WSL2 - Navigate to project
cd /mnt/c/coding/Scrappie

# 2. Start container
podman-compose -f docker/docker-compose.yml up -d

# 3. Enter container
podman exec -it scrappie_core bash

# 4. Build workspace
cd /ws
colcon build --symlink-install
source install/setup.bash

# 5. Test ROS2
ros2 topic list
```

---

## First-Time Setup

### 1. Install WSL2
```powershell
# PowerShell (Administrator)
wsl --install -d Ubuntu-22.04
```

### 2. Install Podman Desktop
Download: https://podman-desktop.io/downloads/windows

### 3. Initialize Podman
```powershell
podman machine init
podman machine start
```

### 4. (Optional) USB Support
```powershell
winget install --interactive --exact dorssel.usbipd-win
```

---

## USB Device Setup

### Attach USB-Serial Adapter

```powershell
# PowerShell (Administrator)

# 1. List USB devices
usbipd list

# 2. Find your USB-Serial (note BUSID)
# Example: BUSID 3-2

# 3. Bind (one-time)
usbipd bind --busid 3-2

# 4. Attach to WSL
usbipd attach --wsl --busid 3-2
```

### Verify in WSL
```bash
ls -l /dev/ttyUSB0
```

---

## GUI/RViz Setup (Optional)

### Option 1: VcXsrv (Windows 10/11)

1. Download: https://sourceforge.net/projects/vcxsrv/
2. Run XLaunch → Multiple windows → Disable access control
3. In WSL:
   ```bash
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
   ```

### Option 2: WSLg (Windows 11 Only)
No setup needed! Just works.

---

## Daily Workflow

### Morning Start
```bash
# 1. Start Podman machine (if not running)
podman machine start

# 2. Attach USB (if using hardware)
# PowerShell: usbipd attach --wsl --busid 3-2

# 3. Start container
cd /mnt/c/coding/Scrappie
podman-compose -f docker/docker-compose.yml up -d

# 4. Happy coding!
podman exec -it scrappie_core bash
```

### Evening Stop
```bash
# Stop container
podman-compose -f docker/docker-compose.yml down
```

---

## Common Commands

```bash
# Build
podman-compose -f docker/docker-compose.yml build

# Start
podman-compose -f docker/docker-compose.yml up -d

# Stop
podman-compose -f docker/docker-compose.yml down

# Logs
podman logs -f scrappie_core

# Shell
podman exec -it scrappie_core bash

# List containers
podman ps
```

---

## Troubleshooting

### Container won't start
```bash
podman machine restart
```

### USB not showing up
```powershell
# Re-attach in PowerShell
usbipd detach --busid 3-2
usbipd attach --wsl --busid 3-2
```

### Port conflicts
```bash
# Change ports in docker-compose.yml
# Or kill conflicting process
```

### GUI not working
```bash
# Make sure VcXsrv is running
# Check DISPLAY
echo $DISPLAY

# Should be: <IP>:0
```

---

## Performance Tips

### Use WSL Filesystem
```bash
# Slow
cd /mnt/c/coding/Scrappie

# Fast - copy to WSL
cp -r /mnt/c/coding/Scrappie ~/Scrappie
cd ~/Scrappie
```

### Allocate More RAM
Create `C:\Users\YourName\.wslconfig`:
```ini
[wsl2]
memory=8GB
processors=4
```

Then restart:
```powershell
wsl --shutdown
```

---

## Full Documentation

- **Complete Setup**: [WINDOWS_PODMAN_SETUP.md](WINDOWS_PODMAN_SETUP.md)
- **General Guide**: [README.md](README.md)
- **Quick Commands**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

**Ready to develop on Windows! 🪟🚀**
