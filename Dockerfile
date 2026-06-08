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
    ros-humble-slam-toolbox \
    ros-humble-realsense2-camera \
    ros-humble-image-transport-plugins \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# rf2o_laser_odometry has no Humble apt binary — build from source into an overlay
RUN apt-get update && apt-get install -y \
    git build-essential cmake \
    python3-colcon-common-extensions python3-rosdep \
    && rosdep init && rosdep update \
    && mkdir -p /opt/overlay_ws/src \
    && git clone https://github.com/MAPIRlab/rf2o_laser_odometry.git /opt/overlay_ws/src/rf2o_laser_odometry \
    && rosdep install --from-paths /opt/overlay_ws/src --ignore-src -r -y \
    && . /opt/ros/humble/setup.sh \
    && cd /opt/overlay_ws \
    && colcon build --merge-install \
    && rm -rf /opt/overlay_ws/build /opt/overlay_ws/log /opt/overlay_ws/src \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Source the overlay on top of the ROS underlay in the entrypoint
RUN cat > /ros_entrypoint.sh <<'EOF'
#!/bin/bash
set -e
source /opt/ros/$ROS_DISTRO/setup.bash
source /opt/overlay_ws/install/setup.bash
exec "$@"
EOF