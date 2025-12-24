
try:
    import mediapipe as mp
    print("mediapipe imported")
    try:
        import mediapipe.solutions.face_detection
        print("mediapipe.solutions.face_detection imported directly")
    except ImportError as e:
        print(f"Direct import failed: {e}")
        
    try:
        print(f"mp.solutions: {mp.solutions}")
        print(f"mp.solutions.face_detection: {mp.solutions.face_detection}")
    except AttributeError as e:
        print(f"Access via mp failed: {e}")

except ImportError as e:
    print(f"mediapipe import failed: {e}")
