import cv2
import numpy as np

img = cv2.imread('saved_image.jpg')
img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
img0 = img.copy()

cv2.imshow('Image', img)

while(True): 
	if (key := cv2.waitKey(1) & 0xFF):
		if ( key == 27 ) or (key == 13):
			break

#kernel = np.ones((3,3), np.uint8)
#img1 = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel, iterations=1)
#
#cv2.imshow('Image', img1)
#
#while(True): 
#	if (key := cv2.waitKey(1) & 0xFF):
#		if ( key == 27 ) or (key == 13):
#			break

mean_brightness = cv2.mean(img)[0]
_, img = cv2.threshold(img, mean_brightness / 2, 255, cv2.THRESH_BINARY)

cv2.imshow('Image', img)

#while(True): 
#	if (key := cv2.waitKey(1) & 0xFF):
#		if ( key == 27 ) or (key == 13):
#			break
#
#mean_brightness = cv2.mean(img1)[0]
#_, img1 = cv2.threshold(img1, mean_brightness / 1.05, 255, cv2.THRESH_BINARY)
#
#cv2.imshow('Image', img1)

while(True): 
	if (key := cv2.waitKey(1) & 0xFF):
		if ( key == 27 ) or (key == 13):
			break

img = cv2.bitwise_not(img)

contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
colored = cv2.cvtColor(img0, cv2.COLOR_GRAY2RGB)

for cnt in contours:
	cv2.drawContours(colored, [cnt], -1, [0, 255, 0], 1)
	
cv2.imshow('Image', colored)

while(True): 
	if (key := cv2.waitKey(1) & 0xFF):
		if ( key == 27 ) or (key == 13):
			break


#import cv2
#from preprocessing import process_answer_sheet
#img = cv2.imread('saved_image.jpg')
#flag, img1 = process_answer_sheet(img)
#cv2.imshow('Image', img1)
#
#while(True): 
#	if (key := cv2.waitKey(1) & 0xFF):
#		if ( key == 27 ) or (key == 13):
#			break