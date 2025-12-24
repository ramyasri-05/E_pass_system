
lines = []
with open('gesture_control.py', 'r') as f:
    lines = f.readlines()

# Line 386 is 'if is_duplicate:'. Let's assume this is the source of truth.
ref_line = lines[385] # 0-indexed
indent_str = ""
for char in ref_line:
    if char == ' ':
        indent_str += " "
    else:
        break

# We need 'else:' at 396 to match 'indent_str'
# We need content inside else (397-434) to be 'indent_str' + 4 spaces
# We need content inside blocks within else (try/except) to be 'indent_str' + 8 spaces, etc.

# But wait, the content I pasted might have varying indentation. 
# Best approach: clean strip lines 396-434 and re-indent them based on their logical structure?
# That's hard to parse.

# Let's rely on the fact that I just pasted a block that WAS internally consistent (mostly 4 space steps).
# So I just need to shift the whole block (396-434) to match 'indent_str'.

# Get current indentation of line 396
current_else_line = lines[395]
current_else_indent = ""
for char in current_else_line:
    if char == ' ':
        current_else_indent += " "
    else:
        break

# Calculate offset
expected_len = len(indent_str)
current_len = len(current_else_indent)
diff = expected_len - current_len

# Apply offset to lines 396 to 434
start_idx = 395
end_idx = 434

for i in range(start_idx, end_idx):
    if i < len(lines):
        # We can't just add/subtract spaces blindy because empty lines might be just '\n'
        # or logic might be complicated.
        # But generally:
        line = lines[i]
        if not line.strip(): 
            continue # skip empty lines

        if diff > 0:
            lines[i] = (" " * diff) + line
        elif diff < 0:
            # remove spaces from start
            # check if it starts with enough spaces
            to_remove = abs(diff)
            if line.startswith(" " * to_remove):
                lines[i] = line[to_remove:]
            else:
                # Fallback: just lstrip and add expected indentation? No that flattens everything.
                pass 

with open('gesture_control.py', 'w') as f:
    f.writelines(lines)
