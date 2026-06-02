FROM ros:humble-ros-core

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-setuptools \
    wget \
    unzip \
    make \
    gcc \
    git \
    cmake \
    libusb-1.0-0-dev \
    libssl-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install ROS Packages
RUN apt-get update && apt-get install -y \
    ros-humble-rclpy \
    ros-humble-geometry-msgs \
    ros-humble-foxglove-bridge \
    ros-humble-librealsense2* \
    ros-humble-realsense2-camera \
    ros-humble-image-transport-plugins \
    ros-humble-rtabmap-ros \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    ros-humble-xacro \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Rebuild librealsense with RSUSB backend so IMU works without Intel's kernel patches.
# The apt package uses the V4L2+IIO backend which requires a d4xx-class kernel module
# that doesn't exist on Raspberry Pi OS. RSUSB uses libusb directly and needs no patches.
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

# Build and install pigpio from source (not in apt repos on Bookworm)
RUN wget https://github.com/joan2937/pigpio/archive/master.zip \
    && unzip master.zip \
    && cd pigpio-master \
    && make \
    && make install \
    && cd .. \
    && rm -rf pigpio-master master.zip

# Install Pololu Dual G2 High-Power Motor Driver library
RUN git clone https://github.com/pololu/dual-g2-high-power-motor-driver-rpi \
    && cd dual-g2-high-power-motor-driver-rpi \
    && python3 setup.py install \
    && cd .. \
    && rm -rf dual-g2-high-power-motor-driver-rpi

WORKDIR /ros_ws
