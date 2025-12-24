# E-Pass Global Deployment Guide

This guide explains how to deploy the E-Pass system globally so it can be used by anyone, anywhere.

## 1. Cloud Deployment (Server)

The server handles the Web UI and API. We recommend using **Render.com**.

### Steps to Deploy to Render:
1.  **Push your code to GitHub**: (See Git Troubleshooting below).
2.  **Create a New Web Service** on Render.
3.  Connect your GitHub repository.
4.  Render will automatically use the `render.yaml` and `Procfile` provided.
5.  Once deployed, you will get a URL like `https://e-pass-system.onrender.com`.

## 2. Local Kiosk Setup (Python)

The local script runs on your PC to handle the webcam and screenshots.

### Configuration:
1.  Open `gesture_control.py`.
2.  Find the `SERVER_URL` variable at the top (Line 47).
3.  Change it from `http://127.0.0.1:5000` to your **Render URL**:
    ```python
    SERVER_URL = "https://your-app-name.onrender.com"
    ```

### Run the Kiosk:
1.  Run `python gesture_control.py` on your PC.
2.  It will now sync with the Cloud server.
3.  **QR Code**: The QR code shown on your PC will now point to the Cloud URL, so anyone can scan it and receive the E-Pass on their mobile data, anywhere in the world.

---

## Git Troubleshooting

If you see `error: src refspec main does not match any`, it means you haven't committed your changes yet.

Run these commands in order:
```bash
git add .
git commit -m "Setup global deployment"
git push -u origin main
```

## How it Works (Global Architecture)

*   **Cloud Server**: Hosts the receiver page, the form, and stores the shared data.
*   **Local Kiosk**: Captures the webcam feed, processes gestures, and "pushes" the data to the Cloud Server.
*   **End User**: Scans the QR code on the kiosk screen, which takes them to the Cloud URL to receive their E-Pass.
