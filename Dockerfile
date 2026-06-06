FROM ros:humble-ros-core

RUN apt-get update && apt-get install -y \
    python3-pip \
    build-essential \
    && pip3 install lgpio \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*