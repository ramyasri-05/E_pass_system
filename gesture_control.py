
import cv2
import mediapipe as mp
# import mediapipe.solutions.face_detection as mp_face_detection (Unavailable in Py3.13)
import time
from datetime import datetime
import threading
import app as server
import requests
import webbrowser
import numpy as np
import os
from utils import get_local_ip, generate_qr, get_screenshot_buffer, select_file
import pyautogui
from pynput import keyboard
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import ctypes

# Define connection indices for drawing hands (Standard MediaPipe connections)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),      # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),      # Index
    (5, 9), (9, 10), (10, 11), (11, 12), # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20), # Pinky
    (0, 17) # Wrist to Pinky base
]

def draw_landmarks(image, landmarks):
    h, w, c = image.shape
    
    # Convert normalized landmarks to pixel coordinates
    points = []
    for lm in landmarks:
        points.append((int(lm.x * w), int(lm.y * h)))
        
    # Draw connections
    for start_idx, end_idx in HAND_CONNECTIONS:
        if start_idx < len(points) and end_idx < len(points):
            cv2.line(image, points[start_idx], points[end_idx], (200, 200, 200), 2)
            
    # Draw points
    for pt in points:
        cv2.circle(image, pt, 4, (0, 255, 0), -1)

# SERVER CONFIGURATION
# Set this to your Cloud URL (e.g., https://e-pass-system.onrender.com)
SERVER_URL = "https://e-pass-system.onrender.com" 
SERVER_PORT = 5000 


# State Variables
pending_buffer = None
pending_filename = None
trigger_selection = False

def on_activate_selection():
    global trigger_selection
    trigger_selection = True

def start_keyboard_listener():
    # Detects <Alt> + <s> globally
    listener = keyboard.GlobalHotKeys({
        '<alt>+s': on_activate_selection
    })
    listener.start()



def is_hand_close(landmarks, img_shape):
    """
    Checks if hand is close enough to camera (based on bounding box).
    """
    h, w, c = img_shape
    x_min = min([lm.x for lm in landmarks])
    x_max = max([lm.x for lm in landmarks])
    y_min = min([lm.y for lm in landmarks])
    y_max = max([lm.y for lm in landmarks])
    
    bbox_w = x_max - x_min
    bbox_h = y_max - y_min
    
    area = bbox_w * bbox_h
    # Threshold for "Close Enough". Lowered to 0.10 for better sensitivity.
    return area > 0.10 

def is_duplicate(img_path1, img_path2):
    """
    Compares two images. Returns True if they are identical.
    """
    if not img_path1 or not img_path2: return False
    if not os.path.exists(img_path1) or not os.path.exists(img_path2): return False
    
    try:
        i1 = cv2.imread(img_path1)
        i2 = cv2.imread(img_path2)
        
        if i1.shape != i2.shape: return False
        
        # Simple bitwise difference
        difference = cv2.subtract(i1, i2)
        b, g, r = cv2.split(difference)
        
        if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
            return True
    except:
        pass
    return False

def is_hand_centered(landmarks, img_shape):
    """
    Checks if the hand centroid is within the middle 40% of the horizontal frame.
    """
    h, w, c = img_shape
    x_center = sum([lm.x for lm in landmarks]) / len(landmarks)
    # Target: 30% to 70% of screen width
    return 0.30 < x_center < 0.70
def check_connection_status():
    """
    Polls the server to check if a client has connected.
    """
    try:
        response = requests.get(f"{SERVER_URL}/status", timeout=1.0)

        if response.status_code == 200:
            return response.json().get('connected', False)
    except:
        pass
    return False

def set_server_message(msg):
    """
    Instructions are now displayed on the desktop overlay. 
    This function now only logs to console for debugging.
    """
    print(f"[SYSTEM]: {msg}")

def minimize_window(title):
    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, title)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 6) # 6 = SW_MINIMIZE
    except Exception as e:
        print(f"Window Minimize Error: {e}")

