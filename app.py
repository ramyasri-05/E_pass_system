from flask import Flask, render_template, send_from_directory, abort, jsonify, request, Response
from datetime import datetime
import os
import threading
import time
import shutil
import cv2
import numpy as np
from utils import get_local_ip

app = Flask(__name__)
# reusing 'screenshots' dir for all shared files for simplicity, or we can rename it 'shared'
SHARED_DIR = os.path.join(os.path.dirname(__file__), 'static', 'screenshots')

# Ensure directory exists immediately
if not os.path.exists(SHARED_DIR):
    os.makedirs(SHARED_DIR, exist_ok=True)


# Global state
history = []
history_lock = threading.Lock()
client_connected = False

# Video Streaming State
latest_frame = None
frame_lock = threading.Lock()
is_captured = False # If True, show snapshot; if False, show video feed
capture_time = None # Formatted string of when the photo was taken
hud_message = ""
hud_message_expiry = 0
is_hand_detected = False

# Gesture-Triggered Shared Data
pending_data = None # Stores {name, rollno, status} until gesture commits it
history_lock = threading.Lock() # Reusing lock for simplicityto static image

# Manual Trigger State
manual_trigger = False
trigger_lock = threading.Lock()



@app.route('/')
def index():
    return "Gesture Swap Server is Running!"


@app.route('/connect')
def connect():
    return render_template('receiver.html')

@app.route('/form')
def form_page():
    return render_template('form.html')

@app.route('/submit_form', methods=['POST'])
def submit_form():
    # Using request.form for standard form submission
    if request.is_json:
        data = request.json
    else:
        data = request.form
        
    rollno = str(data.get('rollno')).upper()
    name = data.get('name')
    status = data.get('status')
    
    print(f"Received Submission - Roll No: {rollno}, Name: {name}, Status: {status}")
    
    # 5. STORE AS PENDING (NOT shared to receiver yet)
    global pending_data
    with history_lock:
        pending_data = {
            "type": "data",
            "name": name,
            "rollno": rollno,
            "status": status,
            "timestamp": time.time()
        }
    
    # Reset User Photo to Placeholder for new candidate
    try:
        placeholder_path = os.path.join(os.path.dirname(__file__), 'static', 'user_placeholder.png')
        target_path = os.path.join(SHARED_DIR, 'latest_user.jpg')
        if os.path.exists(placeholder_path):
            shutil.copy2(placeholder_path, target_path)
    except Exception as e:
        print(f"Error resetting user photo: {e}")
    
    # Reset Capture Flag so UI shows video again
    global is_captured
    is_captured = False
    


    # Format current date for E-Pass
    issued_date = datetime.now().strftime("%b %d, %Y")

    # Render the new E-Pass page with the submitted data
    return render_template('epass.html', rollno=rollno, name=name, status=status, issued_date=issued_date, timestamp=time.time())

@app.route('/poll')
def poll():
    global client_connected
    client_connected = True
    
    client_timestamp = request.args.get('timestamp', 0, type=float)
    
    new_files = []
    
    with history_lock:
        for item in history:
            if item["timestamp"] > client_timestamp:
                new_files.append(item)
    
    response = {
        "new": bool(new_files),
        "files": new_files
    }
    
    if new_files:
        response["latest_timestamp"] = new_files[-1]["timestamp"]
        
    return jsonify(response)

@app.route('/status')
def status():
    """Returns the server status, including client connection."""
    global is_captured, hud_message, hud_message_expiry, is_hand_detected
    
    # Clear expired hud_message
    if hud_message and time.time() > hud_message_expiry:
        hud_message = ""
        
    return jsonify({
        "connected": client_connected,
        "captured": is_captured,
        "capture_time": capture_time,
        "hud_message": hud_message,
        "is_hand_detected": is_hand_detected
    })

def generate_frames():
    global latest_frame
    while True:
        with frame_lock:
            if latest_frame is None:
                # Avoid busy-wait if no frame is available
                frame_available = False
            else:
                # Encode frame
                ret, buffer = cv2.imencode('.jpg', latest_frame)
                frame = buffer.tobytes()
                frame_available = True
            
        if not frame_available:
            time.sleep(0.1)
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        # Limit frame rate to ~25fps
        time.sleep(0.04)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_capture_flag', methods=['POST'])
def set_capture_flag():
    global is_captured, capture_time
    data = request.json
    is_captured = data.get('captured', False)
    capture_time = data.get('time') if is_captured else None
    return jsonify({"status": "success"})

@app.route('/update_hud', methods=['POST'])
def update_hud():
    global hud_message, hud_message_expiry, is_hand_detected
    data = request.json
    
    if "message" in data:
        hud_message = data.get("message")
        duration = data.get("duration", 3)
        hud_message_expiry = time.time() + duration
        
    if "is_hand_detected" in data:
        is_hand_detected = data.get("is_hand_detected")
        
    return jsonify({"status": "success"})

@app.route('/update_frame', methods=['POST'])
def update_frame():
    """ يسمح بتحديث الصورة من عملية خارجية """
    global latest_frame
    try:
        file = request.files.get('frame')
        if not file:
            return jsonify({"status": "error", "message": "No frame provided"}), 400
            
        # Decode image from buffer
        nparr = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is not None:
            with frame_lock:
                latest_frame = img
            return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "error", "message": "Failed to decode frame"}), 400

@app.route('/trigger_capture', methods=['POST'])
def trigger_capture():
    global manual_trigger
    with trigger_lock:
        manual_trigger = True
    return jsonify({"status": "triggered"})

@app.route('/has_pending')
def has_pending():
    global pending_data
    return jsonify({
        "data": pending_data is not None
    })

@app.route('/commit_pending_data', methods=['POST'])
def commit_pending_data():
    global pending_data
    with history_lock:
        if pending_data:
            history.append(pending_data)
            pending_data = None
            return jsonify({"status": "success", "message": "Data shared via gesture"})
    return jsonify({"status": "error", "message": "No pending data"}), 404

@app.route('/update_state', methods=['POST'])
def update_state():
    """
    Called by the gesture script. 
    Accepts 'filename' (if already in static) OR 'filepath' (absolute path to copy).
    """
    data = request.json
    filename = data.get('filename')
    filepath = data.get('filepath')
    
    final_filename = filename
    
    # If a full filepath is provided (selected file), copy it to static dir
    if filepath and os.path.exists(filepath):
        try:
            basename = os.path.basename(filepath)
            # Prepend timestamp to ensure uniqueness and order
            timestamp_str = str(int(time.time()))
            final_filename = f"{timestamp_str}_{basename}"
            destination = os.path.join(SHARED_DIR, final_filename)
            shutil.copy2(filepath, destination)
        except Exception as e:
            print(f"Error copying file: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    if final_filename:
        with history_lock:
            history.append({
                "type": "file",
                "filename": final_filename,
                "timestamp": time.time()
            })
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "No filename or filepath provided"}), 400

@app.route('/files/<filename>')
def serve_file(filename):
    # allow serving any file in the directory
    return send_from_directory(SHARED_DIR, filename, as_attachment=False)

def start_server():
    if not os.path.exists(SHARED_DIR):
        os.makedirs(SHARED_DIR)
        
    port = int(os.environ.get("PORT", 5000))
    ip = get_local_ip()
    print(f"Server starting on http://{ip}:{port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    start_server()
