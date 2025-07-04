import cv2

cap = cv2.VideoCapture("/Users/behruz/Developer/bootcamp/open-cv/videos/nature.mp4")

while True:
    _, frame = cap.read()

    frame_video_size = cv2.resize(frame, (500,300))
    frame_video = cv2.cvtColor(frame_video_size, cv2.COLOR_BGRA2RGBA)
    cv2.imshow("Nature Video", frame_video_size)
    cv2.imshow("Nature Video edited", frame_video)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

