"""
Motor Test Checklist
---------------------
1. M1 forward only        — verify left wheels roll forward
2. M1 backward only       — verify left wheels roll backward
3. M2 forward only        — verify right wheels roll forward
4. M2 backward only       — verify right wheels roll backward
5. Both forward           — robot should drive straight, no pulling left or right
6. Both backward          — robot should drive straight in reverse
7. M1 forward, M2 back    — robot should spin in place to the right
8. M1 backward, M2 forward — robot should spin in place to the left

Notes:
- If a side spins the wrong direction, negate that motor's value in software
- Do not worry about speed calibration at this stage
- Left motors (M1) and right motors (M2) are each wired as a single pair
"""

print("Hello World")