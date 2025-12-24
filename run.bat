@echo off
title E-Pass System Starter
echo Checking requirements...
pip install -r requirements.txt
echo.
echo Starting Gesture Control System...
python gesture_control.py
pause
