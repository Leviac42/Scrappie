#!/bin/bash
# Jetson Orin Nano Setup Script for Scrappie Robot
# Run this script on the Jetson to configure hardware interfaces

set -e

echo "=========================================="
echo "Scrappie Robot - Jetson Orin Nano Setup"
echo "=========================================="

# Check if running on Jetson
if [ ! -f /etc/nv_tegra_release ]; then
    echo "ERROR: This script must be run on a Jetson device"
    exit 1
fi

echo "Detected Jetson device:"
cat /etc/nv_tegra_release

# 1. Enable GPIO UART (UART1 - /dev/ttyTHS0)
echo ""
echo "1. Configuring GPIO UART on 40-pin header..."
echo "   Pins: 8 (TXD), 10 (RXD), 6 (GND)"

# Check if UART is already enabled
if [ -c "/dev/ttyTHS0" ]; then
    echo "   ✓ /dev/ttyTHS0 already exists"
else
    echo "   Enabling UART1..."
    # Note: On recent JetPack versions, UART may need device tree modification
    # For JP5.x and later, use jetson-io tool
    if command -v /opt/nvidia/jetson-io/jetson-io.py &> /dev/null; then
        echo "   Use jetson-io to enable UART1:"
        echo "   sudo /opt/nvidia/jetson-io/jetson-io.py"
        echo "   Select: Configure Jetson 40-pin Header > UART1"
    fi
fi

# Set UART permissions
if [ -c "/dev/ttyTHS0" ]; then
    echo "   Setting UART permissions..."
    sudo usermod -a -G dialout $USER
    sudo chmod 666 /dev/ttyTHS0
    echo "   ✓ UART permissions configured"
fi

# 2. Install RealSense USB rules
echo ""
echo "2. Installing RealSense USB rules..."
RULES_FILE="/etc/udev/rules.d/99-realsense-libusb.rules"

if [ ! -f "$RULES_FILE" ]; then
    sudo tee $RULES_FILE > /dev/null <<'EOF'
# RealSense D435i USB rules for Jetson
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b3a", MODE:="0666", GROUP:="plugdev"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b07", MODE:="0666", GROUP:="plugdev"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b37", MODE:="0666", GROUP:="plugdev"
EOF
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    echo "   ✓ RealSense USB rules installed"
else
    echo "   ✓ RealSense USB rules already exist"
fi

# Add user to video and plugdev groups
sudo usermod -a -G video $USER
sudo usermod -a -G plugdev $USER

# 3. Install Docker with NVIDIA runtime (if not already installed)
echo ""
echo "3. Checking Docker installation..."

if ! command -v docker &> /dev/null; then
    echo "   Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    sudo usermod -aG docker $USER
    echo "   ✓ Docker installed"
else
    echo "   ✓ Docker already installed"
fi

# Check for nvidia-docker runtime
if ! docker info 2>/dev/null | grep -q nvidia; then
    echo "   Installing NVIDIA Container Runtime..."
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
        sudo tee /etc/apt/sources.list.d/nvidia-docker.list
    
    sudo apt-get update
    sudo apt-get install -y nvidia-container-runtime nvidia-docker2
    sudo systemctl restart docker
    echo "   ✓ NVIDIA Container Runtime installed"
else
    echo "   ✓ NVIDIA Container Runtime already configured"
fi

# 4. Install docker-compose
echo ""
echo "4. Checking docker-compose..."

if ! command -v docker-compose &> /dev/null; then
    echo "   Installing docker-compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose
    echo "   ✓ docker-compose installed"
else
    echo "   ✓ docker-compose already installed"
fi

# 5. Install jetson-stats (jtop)
echo ""
echo "5. Installing jetson-stats (jtop)..."

if ! command -v jtop &> /dev/null; then
    sudo pip3 install -U jetson-stats
    echo "   ✓ jetson-stats installed (run 'jtop' to monitor)"
else
    echo "   ✓ jetson-stats already installed"
fi

# 6. Configure power mode for robotics (15W 6-core mode)
echo ""
echo "6. Configuring power mode..."
echo "   Current mode: $(sudo nvpmodel -q | grep 'NV Power Mode')"
echo "   Setting to MAXN (maximum performance)..."
sudo nvpmodel -m 0
sudo jetson_clocks
echo "   ✓ Power mode set to MAXN"

# 7. Create systemd service for auto-start (optional)
echo ""
echo "7. Creating systemd service..."

SERVICE_FILE="/etc/systemd/system/scrappie-robot.service"

if [ ! -f "$SERVICE_FILE" ]; then
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Scrappie Robot ROS2 Stack
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/$USER/scrappie
ExecStart=/usr/bin/docker-compose -f docker/docker-compose.jetson.yml up -d
ExecStop=/usr/bin/docker-compose -f docker/docker-compose.jetson.yml down
User=$USER

[Install]
WantedBy=multi-user.target
EOF
    echo "   ✓ Systemd service created"
    echo "   Enable with: sudo systemctl enable scrappie-robot.service"
else
    echo "   ✓ Systemd service already exists"
fi

# 8. Summary
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Hardware Configuration:"
echo "  • GPIO UART: /dev/ttyTHS0 (pins 8, 10)"
echo "  • USB Cameras: Auto-detected"
echo "  • Power Mode: MAXN (15W)"
echo ""
echo "Next Steps:"
echo "  1. Reboot or re-login for group changes"
echo "  2. Connect hardware:"
echo "     - MDDS30 TXD → Pin 10 (RXD)"
echo "     - MDDS30 RXD → Pin 8 (TXD)"
echo "     - MDDS30 GND → Pin 6 (GND)"
echo "     - RealSense cameras via USB 3.0"
echo "  3. Build Docker image:"
echo "     cd ~/scrappie"
echo "     docker-compose -f docker/docker-compose.jetson.yml build"
echo "  4. Start robot:"
echo "     docker-compose -f docker/docker-compose.jetson.yml up -d"
echo ""
echo "Monitor Jetson: jtop"
echo "View logs: docker logs -f scrappie_jetson"
echo ""
echo "IMPORTANT: You may need to reboot for all changes to take effect"
echo "=========================================="
