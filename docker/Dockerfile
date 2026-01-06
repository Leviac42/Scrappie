FROM ros:humble-perception

# Install ecosystem dependencies
RUN apt-get update && apt-get install -y \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-realsense2-camera \
    ros-humble-realsense2-description \
    ros-humble-slam-toolbox \
    ros-humble-robot-localization \
    ros-humble-xacro \
    ros-humble-depthimage-to-laserscan \
    python3-pip \
    python3-serial \
    python3-colcon-common-extensions \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip3 install pyserial

# Setup workspace
WORKDIR /ws

# Source ros setup in bashrc and overlay workspace
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "if [ -f /ws/install/setup.bash ]; then source /ws/install/setup.bash; fi" >> ~/.bashrc

# Set entrypoint
COPY docker/ros_entrypoint.sh /
RUN chmod +x /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
