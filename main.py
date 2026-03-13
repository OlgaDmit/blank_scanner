import cv2
import sys
import os
import glob

from gui import ask_text_question, ask_multiple_choice_question
from process_frame import process_frame
from blank_reader import print_score_on_blank						
							

def save_result(score):
	for item in score:
		print(str(item[0]) + '\t', end = '')
	print('',flush=True)
	
def save_settings(path_arr, scaling, sharpness):
	x, y, w, h = scaling[:]
	with open('.blank_ocr_config', 'w') as f:
		f.write(f'scaling: {x} {y} {w} {h}\n')
		f.write(f'sharpness: {sharpness}\n')
		for line in path_arr:
			f.write(line)
	
def scale_image(key, x, y, w, h, original_sizes):
	if ( (key == 44) and (y > 0) ):
		y -= velocity
		if (y < 0):
			y = 0
	elif ( (key == 45) and (y+h < original_sizes[0]) ):
		y += velocity
		if (y+h > original_sizes[0]):
			y = original_sizes[0] - h
	elif ( (key == 41) and (x > 0) ):
		x -= velocity
		if (x < 0):
			x = 0
	elif ( (key == 43) and (x+w < original_sizes[1]) ):
		x += velocity
		if (x+w > original_sizes[1]):
			x = original_sizes[1] - w
	elif ( (key == 2) and (w > 1) ):
		x += w // 20
		y += h // 20
		w = w * 9 // 10
		h = h * 9 // 10
	elif (key == 3):
		w = w * 10 // 9
		h = h * 10 // 9
		x -= w // 18
		y -= h // 18
		while (x < 0):
			x += 1
		while (y < 0):
			y += 1
		while ( (x + w > original_sizes[1]) and (x > 0) ):
			x -= 1
		while ( (y + h > original_sizes[0]) and (y > 0) ):
			y -= 1
		if (x + w > original_sizes[1]) :
			w = original_sizes[1] - x
		if (y + h > original_sizes[0]):
			h = original_sizes[0] - y
	return [x, y, w, h]
	
	

if __name__ == "__main__":

	#-- Path handling
	
	scaling_read_flag = False
	path_arr = []
	current_path = None
	sharpness = 1
	try:
		with open('.blank_ocr_config', 'r') as f:
			for line in f:
				if ( line.startswith('scaling') ):
					x, y, w, h = map(int, line.split()[1:])
					scaling_read_flag = True
				elif ( line.startswith('sharpness') ):
					sharpness = float(line.split()[1])
				else:
					path = line.strip()
					if os.path.isdir(path):
						path_arr.append(path)
	except Exception:
		pass
	    
	
	if len(sys.argv) > 1:
		path = sys.argv[1]
		if os.path.isdir(path):
			if not (path in path_arr):
				path_arr.insert(0, path)
			current_path = path
			
	if not current_path:
		if path_arr:
			result = ask_multiple_choice_question("Выберите рабочую папку:", path_arr + ["Ввести новый путь"])
			if result < len(path_arr):
				current_path = path_arr[result]
		if not current_path:
			path = ask_text_question("Выбор рабочей папки", "Введите путь к рабочей папке:")
			while not os.path.isdir(path):
				path = ask_text_question("Выбор рабочей папки", "Введен некорректный путь. Пожалуйста, введите верный путь к рабочей папке:")
			current_path = path
			if not (current_path in path_arr):
				path_arr.insert(0, current_path)
		
		
	#-- Settings handling
	
	search_pattern = os.path.join(current_path, "*.set")
	config_files = glob.glob(search_pattern)
	
	if not config_files:
		sys.exit() #FIXME
	elif len(config_files) == 1:
		with open(config_files[0]) as f:
			path_to_blank_scheme = os.path.join(current_path, f.readline())
			if not os.path.isfile(path_to_blank_scheme):
				sys.exit() #FIXME
			blank_scheme = {}
			with open(path_to_blank_scheme) as g:
				blank_scheme['problems_names'] = g.readline().strip().split(' ')
				blank_scheme['rates'] = list(map(int, g.readline().strip().split(' ')))
				blank_scheme['check_keys'] = list(map(int, g.readline().strip().split(' ')))
				blank_scheme['image_size'] = list(map(int, g.readline().strip().split(' ')))
				blank_scheme['max_area'] = float(g.readline().strip())
				blank_scheme['field_sizes'] = list(map(int, g.readline().strip().split(' ')))
				blank_scheme['var_coords'] = list(map(int, g.readline().strip().split(' ')))
				blank_scheme['problems_coords'] = []
				blank_scheme['rates_coords'] = []
				for line in g:
					pre = list(map(int, line.strip().split(' ')))
					blank_scheme['problems_coords'].append(pre[:3])
					blank_scheme['rates_coords'].append(pre[3:])
			pass # FIXME here should be save method
	
	#-- Main loop
	
	cap = cv2.VideoCapture(0) # 0 for external camera,if mounted, and 1 for internal; or 0 for internal, if now external connected
	
	ret, frame = cap.read()
	original_sizes = frame.shape
	velocity = 10
	if scaling_read_flag and (x >= 0) and (y >= 0) and (x + w < original_sizes[1]) and (y + h < original_sizes[0]):
		pass # everything OK, scaling is set correctly
	else:
		x = 0
		y = 0
		w = original_sizes[1]
		h = w // 2
		velocity = 10
	
	while(True): 
	
		ret, frame = cap.read()
		
		frame = frame[y : y+h, x : x+w]
		cv2.imshow('Video', frame)
		
		if ( (key := cv2.waitKey(1) & 0xFF) and (key < 255) ):
			if ( key == 27 ):
				break
			elif (key == 13): 
				score, sharpness = process_frame(frame, blank_scheme, current_path, sharpness)
				save_settings(path_arr, [x, y, w, h], sharpness)
				cv2.destroyWindow('Image')
				if score:
					save_result(score)
			else:
				x, y, w, h = scale_image(key, x, y, w, h, original_sizes)
				save_settings(path_arr, [x, y, w, h], sharpness)
			
#			if (key < 255):
#				print(key)
						
	
	cap.release()
	cv2.destroyAllWindows()