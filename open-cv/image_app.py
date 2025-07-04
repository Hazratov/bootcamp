import cv2

image = cv2.imread("/Users/behruz/Developer/bootcamp/open-cv/images/download.jpeg")

cv2.imshow("Frame", image)

image_flip = cv2.flip(image,1)
cv2.imshow("Flip Image", image_flip)


cv2.waitKey(0)

