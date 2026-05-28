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
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-rclpy \
    ros-humble-geometry-msgs \
    ros-humble-foxglove-bridge \
    ros-humble-librealsense2* \
    ros-humble-realsense2-camera \
    ros-humble-image-transport-plugins \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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