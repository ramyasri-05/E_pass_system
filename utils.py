import socket
import qrcode
import os
from datetime import datetime

def get_local_ip():
    """
    Retrieves the local IP address of the machine.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def generate_qr(data, filename="qrcode.png"):
    """
    Generates a QR code for the given data and saves it.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        
    save_path = os.path.join(static_dir, filename)
    img.save(save_path)
    return save_path

def get_screenshot_buffer():
    """
    Captures the screen and returns it as an in-memory JPEG buffer.
    """
    import pyautogui
    from io import BytesIO
    import numpy as np
    import cv2
    
    screenshot = pyautogui.screenshot()
    # Convert PIL Image to BytesIO
    buffer = BytesIO()
    screenshot.save(buffer, format="JPEG", quality=70) # Compress for faster cloud upload
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.jpg"
    
    return buffer.getvalue(), filename

def take_screenshot(save_dir="static/screenshots"):
    # Keeping this for legacy/local mode if needed, but get_screenshot_buffer is preferred.

def select_file():
    """
    Opens a file dialog to select a file.
    Returns the absolute path of the selected file, or None.
    """
    import tkinter as tk
    from tkinter import filedialog
    
    root = tk.Tk()
    root.withdraw() # Hide the main window
    root.attributes('-topmost', True) # Bring to front
    
    file_path = filedialog.askopenfilename(
        title="Select File to Share",
        filetypes=[("All Files", "*.*")]
    )
    
    root.destroy()
    return file_path if file_path else None
