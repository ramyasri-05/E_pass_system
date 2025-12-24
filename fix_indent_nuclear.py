
import os

lines = []
with open('gesture_control.py', 'r') as f:
    lines = f.readlines()

# Line 369 (index 368) is 'filename = ...'
# This is inside 'if hand_landmarks:' -> 'if ...' -> 'if ...' ...
# Let's trust its indentation as the "Base for this block"
ref_line = lines[368]
base_indent = ""
for char in ref_line:
    if char == ' ':
        base_indent += " "
    elif char == '\t':
         base_indent += "\t"
    else:
        break

# Define indentation levels
i0 = base_indent
i1 = base_indent + "    "
i2 = base_indent + "        "
i3 = base_indent + "            "

# Construct specific lines for 370-440
new_block = []
new_block.append(f"{i0}is_duplicate = False\n")
new_block.append(f"{i0}if last_sent_screenshot_path and os.path.exists(last_sent_screenshot_path) and os.path.exists(new_filepath):\n")
new_block.append(f"{i1}img1 = read_safe(last_sent_screenshot_path)\n")
new_block.append(f"{i1}img2 = read_safe(new_filepath)\n")
new_block.append(f"{i1}if img1 is not None and img2 is not None and img1.shape == img2.shape:\n")
new_block.append(f"{i2}# Relaxed Comparison using MSE\n")
new_block.append(f"{i2}err = np.sum((img1.astype('float') - img2.astype('float')) ** 2)\n")
new_block.append(f"{i2}err /= float(img1.shape[0] * img1.shape[1])\n")
new_block.append(f"{i2}print(f'MSE: {{err}}')\n")
new_block.append(f"{i2}if err < 50:\n")
new_block.append(f"{i3}is_duplicate = True\n")
new_block.append(f"\n")
new_block.append(f"{i0}if is_duplicate:\n")
new_block.append(f"{i1}print('Duplicate Detected - Deleting File')\n")
new_block.append(f"{i1}set_server_message('Duplicate - Data Not Stored')\n")
new_block.append(f"{i1}cv2.putText(display_img, 'Duplicate - Data Not Stored', (w//2 - 250, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)\n")
new_block.append(f"{i1}try:\n")
new_block.append(f"{i2}if os.path.exists(new_filepath):\n")
new_block.append(f"{i3}os.remove(new_filepath)\n")
new_block.append(f"{i3}print(f'Deleted duplicate: {{new_filepath}}')\n")
new_block.append(f"{i1}except Exception as e:\n")
new_block.append(f"{i2}print(f'Error deleting duplicate: {{e}}')\n")
new_block.append(f"{i0}else:\n")
new_block.append(f"{i1}# New Logic: Save User Photo FIRST\n")
new_block.append(f"{i1}try:\n")
new_block.append(f"{i2}user_photo_path = os.path.join(os.path.dirname(__file__), 'static', 'screenshots', 'latest_user.jpg')\n")
new_block.append(f"{i2}cv2.imwrite(user_photo_path, img)\n")
new_block.append(f"{i2}print(f'User photo saved: {{user_photo_path}}')\n")
new_block.append(f"{i1}except Exception as e:\n")
new_block.append(f"{i2}print(f'Error saving user photo: {{e}}')\n")
new_block.append(f"\n")
new_block.append(f"{i1}print('Waiting 3s for UI update...')\n")
new_block.append(f"{i1}time.sleep(3)\n")
new_block.append(f"\n")
new_block.append(f"{i1}try:\n")
new_block.append(f"{i2}print('Retaking screenshot to capture updated UI...')\n")
new_block.append(f"{i2}if os.path.exists(new_filepath):\n")
new_block.append(f"{i3}os.remove(new_filepath)\n")
new_block.append(f"{i2}new_screenshot = pyautogui.screenshot()\n")
new_block.append(f"{i2}new_screenshot.save(new_filepath)\n")
new_block.append(f"{i2}print(f'Retaken screenshot saved: {{new_filepath}}')\n")
new_block.append(f"{i1}except Exception as e:\n")
new_block.append(f"{i2}print(f'Error retaking screenshot: {{e}}')\n")
new_block.append(f"\n")
new_block.append(f"{i1}requests.post(f'http://127.0.0.1:{{SERVER_PORT}}/update_state', json={{'filename': filename}})\n")
new_block.append(f"{i1}last_sent_screenshot_path = new_filepath\n")
new_block.append(f"{i1}set_server_message('Captured & Sent')\n")
new_block.append(f"{i1}notification_text = 'Screenshot Taken!'\n")
new_block.append(f"{i1}notification_end_time = time.time() + 2.0\n")

# Replace lines 370 to 440 (approximately)
# We need to find where the NEXT block starts to stop correctly.
# The next block starts with 'except Exception as e:' (line ~435 in original file)
# It closes the 'try:' block that started way back.

# Let's find index where line contains 'except Exception as e:' AND it has Outer Indentation.
# Or just replace a fixed range if we are confident.
# The previous view showed:
# 433:                                               except Exception as e:
# 434:                                               print(f"Error: {e}")

# This 'except' matches the 'try' at line 235 (guessing).
# Does it?
# In fix_indent_nuclear.py, I am replacing logic INSIDE the try block.
# So I should not overwrite the outer except.

start_index = 369 # This corresponds to line 370
# finding end index:
# Look for 'except Exception as e:' starting from 369
end_index = -1
for i in range(start_index, len(lines)):
    if "except Exception as e:" in lines[i]:
        # check indentation of this except
        # It should be LESS than base_indent?
        # base_indent is inside the try.
        # So yes, the except for the big try loop should be less indented.
        # But wait, base_indent was taken from line 368 which is inside the loop.
        # So the except for the loop should be far out.
        
        # But there was another 'except' at line 433...
        # 433:                                               except Exception as e:
        # 434:                                               print(f"Error: {e}")
        # This one seems to have indentation similar to base_indent?
        # If so, it closes a try started inside?
        
        # No, let's look at `view_file` (Step 830)
        # 390: try: (inside if is_duplicate)
        # ... except at 394.
        
        # The `except` at 433 (Step 426 view) seemed to close something big.
        # Let's assume lines 370-432 are what I want to replace.
        # And 433 is the `except`.
        end_index = i
        break

if end_index != -1:
    # Remove old lines
    del lines[start_index:end_index]
    # Insert new lines
    for line in reversed(new_block):
        lines.insert(start_index, line)

    with open('gesture_control.py', 'w') as f:
        f.writelines(lines)
else:
    print("Could not find end of block")
