import mediapipe
print(dir(mediapipe))
try:
    import mediapipe.solutions
    print("solutions imported")
except ImportError as e:
    print(f"Error importing solutions: {e}")
