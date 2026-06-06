#!/usr/bin/env python3
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dual_g2_hpmd_rpi as driver

motors = driver.motors
MAX_SPEED = driver.MAX_SPEED

print("Motor test — spinning both motors forward at half speed for 3 seconds.")
print("Press Ctrl+C to stop early.\n")

try:
    if motors.getFaults():
        print("WARNING: fault detected before start — check motor driver wiring.")

    motors.setSpeeds(MAX_SPEED // 2, MAX_SPEED // 2)
    print(f"Running at speed {MAX_SPEED // 2}/{MAX_SPEED}...")

    for i in range(3, 0, -1):
        time.sleep(1)
        print(f"  {i}s remaining")

    motors.setSpeeds(0, 0)
    print("Done.")

except KeyboardInterrupt:
    motors.forceStop()
    print("\nStopped by user.")
