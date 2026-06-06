FROM ros:humble-ros-core

# System Dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    build-essential \
    python3-colcon-common-extensions \
    python3-serial \
    git \
    && pip3 install lgpio \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ROS Packages
RUN apt-get update && apt-get install -y \
    ros-humble-foxglove-bridge \
    ros-humble-robot-state-publisher \
    ros-humble-xacro \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Build rplidar_ros from source
RUN mkdir -p /rplidar_ws/src \
    && git clone -b ros2 --depth 1 https://github.com/Slamtec/rplidar_ros.git /rplidar_ws/src/rplidar_ros \
    && cd /rplidar_ws \
    && . /opt/ros/humble/setup.sh \
    && colcon build \
    && rm -rf /rplidar_ws/src /rplidar_ws/build /root/.colcon

# Extend the entrypoint to also source the rplidar overlay
RUN printf '#!/bin/bash\nset -e\nsource "/opt/ros/humble/setup.bash"\nsource "/rplidar_ws/install/setup.bash"\nexec "$@"\n' > /ros_entrypoint.sh \
    && chmod +x /ros_entrypoint.sh