def main():
    global pending_buffer, pending_filename, trigger_selection
    
    # server_thread = threading.Thread(target=server.start_server, daemon=True)
    # server_thread.start()
    
    # Decide if we use local or global
    is_local = "127.0.0.1" in SERVER_URL or "localhost" in SERVER_URL

    if is_local:
        print("Starting Local Server...")
        server_thread = threading.Thread(target=server.start_server, daemon=True)
        server_thread.start()
        time.sleep(2) # Wait for local server
    
    # Start Global Keyboard Listener
    start_keyboard_listener()
    
    # Force Reset Server Connection State for new session
    current_sid = ""
    print("[SYSTEM] Attempting to reset server connection (Wait for Cloud Server)...")
    while True:
        try:
            r = requests.post(f"{SERVER_URL}/reset_connection", timeout=10.0)
            if r.status_code == 200:
                current_sid = r.json().get('sid', '')
                print(f"[SYSTEM] Connection Reset Successful. New Session ID: {current_sid}")
                break
            else:
                print(f"[WARNING] Server Error during reset: {r.status_code}. Retrying...")
        except requests.exceptions.Timeout:
            print("[WARNING] Reset Timed Out (Server might be waking up). Retrying...")
        except requests.exceptions.ConnectionError:
            print("[WARNING] Connection Error. Check internet. Retrying...")
        except Exception as e:
            print(f"[WARNING] Reset Failed: {e}. Retrying in 2s...")
        
        time.sleep(2.0)

    if is_local:
        ip = get_local_ip()
        connect_url = f"http://{ip}:{SERVER_PORT}/connect"
        if current_sid: connect_url += f"?sid={current_sid}"
        form_url = f"http://127.0.0.1:{SERVER_PORT}/form"
    else:
        connect_url = f"{SERVER_URL}/connect"
        if current_sid: connect_url += f"?sid={current_sid}"
        form_url = f"{SERVER_URL}/form"

    print(f"Connection URL: {connect_url}")
    qr_path = generate_qr(connect_url, filename="connect_qr.png")


    
    # Initialize HandLandmarker (Tasks API)
    base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(base_options=base_options,
                                           num_hands=1)
    detector = vision.HandLandmarker.create_from_options(options)

    # Use DSHOW on Windows for more stable/faster initialization
    print("[SYSTEM] Initializing Camera (DSHOW backend)...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    # Set Resolution for faster processing
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("ERROR: Could not open webcam via DSHOW. Retrying with default backend...")
        cap = cv2.VideoCapture(0)
        
    if not cap.isOpened():
        print("ERROR: Could not open webcam.")
        print("Please check if the camera is connected or used by another app.")
        return

    # Warm-up period: Read 10 frames to let the driver stabilize
    print("[SYSTEM] Camera Warm-up (reading initialization frames)...")
    for i in range(10):
        cap.read()
        time.sleep(0.05)

    # Cooldown & Timer Logic
    last_action_time = 0
    cooldown = 0.5 # Faster successive actions
    
    last_status_check_time = 0 # New variable to throttle server polling
    last_frame_push_time = 0   # New variable to throttle video uploads
    frame_push_lock = threading.Lock() # Ensure one upload at a time
    
    gesture_start_time = 0
    current_stable_gesture = None
    HOLD_DURATION = 0.5 # More intentional
    last_detected_time = 0 # Persistence buffer 
    
    # State for Duplicate Detection
    last_sent_screenshot_path = None 
    
    # Notification State
    notification_text = ""
    notification_end_time = 0
    last_hud_sync_time = 0
    
    # Helper to safe read images
    def read_safe(p):
        try:
            d = np.fromfile(p, dtype=np.uint8)
            return cv2.imdecode(d, cv2.IMREAD_COLOR)
        except: return None

    qr_img = read_safe(qr_path)
    if qr_img is not None:
        qr_img = cv2.resize(qr_img, (250, 250))
    
    print("System Running.")
    print("Press 'Alt+s' to Select a File.")
    set_server_message("Scanning QR Code...")
    
    system_state = "SCANNING"
    qr_decoder = cv2.QRCodeDetector() 

    # Flag to track if manual capture sequence needs to run
    should_run_capture = False 
    browser_opened = False
    pending_connection_actions = False
    connection_action_time = 0

    try:
        while True:
            try:
                current_time = time.time()
                # Re-check server state for HUD Accuracy (Throttled)
                if current_time - last_status_check_time > 0.5: # Sync every 0.5s instead of every frame
                    try:
                        r = requests.get(f"{SERVER_URL}/has_pending", timeout=0.5)
                        has_server_data = r.json().get('data', False)
                    except: has_server_data = False
                else:
                    try: has_server_data = has_server_data # Keep old value
                    except: has_server_data = False

                
                # Check Global Hotkey Trigger
                if trigger_selection:
                    trigger_selection = False
                    print("Hotkey 'Alt+s' pressed. Opening file dialog...")
                    set_server_message("Please Select a File on PC...")
                    try:
                        f = select_file()
                        if f:
                            pending_file = f
                            fname = f.split("/")[-1]
                            print(f"File Selected: {pending_file}")
                            set_server_message(f"Selected: {fname}")
                        else:
                            set_server_message("Selection Cancelled.")
                    except Exception as e:
                        print(e)


                # CHECK MANUAL TRIGGER (From E-Pass Click)
                try:
                    with server.trigger_lock:
                         if server.manual_trigger:
                             print("Manual Trigger Received!")
                             server.manual_trigger = False
                             should_run_capture = True
                except: pass

                # Camera reading moved inside loop but decoupled from QR display
                success = False
                img = None
                if system_state != "SCANNING":
                    for i in range(10):
                        success, img = cap.read()
                        if success: break
                        if i % 2 == 0:
                            print(f"[DEBUG] Camera Read Retry {i+1}/10...")
                        time.sleep(0.1)

                    if not success and system_state != "SCANNING":
                        print("[DEBUG] Camera Read Failed after 10 robust retries. Exiting loop.")
                        break
                else:
                    # In SCANNING mode, we try to read but don't exit if it fails
                    success, img = cap.read()
                    

                # hold_time is NO LONGER reset to 0 every frame
                # Instead, it persists unless hand is gone for more than 0.2s 
                if current_time - last_detected_time > 0.2:
                    hold_time = 0
                    gesture_start_time = 0
                    current_stable_gesture = None

                if img is None:
                    # Create black dummy image if camera read failed
                    img = np.zeros((480, 640, 3), dtype=np.uint8)
                    success = False
                
                if success:
                    img = cv2.flip(img, 1)
                
                h, w, c = img.shape
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Share frame with server for streaming
                try:
                    # Method 1: Same-process shared memory
                    with server.frame_lock:
                        server.latest_frame = img.copy()
                except: pass

                # Method 2: POST to server (Fallback/Multi-process support)
                # Stricter throttling for Cloud deployment (Max 2 FPS)
                if current_time - last_frame_push_time > 0.5: 
                     if frame_push_lock.acquire(blocking=False):
                        last_frame_push_time = current_time
                        def push_frame(frame):
                            try:
                                _, img_encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60]) # Lower quality for faster upload
                                requests.post(f"{SERVER_URL}/update_frame", 
                                             files={'frame': ('frame.jpg', img_encoded.tobytes(), 'image/jpeg')},
                                             timeout=1.0) # More generous timeout
                            except: pass
                            finally:
                                frame_push_lock.release()
                        
                        threading.Thread(target=push_frame, args=(img.copy(),), daemon=True).start()


                
                # Process with Tasks API (Only if we have a real image)
                is_hand_present = False
                if success:
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
                    detection_result = detector.detect(mp_image)
                    is_hand_present = bool(detection_result.hand_landmarks)
                
                current_time = time.time()
                
                # Check Connection State periodically (Throttled to every 2 seconds)
                if system_state == "SCANNING" and (current_time - last_status_check_time > 2.0):
                    last_status_check_time = current_time
                    if check_connection_status():
                         system_state = "CONNECTED" 
                         msg = "System Ready. Waiting for Command."
                         print(msg)
                         set_server_message(msg)
                         
                         # Trigger Browser and Minimize sequence
                         if not browser_opened:
                             pending_connection_actions = True
                             connection_action_time = current_time + 1.0 # 1s buffer

                # Visualization
                display_img = img.copy()
                
                # SCANNING MODE: Black Background, No Gestures
                if system_state == "SCANNING":
                    display_img[:] = 0 # Black background
                    
                    # Draw QR Code centered
                    if qr_img is not None:
                        h_qr, w_qr, _ = qr_img.shape
                        x_offset = (w - w_qr) // 2
                        y_offset = (h - h_qr) // 2
                        if y_offset >= 0 and x_offset >= 0:
                             display_img[y_offset:y_offset+h_qr, x_offset:x_offset+w_qr] = qr_img
                    # Status Text
                    if qr_img is not None:
                        # Text below QR Code
                        text_y = y_offset + h_qr + 40
                        cv2.putText(display_img, "Scan QR to Connect", (w//2 - 130, text_y), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    
                    # URL at the bottom
                    cv2.putText(display_img, f"Visit: {connect_url}", (20, h - 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

                    # Check for QR Codes (OpenCV) - Only if camera actually gave us a frame
                    if img is not None:
                        try:
                            # Use Grayscale for better detection
                            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                            data, bbox, _ = qr_decoder.detectAndDecode(gray_img)
                            
                            if data:
                                print(f"QR Code Detected: {data}")
                                system_state = "CONNECTED"
                                msg = "QR Verified. Connected."
                                print(msg)
                                set_server_message(msg)

                                # Trigger Browser and Minimize sequence
                                if not browser_opened:
                                    pending_connection_actions = True
                                    connection_action_time = current_time + 1.0
                        except Exception as e:
                            print(f"QR Error: {e}")
                    
                    cv2.putText(display_img, "Scan QR to Connect", (w//2 - 100, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    cv2.imshow("Gesture Swap", display_img)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("[DEBUG] 'q' pressed in SCANNING mode. Exiting.")
                        break
                    continue # SKIP Gesture Processing
                
                # EXECUTE PENDING ACTIONS (Minimized/Browser)
                if pending_connection_actions and current_time >= connection_action_time:
                    pending_connection_actions = False
                    print(f"Opening E-Pass Form: {SERVER_URL}/form")
                    webbrowser.open(f"{SERVER_URL}/form")
                    browser_opened = True
                    minimize_window("Gesture Swap")
                    print("[SYSTEM] Browser opened and window minimized.")

                # CONNECTED MODE: HUD is drawn at the end of the loop
                if system_state == "CONNECTED":
                     pass
                
                # SYNC HAND STATE TO WEB SERVER HUD
                if current_time - last_hud_sync_time > 0.1: # 10Hz sync
                    try:
                        requests.post(f"{SERVER_URL}/update_hud", 
                                      json={"is_hand_detected": is_hand_present}, timeout=0.05)
                        last_hud_sync_time = current_time
                    except: pass

                # Tasks API returns a list of NormalizedLandmark list, e.g. [[lm1, lm2...]]
                if detection_result.hand_landmarks:
                    for hand_lms in detection_result.hand_landmarks:
                        # Draw using custom function
                        draw_landmarks(display_img, hand_lms)
                        
                        # 1. Proximity and Centering Check
                        hand_close = is_hand_close(hand_lms, img.shape)
                        hand_centered = is_hand_centered(hand_lms, img.shape)
                        
                        if not hand_close:
                            gesture_start_time = 0
                            current_stable_gesture = None
                            msg = "BRING HAND CLOSER"
                            cv2.putText(display_img, msg, (10, h - 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                            # Web HUD Sync
                            try: requests.post(f"{SERVER_URL}/update_hud", json={"message": msg, "duration": 1})
                            except: pass
                            continue
                        
                        if not hand_centered:
                            gesture_start_time = 0
                            current_stable_gesture = None
                            msg = "CENTER YOUR HAND"
                            cv2.putText(display_img, msg, (10, h - 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                            # Web HUD Sync
                            try: requests.post(f"{SERVER_URL}/update_hud", json={"message": msg, "duration": 1})
                            except: pass
                            continue

                        # 2. Trigger by Position (Any hand is fine if correctly placed)
                        detected_gesture = "PROXIMITY" 
                        last_detected_time = current_time # Update persistence
                        
                        # 3. Stability Timer
                        if current_stable_gesture == "PROXIMITY":
                            hold_time = current_time - gesture_start_time
                            
                            # Feedback
                            pct = int((hold_time / HOLD_DURATION) * 100)
                            cv2.putText(display_img, f"{pct}%", (10, h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                            cv2.putText(display_img, "Triggering...", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
                            
                            if pct > 50:
                                    cv2.putText(display_img, "Ready...", (w//2 - 100, h//2 - 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)

                        else:
                            current_stable_gesture = "PROXIMITY"
                            gesture_start_time = current_time
                            hold_time = 0

                # GLOBAL TRIGGER CHECK (Manual or Gesture)
                trigger_active = False
                is_manual = False
                
                # Check Manual Trigger
                if should_run_capture:
                     trigger_active = True
                     is_manual = True
                     should_run_capture = False
                
                if hold_time > HOLD_DURATION:
                     trigger_active = True
                     is_manual = False


                
                if trigger_active:
                    # TRIGGER LOGIC
                    if is_manual or (current_time - last_action_time > cooldown):
                        msg = ""
                        
                        # 1. Manual Click (E-Pass Button) -> Capture Image
                        if is_manual:
                            last_action_time = current_time
                            
                            # 1. RESET TO LIVE FEED FIRST (So user can pose)
                            try:
                                requests.post(f"{SERVER_URL}/set_capture_flag", json={"captured": False})
                            except: pass
                            
                            msg = "GET READY! CAPTURING IN 1s..."
                            set_server_message(msg)
                            # Web HUD Sync
                            try: requests.post(f"{SERVER_URL}/update_hud", json={"message": msg, "duration": 2})
                            except: pass
                            print(msg)
                            
                            # 2. GIVE USER TIME TO POSE (Seeing live feed)
                            time.sleep(1.0)
                            
                            try:
                                buffer, filename = get_screenshot_buffer()
                                
                                # New Logic: Face Fit (Smart Crop)
                                try:
                                    # Capture NEW frame (Clean shot)
                                    ret_clean, clean_img = cap.read()
                                    if not ret_clean:
                                        clean_img = img.copy()
                                    else:
                                        clean_img = cv2.flip(clean_img, 1)
                                        
                                    # Update server feed
                                    with server.frame_lock:
                                        server.latest_frame = clean_img.copy()

                                    user_photo_path = os.path.join(os.path.dirname(__file__), "static", "screenshots", "latest_user.jpg")
                                    final_user_img = clean_img.copy()
                                        
                                    # Face Detection (More sensitive)
                                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
                                    gray_face = cv2.cvtColor(clean_img, cv2.COLOR_BGR2GRAY)
                                    faces = face_cascade.detectMultiScale(gray_face, 1.2, 5)
                                    ih, iw, _ = clean_img.shape
                                        
                                    if len(faces) > 0:
                                        # Pick the largest face detected
                                        faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
                                        (x, y, w_box, h_box) = faces[0]
                                            
                                        # Tighter Passport padding: 
                                        # face should be ~75% of the height
                                        y1 = max(0, int(y - 0.2 * h_box))
                                        y2 = min(ih, int(y + 1.2 * h_box))
                                        x1 = max(0, int(x - 0.25 * w_box))
                                        x2 = min(iw, int(x + 1.25 * w_box))
                                            
                                        # Enforce Passport Aspect Ratio (roughly 3.5:4.5)
                                        target_ratio = 4.5 / 3.5
                                        curr_w = x2 - x1
                                        curr_h = y2 - y1
                                            
                                        if curr_h / curr_w < target_ratio:
                                            # Box is too wide for passport
                                            needed_h = int(curr_w * target_ratio)
                                            diff = needed_h - curr_h
                                            y1 = max(0, y1 - diff // 2)
                                            y2 = min(ih, y1 + needed_h)
                                        else:
                                            # Box is too tall for passport
                                            needed_w = int(curr_h / target_ratio)
                                            diff = needed_w - curr_w
                                            x1 = max(0, x1 - diff // 2)
                                            x2 = min(iw, x1 + needed_w)
                                                
                                        final_user_img = clean_img[y1:y2, x1:x2]
                                        print('Face detected and cropped (Passport Style).')
                                    else:
                                        # Fallback: Tighter Center Crop
                                        print("No face detected. Using tighter center crop fallback.")
                                        cw, ch = iw // 2, ih // 2
                                        crop_h = int(ih * 0.75) # 75% height
                                        crop_w = int(crop_h / (4.5/3.5))
                                        y1, y2 = max(0, ch - int(crop_h * 0.6)), min(ih, ch + int(crop_h * 0.4)) # Shift up slightly
                                        x1, x2 = max(0, cw - crop_w // 2), min(iw, cw + crop_w // 2)
                                        final_user_img = clean_img[y1:y2, x1:x2]

                                    cv2.imwrite(user_photo_path, final_user_img)
                                        
                                    # Signal Frontend with current Time
                                    now = datetime.now()
                                    time_str = now.strftime("%b %d, %I:%M %p")
                                    requests.post(f"{SERVER_URL}/set_capture_flag", 
                                                  json={"captured": True, "time": time_str})
                                        
                                    print("Waiting 3s for UI update...")
                                    time.sleep(3)
                                        
                                    # Retake UI Screenshot (Now In-Memory)
                                    buffer, filename = get_screenshot_buffer()
                                        
                                    pending_buffer = buffer
                                    pending_filename = filename
                                    notification_text = "Captured. Gesture to Send."
                                    set_server_message("Captured. Gesture to Send.")
                                    # Web HUD Update
                                    requests.post(f"{SERVER_URL}/update_hud", 
                                                  json={"message": "READY TO SEND", "duration": 4})
                                    notification_end_time = time.time() + 3.0
                                except Exception as e:
                                    print(f"Capture Error: {e}")
                            except Exception as e:
                                print(f"Global Trigger Error: {e}")
                        
                        # 2. Gesture Proximity (Hand) -> Capture OR Share
                        elif not is_manual:
                            last_action_time = current_time
                            
                            # Re-check server state precisely at trigger time
                            try:
                                r = requests.get(f"{SERVER_URL}/has_pending")
                                has_server_data = r.json().get('data', False)
                            except: has_server_data = False

                            if pending_buffer or has_server_data:
                                # CASE 1: Something is pending -> SHARE IT
                                msg = "Sharing to Mobile via Gesture..."
                                set_server_message(msg)
                                print(msg)
                                
                                def share_func(buffer, filename, send_data):
                                    try:
                                        if buffer:
                                            requests.post(f"{SERVER_URL}/update_state", 
                                                         files={'file': (filename, buffer, 'image/jpeg')}, 
                                                         timeout=10)
                                            time.sleep(1)
                                        if send_data:
                                            requests.post(f"{SERVER_URL}/commit_pending_data", timeout=5)
                                            time.sleep(1)
                                        set_server_message("SENDED SUCCESSFULLY")
                                        # Web HUD Update
                                        requests.post(f"{SERVER_URL}/update_hud", 
                                                      json={"message": "FILE SUCCESSFULLY SEND", "duration": 4})
                                    except Exception as e:
                                        print(f"Sharing Error: {e}")
                                
                                threading.Thread(target=share_func, 
                                                 args=(pending_buffer, pending_filename, has_server_data), 
                                                 daemon=True).start()
                                
                                pending_buffer = None
                                pending_filename = None
                                notification_text = "SENDED SUCCESSFULLY"
                                set_server_message("SENDED SUCCESSFULLY")
                                notification_end_time = time.time() + 3.0
                            else:
                                # CASE 2: Nothing pending -> CAPTURE CURRENT SCREEN (IN-MEMORY)
                                msg = "Capturing Full Screen..."
                                set_server_message(msg)
                                print(msg)
                                try:
                                    buffer, filename = get_screenshot_buffer()
                                    
                                    # Skip duplicate detection for now to prioritize "Real Time" simplicity
                                    pending_buffer = buffer
                                    pending_filename = filename
                                    notification_text = "READY TO SEND"
                                    set_server_message("READY TO SEND")
                                    # Web HUD Update
                                    requests.post(f"{SERVER_URL}/update_hud", 
                                                  json={"message": "READY TO SEND", "duration": 5})
                                    notification_end_time = time.time() + 3.0
                                except Exception as e:
                                    print(f"Universal Capture Error: {e}")
                

                            
                cv2.imshow("Gesture Swap", display_img)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("[DEBUG] 'q' pressed in CONNECTED mode. Exiting.")
                    break
            
            except Exception as e:
                print(f"[CRITICAL ERROR] Crash in main loop: {e}")
                import traceback
                traceback.print_exc()
                break # Break loop on crash to allow finally block

    except KeyboardInterrupt:
        print("\n[SYSTEM] Ctrl+C detected. Shutting down...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[SYSTEM] Cleanup complete. Goodbye.")
        os._exit(0) # Force exit to kill daemon threads

if __name__ == "__main__":
    main()
