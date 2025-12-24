import cv2
import mediapipe as mp
import time
import threading
import server
import requests
import numpy as np
from utils import get_local_ip, generate_qr, take_screenshot, select_file
from pynput import keyboard

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7, 
    max_num_hands=1
)
mp_draw = mp.solutions.drawing_utils

SERVER_PORT = 5000

# Global variable for selected file
pending_file = None
trigger_selection = False

def on_press(key):
    global trigger_selection
    try:
        if key.char == 's':
            trigger_selection = True
    except AttributeError:
        pass

def start_keyboard_listener():
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

def get_gesture(landmarks):
    """
    Returns 'FIST', 'INDEX', or 'OTHER'
    """
    # Check Extended Fingers
    index_extended = landmarks[8].y < landmarks[6].y
    middle_extended = landmarks[12].y < landmarks[10].y
    ring_extended = landmarks[16].y < landmarks[14].y
    pinky_extended = landmarks[20].y < landmarks[18].y
    
    # FIST: All folded (strict check)
    fist = (
        not index_extended and 
        not middle_extended and 
        not ring_extended and 
        not pinky_extended
    )
    
    if fist:
        return 'FIST'
    
    # INDEX: Only Index extended
    index_only = (
        index_extended and 
        not middle_extended and 
        not ring_extended and 
        not pinky_extended
    )
    
    if index_only:
        return 'INDEX'
        
    return 'OTHER'

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
    # Threshold for "Close Enough". > 12%
    return area > 0.12 

def check_connection_status():
    """
    Polls the server to check if a client has connected.
    """
    try:
        response = requests.get(f"http://127.0.0.1:{SERVER_PORT}/status")
        if response.status_code == 200:
            return response.json().get('connected', False)
    except:
        pass
    return False

def set_server_message(msg):
    """
    Sends a status message to the server to display on client.
    """
    try:
        requests.post(f"http://127.0.0.1:{SERVER_PORT}/set_message", json={"message": msg})
    except:
        pass

def main():
    global pending_file, trigger_selection
    
    server_thread = threading.Thread(target=server.start_server, daemon=True)
    server_thread.start()
    
    # Start Global Keyboard Listener
    start_keyboard_listener()
    
    ip = get_local_ip()
    connect_url = f"http://{ip}:{SERVER_PORT}/connect"
    print(f"Connection URL: {connect_url}")
    qr_path = generate_qr(connect_url, filename="connect_qr.png")
    
    cap = cv2.VideoCapture(0)
    
    # Cooldown & Timer Logic
    last_action_time = 0
    cooldown = 3.0
    
    gesture_start_time = 0
    current_stable_gesture = None
    HOLD_DURATION = 1.0 
    
    qr_img = cv2.imread(qr_path)
    if qr_img is not None:
        qr_img = cv2.resize(qr_img, (150, 150))
    
    print("System Running.")
    print("Press 's' to Select a File.")
    set_server_message("Scanning QR Code...")
    
    system_state = "SCANNING" 

    while True:
        # Check Global Hotkey Trigger
        if trigger_selection:
            trigger_selection = False
            print("Hotkey 's' pressed. Opening file dialog...")
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
        
        success, img = cap.read()
        if not success:
            break
            
        img = cv2.flip(img, 1)
        h, w, c = img.shape
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)
        
        current_time = time.time()
        
        # Check Connection State periodically
        if system_state == "SCANNING" and int(current_time) % 2 == 0:
             if check_connection_status():
                 system_state = "BACKGROUND"
                 msg = "System Ready. Waiting for Command."
                 print(msg)
                 set_server_message(msg)
                 cv2.destroyAllWindows()

        # Visualization ONLY if SCANNING
        display_img = None
        if system_state == "SCANNING":
            display_img = img.copy()
        
        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                
                # 1. Proximity Check
                if not is_hand_close(hand_lms.landmark, img.shape):
                    gesture_start_time = 0
                    current_stable_gesture = None
                    if system_state == "SCANNING":
                         cv2.putText(display_img, "Bring Hand Closer", (10, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    continue

                # 2. Get Gesture
                detected_gesture = get_gesture(hand_lms.landmark)
                
                # 3. Stability Timer
                if detected_gesture != "OTHER":
                    if detected_gesture == current_stable_gesture:
                        hold_time = current_time - gesture_start_time
                        
                        # Feedback if scanning
                        if system_state == "SCANNING":
                             pct = int((hold_time / HOLD_DURATION) * 100)
                             cv2.putText(display_img, f"{pct}%", (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                        
                        if hold_time > HOLD_DURATION:
                            # TRIGGER
                            if current_time - last_action_time > cooldown:
                                msg = ""
                                if detected_gesture == "INDEX" and pending_file is None:
                                    last_action_time = current_time 
                                    print("No File Selected. Opening Dialog form Gesture...")
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
                                        
                                elif pending_file:
                                    last_action_time = current_time
                                    msg = "Sending File..."
                                    set_server_message(msg)
                                    print(msg)
                                    try:
                                        requests.post(f"http://127.0.0.1:{SERVER_PORT}/update_state", json={"filepath": pending_file})
                                        pending_file = None
                                        # Delay slightly then reset message
                                        def reset_msg():
                                            time.sleep(2)
                                            set_server_message("File Sent. Ready.")
                                        threading.Thread(target=reset_msg, daemon=True).start()
                                    except Exception as e:
                                        print(e)
                                        
                                elif not pending_file and detected_gesture == "FIST":
                                     last_action_time = current_time
                                     msg = "Capturing Screenshot..."
                                     set_server_message(msg)
                                     print(msg)
                                     try:
                                         filename = take_screenshot()
                                         requests.post(f"http://127.0.0.1:{SERVER_PORT}/update_state", json={"filename": filename})
                                         def reset_msg():
                                            time.sleep(2)
                                            set_server_message("Screenshot Sent. Ready.")
                                         threading.Thread(target=reset_msg, daemon=True).start()
                                     except Exception as e:
                                         print(e)
                                
                                gesture_start_time = 0
                                current_stable_gesture = None
                                
                    else:
                        current_stable_gesture = detected_gesture
                        gesture_start_time = current_time
                else:
                    gesture_start_time = 0
                    current_stable_gesture = None


        if system_state == "SCANNING":
            # Overlay QR Code ONLY if Scanning
            if qr_img is not None:
                h_qr, w_qr, _ = qr_img.shape
                # Center
                x_offset = (w - w_qr) // 2
                y_offset = (h - h_qr) // 2
                if y_offset >= 0 and x_offset >= 0:
                    display_img[y_offset:y_offset+h_qr, x_offset:x_offset+w_qr] = qr_img

            cv2.imshow("Gesture Swap", display_img)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Handle standard key press if window is open
                trigger_selection = True # Defer to main loop handler

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
