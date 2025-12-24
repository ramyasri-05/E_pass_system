
lines = []
with open('gesture_control.py', 'r') as f:
    lines = f.readlines()

# Get indentation of line 386 (index 385)
ref_line = lines[385]
indent_str = ""
for char in ref_line:
    if char == ' ':
        indent_str += " "
    else:
        break

# Apply this indentation to lines 396 to 435 (indices 395 to 434)
start_idx = 395
end_idx = 435

for i in range(start_idx, end_idx):
    if i < len(lines):
        stripped = lines[i].lstrip()
        if stripped: # If not empty line
            lines[i] = indent_str + stripped
        else:
            lines[i] = "\n" # keep empty lines empty

with open('gesture_control.py', 'w') as f:
    f.writelines(lines)
