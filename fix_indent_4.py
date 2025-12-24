
lines = []
with open('gesture_control.py', 'r') as f:
    lines = f.readlines()

# Line 396 is 'else:'. It has some indentation.
# Lines 397 to 435 need to represent the block inside 'else:', so they need MORE indentation.
# Currently they seem to have the SAME indentation as 'else:'.

ref_line_else = lines[396] 
indent_str_else = ""
for char in ref_line_else:
    if char == ' ':
        indent_str_else += " "
    else:
        break

# define the new indentation for the block
block_indent = indent_str_else + "    " # Add 4 spaces

start_idx = 397
end_idx = 435

for i in range(start_idx, end_idx):
    if i < len(lines):
        stripped = lines[i].lstrip()
        if stripped: 
            lines[i] = block_indent + stripped
        else:
             lines[i] = "\n"

with open('gesture_control.py', 'w') as f:
    f.writelines(lines)
