# Rover — Working Notes

## Saving the slam_toolbox map

Once the map is built, serialize it to `maps/my_map.posegraph` + `maps/my_map.data`:

```bash
docker compose exec lidar bash -c "source /opt/ros/humble/setup.bash && source /opt/overlay_ws/install/setup.bash && ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph '{filename: /ros_ws/maps/my_map}'"
```

To reload the map on next startup

```bash
docker compose exec lidar bash -c "source /opt/ros/humble/setup.bash && source /opt/overlay_ws/install/setup.bash && ros2 service call /slam_toolbox/deserialize_map slam_toolbox/srv/DeserializePoseGraph '{filename: /ros_ws/maps/my_map, match_type: 2, initial_pose: {x: 0.0, y: 0.0, theta: 0.0}}'"
```

## Sync Windows Clock
```powershell
net start w32time
w32tm /resync /force
```

## Wi-Fi

```bash
# Set the WiFi regulatory country (persists across reboots). Required once per Pi,
# or 5 GHz AP won't start (default regdomain "00" forbids it). Verify: iw reg get
sudo raspi-config nonint do_wifi_country US
```

```bash
# 5 GHz hotspot (band a, ch 36) so WiFi doesn't collide with 2.4 GHz Bluetooth
# on the same onboard chip -> fixes the controller dropping under load.
# Needs the country set (above); clients must support 5 GHz.
sudo nmcli con add type wifi ifname wlan0 con-name "Rover-Hotspot" autoconnect no ssid "Rover"
sudo nmcli con modify "Rover-Hotspot" 802-11-wireless.mode ap 802-11-wireless.band a 802-11-wireless.channel 36 ipv4.method shared
sudo nmcli con modify "Rover-Hotspot" wifi-sec.key-mgmt wpa-psk wifi-sec.psk 'B&GSP!R!T'
sudo nmcli con modify "Rover-Hotspot" ipv4.addresses 10.42.0.1/24
```

```bash
sudo nmcli con up Rover-Hotspot
```

```bash
sudo nmcli con up BG
```

```bash
sudo nmcli connection modify BG connection.autoconnect no
sudo nmcli connection modify Rover-Hotspot connection.autoconnect yes
```

## System changes made on the Pi (not in git — re-apply on a fresh SD card)
These edits live in `/boot/firmware/config.txt`. Each needs a reboot.

```bash
# Full USB current budget — or the RPLIDAR motor browns out / the port over-currents
usb_max_current_enable=1

# Hardware PWM on GPIO12/13 for the motor driver (24 kHz = silent, no audible whine)
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

Lidar gotcha: the `ttyUSB` number is unstable — `docker-compose.yml` uses the
stable `/dev/serial/by-id/usb-Silicon_Labs_CP2102_...` path, not `/dev/ttyUSB0`.

### Xbox controller over Bluetooth — disable ERTM
The Xbox pad pairs but then *immediately disconnects* unless Bluetooth ERTM is
off. The `bluetooth` module is loadable, so persist it via modprobe.d:

```bash
# apply now (module is already loaded)
echo Y | sudo tee /sys/module/bluetooth/parameters/disable_ertm
# persist across reboots
echo 'options bluetooth disable_ertm=Y' | sudo tee /etc/modprobe.d/xbox-bt.conf
```

Pair once (then `trust` so it auto-reconnects on boot):
```bash
bluetoothctl
  scan on            # note the "Xbox Wireless Controller" MAC
  pair  <MAC>
  trust <MAC>
  connect <MAC>
