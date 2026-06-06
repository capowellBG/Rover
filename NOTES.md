# Rover — Working Notes

## Pi setup requirement: max USB current (RPLIDAR motor)
The RPLIDAR A2M12 motor needs the Pi 5's full USB current budget, or the port
over-currents / the motor browns out. On a fresh Pi, enable it once, then reboot:

```bash
echo -e '\n# Allow full USB current budget for RPLidar motor\nusb_max_current_enable=1' | sudo tee -a /boot/firmware/config.txt
```

Related gotcha: the lidar's `ttyUSB` number is unstable — use the
`/dev/serial/by-id/usb-Silicon_Labs_CP2102_...` path (already done in
`docker-compose.yml`), not `/dev/ttyUSB0` directly.

---

## OPTIONAL (deprioritized): spin the lidar at 15 Hz  (NOT solved; 10 Hz is enough)

**Symptom:** `/scan` publishes at ~11.3 Hz no matter what we set. We want 15 Hz
for more responsive odom (to drive faster).

**Ruled out (with evidence):**
- NOT CPU — rf2o is ~1/3 of one core; ~3 cores free (4-core Pi 5).
- NOT power — `usb_max_current_enable=1` is set, no over-current events in dmesg.
- NOT scan mode — measured ~11.2–11.3 Hz in BOTH `Sensitivity` and `Boost`.
- NOT `scan_frequency` — driver accepts `15.0`, logs "scan frequency: 15.0 Hz",
  but the motor never changes. The param is only used for buffer math + the log.

**Root cause (confirmed in driver source):** the Slamtec ROS2 drivers never
command a higher motor speed for A-series units.
- Stock `rplidar_ros`: A-series path hardcodes `setMotorSpeed(600)` (= 10 Hz /
  600 RPM default). Only S-series get `setMotorSpeed(scan_frequency*60)`.
- Newer `sllidar_ros2`: calls `setMotorSpeed()` with no arg (SDK default).
- No parameter in any version exposes the motor PWM. Hardware *can* do 15 Hz
  (default 600 RPM is just never raised).

**Next step (planned, not started):** patch `rplidar_ros` and build it into the
same overlay as rf2o (`/opt/overlay_ws`); the overlay copy shadows the apt one.
Change the A-series motor call from fixed `setMotorSpeed(600)` to a higher PWM
driven by `scan_frequency` (motor PWM range ~0–1023; 600≈10 Hz, try ~900 for
15 Hz). Then set `scan_frequency: 15` and measure `ros2 topic hz /scan`.
- **CAVEAT:** only works if this USB adapter does PWM motor control. Some
  A-series adapters are DTR on/off only (fixed speed) → 15 Hz would then need an
  external PWM source (Pi GPIO / Arduino, 25 kHz to the MOTOCTL pin). One
  build-and-measure tells us which case we're in.

**Decision:** 10 Hz is sufficient. Reverted to `scan_mode: 'Sensitivity'` and
dropped the `scan_frequency` override. The 15 Hz driver patch above is optional.

**Better long-term path for "responsive odom to drive faster":** rf2o laser
odometry is fundamentally scan-rate-bound (~11 Hz, ~165 ms latency). Wheel
encoders + IMU fused odometry (50–100 Hz, ~ms latency) is the real fix, with
slam_toolbox / rf2o correcting drift. Highest-leverage upgrade. `motor_driver`
already exists; encoders are the missing piece.

---

## Current working config (reference / what we fixed this session)
- **rf2o** has no Humble apt binary → built from source into `/opt/overlay_ws`
  (Dockerfile). Entrypoint sources the overlay on top of `/opt/ros/humble`.
  Do NOT `--merge-install` into `/opt/ros/humble` — it clobbers ROS's
  `setup.bash` and breaks `rclpy` for every node.
- **rf2o `init_pose_from_topic: ''`** — required. Default is
  `/base_pose_ground_truth`, which nothing publishes; with it non-empty rf2o
  silently ignores every scan and only logs "Waiting for laser_scans...".
- **`base_footprint`** frame at floor (URDF) is the slam/rf2o base_frame, so the
  2D map plane sits under the robot instead of slicing through its middle.
  (rf2o `base_frame_id` AND slam `base_frame` must both be `base_footprint`, or
  base_link gets two TF parents.)
- **slam_toolbox `scan_queue_size: 20`** — the real fix for "Message Filter
  dropping message ... queue is full". Default is 1; rf2o's odom TF lands
  ~165 ms after each scan's stamp, so the filter must buffer a few scans.
  Bumping rf2o `freq` did NOT help (it's latency-bound, not rate-bound).
- **Responsiveness:** slam `map_update_interval: 1.0` (was 5.0, the "map clips
  in every few seconds" cause) and `minimum_time_interval: 0.2` (was 0.5).
- rf2o `freq` is `10.0`; could bump to `11` to use the full ~11.3 Hz scan rate
  (small, free win) — left at 10 pending the 15 Hz decision above.
