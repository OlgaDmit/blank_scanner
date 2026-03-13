import cv2
import sys
import glob

from preprocessing import process_answer_sheet
from blank_reader import read_preprocessed_blank, print_ans_on_blank, print_score_on_blank, print_areas_on_blank
from gui import ask_text_question, ask_multiple_choice_question
import os



def check(result, blank_scheme, current_path):
	var = ''.join(result[0]).strip(' ')
	filename = os.path.join(current_path, var + '.var')
	try:
		with open(filename, 'r') as f:
			correct = []
			for line in f:
				correct.append(line.strip())
	except Exception:
		print('AAAAA! No correct .var file! AAAAA!')
		print(f'file `{filename}` not found')
		return []
		
	if len(result) - 1 != len(correct):
		print('AAAAA! Incorrect length .var file! AAAAA!')
		sys.exit()
		
	check_keys = blank_scheme['check_keys']
	score = []
	
	for i in range(len(check_keys)):
		if check_keys[i]:
			ans = ''.join(result[i+1]).strip(' ')
			corr = correct[i]
			match check_keys[i]:
				case 1:
					if (ans == corr):
						score.append([1, True]) # second parameter - if max
					else:
						score.append([0, False])
				case 2: # table
					if len(ans) > len(corr):
						score.append([0, False])
						continue
					while len(ans) < len(corr):
						ans = ans + ' '
					counter = 0
					for j in range(len(corr)):
						if ans[j] != corr[j]:
							counter += 1
					if not counter:
						score.append([2, True])
					elif counter == 1:
						score.append([1, False])
					else:
						score.append([0, False])
				case 3: # set
					counter = 0
#					ans = "".join(set(ans)) # FIXME need to check
					for c in corr:
						if not (c in ans):
							counter += 1
					counter += len(ans) - len(corr) + counter
					if not counter:
						score.append([2, True])
					elif counter == 1:
						score.append([1, False])
					else:
						score.append([0, False])
	return score
	
	
	
def save_dataset(result, digits):
#	try:
	data_path = os.path.join('model', 'autosaved')
	for i in range(len(result)):
		for j in range(len(result[i])):
			if ( not (digits[i][j] is None) and (result[i][j] != ' ') ):
				path = os.path.join(data_path, str(result[i][j]))
				files = glob.glob(os.path.join(path, '*.jpg'))
				if (files):
					filenumbers = [int(i.split('/')[-1][:-4]) for i in files]
					last_num = sorted( filenumbers )[-1]
				else:
					last_num = -1
#				print(f'{result[i][j]} {last_num}')
				filename = str(last_num + 1) + '.jpg'
				path_new = os.path.join(path, filename)
				cv2.imwrite(path_new, digits[i][j])
#	except Exception:
#		print('Problems while adding data to dataset.\n')


def point_capture(event, x, y, flags, params):
	if event == cv2.EVENT_LBUTTONDOWN:
		image, result, score, areas, blank_scheme, current_path = params
		for i in range(len(result)):
			for j in range(len(result[i])):
				if ( (x > areas[i][j][0]) and (x < areas[i][j][0] + areas[i][j][2]) and (y > areas[i][j][1]) and (y < areas[i][j][1] + areas[i][j][3]) ):
					chosen = print_ans_on_blank(image, result, areas)
					cv2.rectangle(chosen, areas[i][j], (0, 165, 255), 3)
					cv2.imshow('Image', chosen)
					while (True):
						if (key := cv2.waitKey(1) & 0xFF) and (key < 255):
							if ( (key >= ord('0')) and (key <= ord('9')) or (key == ord(',')) or (key == ord(' ')) ):
								result[i][j] = chr(key)
								checked = print_ans_on_blank(image, result, areas)
								new_score = check(result, blank_scheme, current_path)
								if new_score:
									score.clear()
									for i in range(len(new_score)):
										score.append(new_score[i])
									final = print_score_on_blank(checked, blank_scheme, score)
								else:
									final = checked
								cv2.imshow('Image', final)
								return

							if ( key == 27 ):
								return
							elif (key == 13): 
								return
		print("Missclick") #FIXME
		
        
        

def process_frame(frame, blank_scheme, current_path, sharpness = 1):

#	frame = cv2.imread("saved_image.jpg") # FIXME
#	frame = cv2.imread("answer_sheet_template_filled.png") # FIXME

	flag, processed_image = process_answer_sheet(frame, sharpness = sharpness)
	
	cv2.destroyWindow('Video')
	if flag:
		image_to_show = print_areas_on_blank(processed_image, blank_scheme)
	else:
		image_to_show = processed_image
		
	cv2.imshow('Image', image_to_show)
	
	while(True):
		if (key := cv2.waitKey(1) & 0xFF ):
			if ( key == 27 ):
				return
			elif (key == 13): 
				break
			elif ( (key == 2) ):
				sharpness = sharpness * 9 / 10
				flag, processed_image = process_answer_sheet(frame, sharpness = sharpness)
				if flag:
					image_to_show = print_areas_on_blank(processed_image, blank_scheme)
				else:
					image_to_show = processed_image
				cv2.imshow('Image', image_to_show)
			elif (key == 3):
				sharpness = sharpness * 10 / 9
				flag, processed_image = process_answer_sheet(frame, sharpness = sharpness)
				if flag:
					image_to_show = print_areas_on_blank(processed_image, blank_scheme)
				else:
					image_to_show = processed_image
				cv2.imshow('Image', image_to_show)
	
	cutted_image, result, areas, digits = read_preprocessed_blank(processed_image, blank_scheme)
	
	checked = print_ans_on_blank(cutted_image, result, areas)
	score = check(result, blank_scheme, current_path)
	if score:
		final = print_score_on_blank(checked, blank_scheme, score)
	else:
		final = checked
	cv2.imshow('Image', final)
	
	cv2.setMouseCallback('Image', point_capture, [cutted_image, result, score, areas, blank_scheme, current_path])
	
	while(True):
		key = cv2.waitKey(1) & 0xFF
		if (key < 255):
			print(f'h{key}')
		if ( key == 27 ):
			return None, sharpness
		elif (key == 13): # ( (key == ord('`')) or (key == ord(']')) ):
			print('OK')
			save_dataset(result, digits)
			return score, sharpness