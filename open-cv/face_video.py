import cv2

cap = cv2.VideoCapture(0)

while True:
    _, frame = cap.read()

    video_flip = cv2.flip(frame,1)
    #cv2.imshow('Webcamera', frame)
    cv2.imshow('Webcamera edited', video_flip)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()