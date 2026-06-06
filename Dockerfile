FROM ros:humble-ros-core

# System Dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    && pip3 install lgpio \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ROS Packages
RUN apt-get update && apt-get install -y \
    ros-humble-foxglove-bridge \
    ros-humble-robot-state-publisher \
    ros-humble-xacro \
    ros-humble-rplidar-ros \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*