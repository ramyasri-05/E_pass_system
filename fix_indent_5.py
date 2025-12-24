
lines = []
with open('gesture_control.py', 'r') as f:
    lines = f.readlines()

# Based on previous failure:
# Line 396 is 'else:'.
# Line 397 is '# New Logic...'.
# Line 398 is 'try:'.
# Line 399 is 'user_photo_path = ...'
# The error says "expected an indented block after 'try' statement on line 398".
# This means line 399 is NOT indented relative to 398.

# Let's inspect line 398 indentation
try_line = lines[398]
indent_str_try = ""
for char in try_line:
    if char == ' ':
        indent_str_try += " "
    else:
        break

# The block inside try (399-401) needs to be indent_str_try + 4 spaces
block_indent_try = indent_str_try + "    "

start_idx = 399
end_idx = 402 # lines 399, 400, 401
for i in range(start_idx, end_idx):
    if i < len(lines):
        stripped = lines[i].lstrip()
        lines[i] = block_indent_try + stripped

# Also check 'except:' at 402?
# And block inside except at 403?

except_line = lines[402]
# except should align with try
lines[402] = indent_str_try + except_line.lstrip()

# inside except
lines[403] = block_indent_try + lines[403].lstrip()

with open('gesture_control.py', 'w') as f:
    f.writelines(lines)
