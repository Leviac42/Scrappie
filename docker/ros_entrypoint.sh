#!/bin/bash
set -e

# Source ROS2 workspace
source /opt/ros/humble/setup.bash

# Source overlay workspace if it exists
if [ -f /ws/install/setup.bash ]; then
    source /ws/install/setup.bash
fi

# Execute the command passed to docker run
exec "$@"
