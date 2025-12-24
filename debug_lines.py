import sys

with open('e:/swap_data - Copy/gesture_control.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'update_state' in line:
        print(f"{i+1}: {repr(line)}")
