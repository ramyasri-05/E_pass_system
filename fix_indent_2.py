
lines = []
with open('gesture_control.py', 'r') as f:
    lines = f.readlines()

# Line 396 (index 395) has an indentation issue. It should match the indentation of the 'if' at line 386.
# It seems lines 396 to 430 are indented by 1 extra space.
start_idx = 396
end_idx = 435 # approximate end of the block

for i in range(start_idx, end_idx):
    if i < len(lines) and len(lines[i]) > 0 and lines[i][0] == ' ':
         # Remove exactly 1 space
        lines[i] = lines[i][1:]

with open('gesture_control.py', 'w') as f:
    f.writelines(lines)
