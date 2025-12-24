import cv2
print(cv2.__version__)
try:
    path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    clf = cv2.CascadeClassifier(path)
    if clf.empty():
        print("Classifier empty")
    else:
        print("Classifier loaded")
except Exception as e:
    print(e)