```

The pad shows up as `/dev/input/js0` (joydev auto-loads). The `joystick`
compose service drives `cmd_vel` from it — see `scripts/joystick_node.py`. Axis
numbers there assume the xpad mapping; the stock Bluetooth driver may differ, so
verify with `jstest /dev/input/js0` if controls are wrong.

---

## Motor PWM (silent drive)
`scripts/dual_g2_hpmd_rpi.py` drives GPIO12/13 via the RP1 **hardware** PWM
(sysfs `/sys/class/pwm`) at 24 kHz, so the switching is ultrasonic and the
motors don't whine. lgpio software PWM can't reach ~20 kHz on RP1, which is why
the old 2 kHz tone was audible. Needs the `pwm-2chan` overlay above + reboot.
- Chip number is auto-detected (first `pwmchip*` with ≥2 channels). Override
  with `MOTOR_PWMCHIP=pwmchipN` if it ever collides with another PWM.
- Direction/enable/fault pins still use lgpio; only the PWM pins moved.

---

## Current working SLAM/odom config (what got it running)
- **rf2o** has no Humble apt binary → built from source into `/opt/overlay_ws`
  (Dockerfile), sourced on top of `/opt/ros/humble` in the entrypoint. Do NOT
  `--merge-install` into `/opt/ros/humble` — it clobbers ROS's `setup.bash`.
- **rf2o `init_pose_from_topic: ''`** — required; the default topic
  (`/base_pose_ground_truth`) is never published, so rf2o silently ignores
  every scan ("Waiting for laser_scans...").
- **`base_footprint`** must be the base frame for BOTH rf2o (`base_frame_id`)
  and slam (`base_frame`), or base_link gets two TF parents and the 2D map
  plane slices through the robot.
- **slam_toolbox `scan_queue_size: 20`** — fixes "Message Filter dropping
  message ... queue full" (default 1; rf2o's odom TF lands ~165 ms late, so the
  filter must buffer). Bumping rf2o `freq` did NOT help — it's latency-bound.
- **Responsiveness:** slam `map_update_interval: 1.0` (was 5.0) and
  `minimum_time_interval: 0.2` (was 0.5). rf2o `freq` 10.0.

---

## Known limitation: scan rate stuck at ~11 Hz (10 Hz is enough — not pursued)
`/scan` publishes ~11.3 Hz regardless of `scan_frequency`. Root cause: the
Slamtec ROS2 drivers hardcode A-series motor speed (`setMotorSpeed(600)` ≈
10 Hz) and expose no PWM param — the hardware *can* do 15 Hz but is never
commanded to. Ruled out CPU, power, and scan mode (all measured).

**Real fix for "responsive odom to drive faster":** rf2o is scan-rate-bound
(~11 Hz, ~165 ms latency). Wheel encoders + IMU fused odom (50–100 Hz) is the
proper upgrade, with slam/rf2o correcting drift. `motor_driver` exists; encoders
are the missing piece.

---

## Odom/SLAM architecture decision (Topology 1)
**Decision:** odometry from RTAB-Map **visual-inertial** odom (`rgbd_odometry` +
D455 IMU); map building **and loop closure stay on slam_toolbox** (LiDAR).
Decouple the odom engine from the map engine.

**Why:** rf2o (any 2D-lidar odom) slips down long straight hallways — the scan is
identical frame-to-frame along the travel axis, so forward translation is
unobservable. The forward camera sees features moving toward it (doors, floor
seams, lights) and observes that axis. Keep slam_toolbox for mapping because
RGBD occupancy grids aren't as clean as the lidar ones.

**TF ownership — exactly one writer each:**
- `odom→base_footprint` ← `rgbd_odometry` (set rf2o `publish_tf:=False`, or drop it).
- `map→odom` + occupancy grid ← slam_toolbox (unchanged).

**Implemented (visual-inertial odom):** `launch/camera_odom.launch.py` runs
`imu_filter_madgwick` (raw `/camera/camera/imu` → oriented `/imu/data`, `use_mag:=false`)
feeding `rtabmap_odom`'s `rgbd_odometry` (`frame_id:=base_footprint`, `odom_frame_id:=odom`,
`publish_tf:=true`, `wait_imu_to_init:=true`, depth `aligned_depth_to_color`). Started by the
`camera_odom` compose service; needs `camera` + `robot_description` up.
**When LiDAR mapping is re-enabled, `lidar.launch.py` still sets rf2o `publish_tf: True` —
flip it to `False` (or drop rf2o) so `rgbd_odometry` is the sole writer of `odom→base_footprint`.**

**D455 IMU** is currently off (`enable_gyro/accel: false` in `config/camera_config.yaml`).
To enable it *cleanly*, build librealsense from source with
`-DFORCE_RSUSB_BACKEND=ON` (RSUSB/libuvc backend) into `/opt/overlay_ws` — avoids
host kernel patching, which is the fragile path that breaks on kernel updates.
Then `enable_gyro/accel:=true`, `unite_imu_method:=2`, optionally
`imu_filter_madgwick` → `/imu/data`. For `rgbd_odometry` also set
`align_depth:=true`, `640x480x30`, and drop the pointcloud.

**Staging:** (1) visual-only `rgbd_odometry` replacing rf2o's TF — corridor fix,
no rebuild. (2) add IMU (RSUSB build) → visual-inertial. (3) optional true
3-sensor LVIO: rf2o back as a *non-TF* velocity source + `robot_localization` EKF,
assigning DoF by sensor — **vx←camera, vy+vyaw←laser (360°), yaw-rate/gravity←IMU**.
Per-DoF assignment structurally excludes the laser's corridor slip (never take vx
from the laser). Tightly-coupled single-node LVIO (LVI-SAM / FAST-LIVO) ruled out
— too heavy for the Pi 5.

---
