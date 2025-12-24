# How to Deploy E-Pass System to Render.com (Step-by-Step)

Follow these steps to make your system accessible from anywhere in the world.

## Phase 1: Force Update Your Code (Git)

The error you saw (`ModuleNotFoundError: No module named 'app'`) happened because Render couldn't find the entry point. I have renamed `server.py` to `app.py` to fix this.

**Run these commands to update your GitHub:**
1.  **Stage everything:**
    ```bash
    git add .
    ```
2.  **Commit:**
    ```bash
    git commit -m "Fix: Rename server to app for Render"
    ```
3.  **Push:**
    ```bash
    git push -u origin main
    ```

Once you push, Render will automatically detect the changes and start a new build.

---

## Phase 2: Deploy to Render (If not already created)

1.  **Sign Up/Login**: Go to [Render.com](https://render.com).
2.  **Create New Service**: Click **"New +"** -> **"Web Service"**.
3.  **Connect GitHub**: Select your `E_pass_system` repository.
4.  **Configuration**:
    *   **Name**: `e-pass-system`
    *   **Language**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn app:app` (This is the most important part!)
5.  **Plan**: Select **"Free"**.
6.  **Create**: Click **"Create Web Service"**.

---

## Phase 3: Final Connection

1.  **Wait for Build**: Wait for the "Live" message on Render.
2.  **Copy Your URL**: Find the link like `https://e-pass-system.onrender.com`.
3.  **Update Kiosk Script**: 
    *   Open `gesture_control.py`.
    *   Ensure line 47 has your Cloud URL:
    ```python
    SERVER_URL = "https://e-pass-system.onrender.com"
    ```
4.  **Run Locally**: Run `python gesture_control.py`.

---

## Troubleshooting "libGL" Error on Render
If the Render logs show an error about `libGL.so.1`, it means we need to use a "headless" version of OpenCV. 
1. Open `requirements.txt`.
2. Change `opencv-python` to `opencv-python-headless`.
3. Push to GitHub again.
