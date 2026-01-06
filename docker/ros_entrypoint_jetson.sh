#!/bin/bash
set -e

# Jetson-specific ROS2 entrypoint script

echo "Starting Scrappie Robot on Jetson Orin Nano..."

# Check Jetson power mode
if command -v jetson_clocks &> /dev/null; then
    echo "Jetson power mode: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
    # Optional: Enable max performance
    # sudo jetson_clocks
fi

# Enable GPIO UART if not already enabled
if [ ! -c "/dev/ttyTHS0" ]; then
    echo "Warning: /dev/ttyTHS0 not found. GPIO UART may not be configured."
    echo "Run: sudo busybox devmem 0x0c302000 32 0x0000C400"
fi

# Source ROS2 workspace
source /opt/ros/humble/setup.bash

# Source RealSense overlay
if [ -f /opt/ros_ws/install/setup.bash ]; then
    source /opt/ros_ws/install/setup.bash
fi

# Source Scrappie workspace if it exists
if [ -f /ws/install/setup.bash ]; then
    source /ws/install/setup.bash
fi

# Set RMW implementation for better performance
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Jetson-specific optimizations
export OPENBLAS_CORETYPE=ARMV8
export OMP_NUM_THREADS=$(nproc)

# RealSense USB rule check
if [ -f /etc/udev/rules.d/99-realsense-libusb.rules ]; then
    echo "RealSense USB rules configured"
else
    echo "Warning: RealSense USB rules not found. Run setup script."
fi

echo "Environment ready. Launching command: $@"

# Execute the command passed to docker run
exec "$@"
