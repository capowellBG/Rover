FROM ros:humble-ros-core

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-pigpio \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Pololu Dual G2 High-Power Motor Driver library
RUN git clone https://github.com/pololu/dual-g2-high-power-motor-driver-rpi \
    && cd dual-g2-high-power-motor-driver-rpi \
    && python3 setup.py install \
    && cd .. \
    && rm -rf dual-g2-high-power-motor-driver-rpi

WORKDIR /ros_ws