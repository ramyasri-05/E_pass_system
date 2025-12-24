
lines = []
with open('gesture_control.py', 'r') as f:
    lines = f.readlines()

# Lines 386 to 405 (0-indexed: 385 to 404) seem to have 1 extra space of indentation
# We want to remove 1 space from the beginning of these lines.
start_idx = 385
end_idx = 405

for i in range(start_idx, end_idx):
    if len(lines[i]) > 0 and lines[i][0] == ' ':
        lines[i] = lines[i][1:]

with open('gesture_control.py', 'w') as f:
    f.writelines(lines)
