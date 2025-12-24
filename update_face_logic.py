
import os

lines = []
with open('gesture_control.py', 'r') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

target_start = "# New Logic: Save User Photo FIRST"
target_end_marker = "print('Waiting 3s for UI update...')"

for i, line in enumerate(lines):
    if target_start in line:
        start_idx = i
    if target_end_marker in line: # This is AFTER the block
        end_idx = i
        break # Found the end of the gap we want to fill? 
        # Actually the block ends at 'except ... print ...' before this line.

if start_idx != -1 and end_idx != -1:
    # We want to keep indentation of start_idx
    indent = lines[start_idx][:lines[start_idx].find(target_start)]
    
    # New content
    new_lines = []
    new_lines.append(f"{indent}# New Logic: Face Fit (Smart Crop)\n")
    new_lines.append(f"{indent}try:\n")
    new_lines.append(f"{indent}    user_photo_path = os.path.join(os.path.dirname(__file__), 'static', 'screenshots', 'latest_user.jpg')\n")
    new_lines.append(f"{indent}    final_user_img = img.copy()\n")
    new_lines.append(f"{indent}    \n")
    new_lines.append(f"{indent}    # Face Detection\n")
    new_lines.append(f"{indent}    with mp_face_detection.FaceDetection(min_detection_confidence=0.5) as face_detection:\n")
    new_lines.append(f"{indent}        results = face_detection.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))\n")
    new_lines.append(f"{indent}        if results.detections:\n")
    new_lines.append(f"{indent}            detection = results.detections[0]\n")
    new_lines.append(f"{indent}            bboxC = detection.location_data.relative_bounding_box\n")
    new_lines.append(f"{indent}            ih, iw, _ = img.shape\n")
    new_lines.append(f"{indent}            x, y, w_box, h_box = int(bboxC.xmin * iw), int(bboxC.ymin * ih), int(bboxC.width * iw), int(bboxC.height * ih)\n")
    new_lines.append(f"{indent}            \n")
    new_lines.append(f"{indent}            # Expand Box (Padding)\n")
    new_lines.append(f"{indent}            pad_w = int(w_box * 0.5)\n")
    new_lines.append(f"{indent}            pad_h = int(h_box * 0.5)\n")
    new_lines.append(f"{indent}            \n")
    new_lines.append(f"{indent}            y1 = max(0, y - pad_h)\n")
    new_lines.append(f"{indent}            y2 = min(ih, y + h_box + pad_h)\n")
    new_lines.append(f"{indent}            x1 = max(0, x - pad_w)\n")
    new_lines.append(f"{indent}            x2 = min(iw, x + w_box + pad_w)\n")
    new_lines.append(f"{indent}            \n")
    new_lines.append(f"{indent}            # Make Square-ish\n")
    new_lines.append(f"{indent}            crop_h = y2 - y1\n")
    new_lines.append(f"{indent}            crop_w = x2 - x1\n")
    new_lines.append(f"{indent}            \n")
    new_lines.append(f"{indent}            if crop_h > crop_w:\n")
    new_lines.append(f"{indent}                diff = crop_h - crop_w\n")
    new_lines.append(f"{indent}                x1 = max(0, x1 - diff // 2)\n")
    new_lines.append(f"{indent}                x2 = min(iw, x2 + diff // 2)\n")
    new_lines.append(f"{indent}            else:\n")
    new_lines.append(f"{indent}                diff = crop_w - crop_h\n")
    new_lines.append(f"{indent}                y1 = max(0, y1 - diff // 2)\n")
    new_lines.append(f"{indent}                y2 = min(ih, y2 + diff // 2)\n")
    new_lines.append(f"{indent}                \n")
    new_lines.append(f"{indent}            final_user_img = img[y1:y2, x1:x2]\n")
    new_lines.append(f"{indent}            print('Face detected and cropped.')\n")
    new_lines.append(f"{indent}    \n")
    new_lines.append(f"{indent}    cv2.imwrite(user_photo_path, final_user_img)\n")
    new_lines.append(f"{indent}    print(f'User photo saved: {{user_photo_path}}')\n")
    new_lines.append(f"{indent}except Exception as e:\n")
    new_lines.append(f"{indent}    print(f'Error saving user photo: {{e}}')\n")
    new_lines.append(f"\n")

    # We replace from start_idx up to end_idx - 1 (because end_idx is the 'Waiting' line)
    # But wait, the 'except' block was ending at line 417, and 'Waiting' was at 419.
    # There was a blank line at 418.
    
    # Effectively we define the replacement to include the whole try/except block.
    # So we delete lines start_idx to end_idx (exclusive of end_idx)
    # And check if the last deleted line was empty?
    
    # Just careful about the end.
    # The new_lines include '\n' at the end.
    
    del lines[start_idx:end_idx]
    for line in reversed(new_lines):
        lines.insert(start_idx, line)
    
    with open('gesture_control.py', 'w') as f:
        f.writelines(lines)
    print("Updated successfully.")

else:
    print("Could not find markers.")
