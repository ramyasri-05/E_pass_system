
lines = []
with open('gesture_control.py', 'r') as f:
    lines = f.readlines()

# Line 360 (index 359) is 'elif ...' (Reference for else at 425)
# Line 366 (index 365) is 'try:' (Reference for except at 421)

indent_elif = ""
if len(lines) > 359:
    for char in lines[359]:
        if char == ' ':
            indent_elif += " "
        elif char == '\t':
             indent_elif += "\t"
        else:
            break

indent_try = ""
if len(lines) > 365:
    for char in lines[365]:
        if char == ' ':
            indent_try += " "
        elif char == '\t':
             indent_try += "\t"
        else:
            break

# Target lines:
# 421 (index 420) -> 'except Exception as e:' -> needs indent_try
# 422 (index 421) -> 'print...' -> needs indent_try + 4 spaces (or match style)

# 425 (index 424) -> 'else:' -> needs indent_elif
# 426-427 -> indent_elif + 4 spaces

# 428 (index 427) -> 'else:' (matches outer 'if'?)
# Wait, 428 'else:' is indented LESS than 425?
# In view_file:
# 425:                    else:
# 428:                 else:
# So 428 matches something outer. Leave it for now if it wasn't touched.

# Fix 421
if len(lines) > 420:
    lines[420] = indent_try + lines[420].lstrip()
# Fix 422
if len(lines) > 421:
    lines[421] = indent_try + "    " + lines[421].lstrip()

# Fix 425
if len(lines) > 424:
    lines[424] = indent_elif + lines[424].lstrip()
# Fix 426
if len(lines) > 425:
    lines[425] = indent_elif + "    " + lines[425].lstrip()
# Fix 427
if len(lines) > 426:
    lines[426] = indent_elif + "    " + lines[426].lstrip()

with open('gesture_control.py', 'w') as f:
    f.writelines(lines)
