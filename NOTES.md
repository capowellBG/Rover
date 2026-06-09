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
sudo nmcli con add type wifi ifname wlan0 con-name "Rover-Hotspot" autoconnect no ssid "Rover"
sudo nmcli con modify "Rover-Hotspot" 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
sudo nmcli con modify "Rover-Hotspot" wifi-sec.key-mgmt wpa-psk wifi-sec.psk 'B&GSP!R!T'
sudo nmcli con modify "Rover-Hotspot" ipv4.addresses 10.42.0.1/24
```

```bash
sudo nmcli con up Rover-Hotspot
```

```bash
sudo nmcli con up BG
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
