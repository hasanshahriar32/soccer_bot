import cv2

print("Opening TCP Camera Stream at tcp://10.72.30.146:8000...")
cap = cv2.VideoCapture('tcp://10.72.30.146:8000')
print("Is cap opened:", cap.isOpened())

for i in range(5):
    ret, frame = cap.read()
    print(f"Frame {i} read:", ret, "Shape:" if ret else "", frame.shape if ret else "")

cap.release()
