
lines = []
with open('gesture_control.py', 'r') as f:
    lines = f.readlines()

# Line 370 (index 369) is 'is_duplicate = False'. Its indentation is correct scope-wise.
ref_line = lines[369] 
base_indent = ""
for char in ref_line:
    if char == ' ':
        base_indent += " "
    else:
        break

# We want line 386 (index 385) 'if is_duplicate:' to have base_indent
# We want line 396 (index 395) 'else:' to have base_indent

# And their contents to be base_indent + 4 spaces
block_indent = base_indent + "    "
# And nested to be base_indent + 8 spaces
nested_indent = base_indent + "        "

# Apply to 386
lines[385] = base_indent + lines[385].lstrip()

# Apply to 387-395 (content of if)
start_if = 386
end_if = 395
for i in range(start_if, end_if):
    if i < len(lines):
        stripped = lines[i].lstrip()
        if stripped:
            lines[i] = block_indent + stripped

# Apply to 396 (else)
lines[395] = base_indent + lines[395].lstrip()

# Apply to 397-434 (content of else)
# This is tricky because it has nested blocks (try/except)
# We need to preserve relative indentation if possible, OR just hardcode it.

# Let's hardcode the structure because I know it.
start_else = 396
end_else = 435 # approximate
# Content of else starts at 397.

for i in range(start_else, end_else):
    if i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if not stripped: continue

        # Identify nested levels
        # try/except/if inside else -> nested_indent
        # simple statements inside else -> block_indent
        
        # This detection is simple but might work for this block
        if stripped.startswith("try:") or stripped.startswith("except") or stripped.startswith("if ") or stripped.startswith("else:") or stripped.startswith("requests") or stripped.startswith("last_sent") or stripped.startswith("set_server") or stripped.startswith("notification") or stripped.startswith("#") or stripped.startswith("print"):
             # These are mostly at block level inside else? NO.
             # try/except ARE nested? No, try is statement at block level.
             # requests is statement at block level.
             
             # Wait. 'try:' IS a block starter. It is at block_indent.
             # Its content logic is at nested_indent.
             pass
        
        # Okay, simpler:
        # Re-construct the block logic? No, too risky.
        
        # Just use the fact that lines I pasted were relative.
        # If I pasted them with 43 spaces base...
        # And now base_indent might be 43.
        # Then they are ALREADY correct relative to each other?
        # Maybe.
        
        # Let's just Apply base_indent to the 'if' and 'else' lines ONLY first.
        # And Assume relative indentation of their bodies follows?
        # No, if I shift parent, I must shift children.
        
        # Just Fix 386 and 396 to match 369.
        # And shift everything in between by the (New - Old) offset.
        pass

# Strategy: Calculate offset on line 386 and apply to 386-435
current_386 = lines[385]
current_indent_386 = ""
for char in current_386:
    if char == ' ':
        current_indent_386 += " "
    else:
        break
        
diff = len(base_indent) - len(current_indent_386)

start_idx = 385
end_idx = 435 # inclusive of block

for i in range(start_idx, end_idx):
    if i < len(lines):
        line = lines[i]
        if not line.strip(): continue # touch only non-empty
        
        if diff > 0:
            lines[i] = (" " * diff) + line
        elif diff < 0:
             # removal
             # Be careful not to strip essential indentation
             current = len(line) - len(line.lstrip())
             if current >= abs(diff):
                 lines[i] = line[abs(diff):]
             
with open('gesture_control.py', 'w') as f:
    f.writelines(lines)
