import cv2
import sys


#    ^ Use capital T here if using Python 2.7

from preprocessing import process_answer_sheet
from blank_reader import read_preprocessed_blank


def point_capture(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Coordinate of Image: ({x}, {y})")
        cv2.putText(image, f'({x}, {y})', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow('TechVidvan', image)










				


if __name__ == "__main__":

	if len(sys.argv) > 1:
		path = sys.argv[1]
	else:
		path = ask_text_question("Title", "Пожалуйста, введите путь к рабочей папке:")
		
	

	result = ask_multiple_choice_question(
	    "What is your favorite color?",
	    [
	        "Blue!",
	        "No -- Yellow!",
	        "Aaaaargh!"
	    ]
	)
	
	print("User's response was: {}".format(repr(result)))
	
	
	
	while(True): 
		ret, frame = cap.read()
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		cv2.imshow('Video', frame)
		# cv2.imshow('frame',gray)
		if (key := cv2.waitKey(1)  & 0xFF):
			if ( key == 27 ):
				break
			elif (key == 13): #ord('/')):
				result = process_frame(frame)
				if result:
					print('\n'.join([''.join(i) for i in result]))
				
				
				
				
				
				
	
	cap.release()
	cv2.destroyAllWindows()






        
imagge = cv2.imread("heatmap_R_vs_phi_E__w_Xperiod_508_ratio_0.56_nTa2O5_2.16_dX_1.5_dhBN_9.png")
cv2.imshow("TechVidvan", imagge)
cv2.setMouseCallback('TechVidvan', point_capture)
cv2.waitKey(0)
cv2.destroyAllWindows()