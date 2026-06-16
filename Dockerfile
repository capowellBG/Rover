FROM ros:humble-ros-core

# System dependencies + shared build tooling (used by the librealsense source build)
RUN apt-get update && apt-get install -y \
    python3-pip \
    git build-essential cmake libusb-1.0-0-dev libssl-dev pkg-config \
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
    ros-humble-rtabmap-odom \
    ros-humble-imu-filter-madgwick \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# librealsense from source, RSUSB backend — D455 IMU without host kernel patching
RUN git clone https://github.com/IntelRealSense/librealsense.git -b v2.57.7 --depth 1 \
    && cd librealsense \
    && mkdir build && cd build \
    && cmake .. \
        -DFORCE_RSUSB_BACKEND=ON \
        -DCMAKE_INSTALL_PREFIX=/opt/ros/humble \
        -DCMAKE_INSTALL_LIBDIR=lib/aarch64-linux-gnu \
        -DBUILD_EXAMPLES=OFF \
        -DBUILD_GRAPHICAL_EXAMPLES=OFF \
        -DBUILD_PYTHON_BINDINGS=OFF \
        -DBUILD_UNIT_TESTS=OFF \
        -DCMAKE_BUILD_TYPE=Release \
    && make -j$(nproc) \
    && make install \
    && cd / && rm -rf librealsense

# Source the ROS underlay in the entrypoint
RUN cat > /ros_entrypoint.sh <<'EOF'
#!/bin/bash
set -e
source /opt/ros/$ROS_DISTRO/setup.bash
exec "$@"
EOF