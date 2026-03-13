import cv2
import numpy as np
from tensorflow import keras
import matplotlib.pyplot as plt
import math
from scipy.ndimage.measurements import center_of_mass
from preprocessing import preprocess_one_digit_area, process_answer_sheet

def read_preprocessed_blank(image, blank_scheme):
	# Загружаем предобученную модель (например, MNIST)
	model = keras.models.load_model('model/mnist1.h5')  # Укажите путь к вашей модели

	imwidth, imheight = blank_scheme['image_size']
	max_area = blank_scheme['max_area']
	w, h, mw, mh = blank_scheme['field_sizes']
	var_coords = blank_scheme['var_coords']
	problems_coords = blank_scheme['problems_coords']
	problems_coords = [var_coords] + problems_coords

	
	image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) # в чб
	
	image = cv2.resize(image, (imwidth, imheight)) # подгоняем размер под исходный размер бланка
	
#	cv2.imwrite('resized_image.jpeg', image)
	
	recognized_answers = []
	areas = []
	digits_all = []
	
	for problem_x, problem_y, fields_number in problems_coords:
		recognized_digits = []
		areas_digits = []
		digits = []
		for digit_index in range(fields_number):
			# Получаем прямоугольник вокруг цифры
			digit_x = problem_x + digit_index * (w + mw) + mw // 2
			digit_y = problem_y + mh // 2
			
			# Вырезаем цифру
			digit = image[digit_y : digit_y + h + mh, digit_x : digit_x + w + mw]
#			print(f'{digit_y} {digit_y + h + mh} {digit_x} {digit_x + w + mw}')
			digits.append(digit)
	
			digit = preprocess_one_digit_area(digit, 42, 28, sharpness = 1.1)
			
			areas_digits.append([digit_x, digit_y, w + mw, h + mh])
	
			if digit.max() == 0:
				recognized_digits.append(' ')
				digits.append(None)
				continue
				
#			processed = cv2.resize(digit, (w + mw, h + mh))
#			image[digit_y : digit_y + h + mh, digit_x : digit_x + w + mw] = processed
			
			# Подготовка к распознаванию
			digit = digit.astype('float32') / 255.0 # Нормировка на 1 (как в MNIST)
			digit = np.expand_dims(digit, axis=-1)  # Добавляем размерность канала
			
			# Распознаем
			prediction = model.predict(np.array([digit]))
			recognized_digit = np.argmax(prediction)
			if recognized_digit < 10:
				recognized_digits.append(str(recognized_digit))
			else:
				recognized_digits.append(',')
#			print(recognized_digits[-1])
				
		recognized_answers.append(recognized_digits)
		areas.append(areas_digits)
		digits_all.append(digits)
		
	colored = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
	
	return [colored, recognized_answers, areas, digits_all] # zero position in recognized_answers is variant number
	
	
#def generate_areas(image, blank_scheme):
#
#	imwidth, imheight = blank_scheme['image_size']
#	w, h, mw, mh = blank_scheme['field_sizes']
#	var_coords = blank_scheme['var_coords']
#	problems_coords = blank_scheme['problems_coords']
#	problems_coords = [var_coords] + problems_coords
#
#	
#	image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) # в чб
#	
#	image = cv2.resize(image, (imwidth, imheight)) # подгоняем размер под исходный размер бланка
#	
#	areas = []
#	
#	for problem_x, problem_y, fields_number in problems_coords:
#		areas_digits = []
#		for digit_index in range(fields_number):
#			# Получаем прямоугольник вокруг цифры
#			digit_x = problem_x + digit_index * (w + mw) + mw // 2
#			digit_y = problem_y + mh // 2
#			
#			areas_digits.append([digit_x, digit_y, w + mw, h + mh])
#	
#		areas.append(areas_digits)
#		
#	colored = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
#	
#	return [areas, colored] # zero position in recognized_answers is variant number


def print_areas_on_blank(image, blank_scheme):

	imwidth, imheight = blank_scheme['image_size']
	w, h, mw, mh = blank_scheme['field_sizes']
	var_coords = blank_scheme['var_coords']
	problems_coords = blank_scheme['problems_coords']
	problems_coords = [var_coords] + problems_coords
	
	image = cv2.resize(image, (imwidth, imheight)) # подгоняем размер под исходный размер бланка
	
	for problem_x, problem_y, fields_number in problems_coords:
		areas_digits = []
		for digit_index in range(fields_number):
			# Получаем прямоугольник вокруг цифры
			digit_x = problem_x + digit_index * (w + mw) + mw // 2
			digit_y = problem_y + mh // 2
			
			square = [digit_x, digit_y, w + mw, h + mh]
			cv2.rectangle(image, square, (255, 0, 255), 1)
			
	return image	

	
def print_ans_on_blank(temp_image, recognized_answers, areas):
#	problems_coords = blank_scheme['problems_coords']
	image = temp_image.copy()
	for problem_index in range(len(recognized_answers)):
		for digit_index in range(len(recognized_answers[problem_index])):
			square = areas[problem_index][digit_index]
			cv2.rectangle(image, square, (0, 255, 0), 1)
			cv2.putText(image, recognized_answers[problem_index][digit_index], [square[0] + square[2]//2, square[1] + square[3]], cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
	return image
	
	
def print_score_on_blank(temp_image, blank_scheme, score):
	rates_coords = blank_scheme['rates_coords']
	w, h, mw, mh = blank_scheme['field_sizes']
	image = temp_image.copy()
	for problem_index in range(len(score)):
		if score[problem_index][1]:
			color = (0, 150, 0)
		else:
			color = (0, 0, 255)
		square = [rates_coords[problem_index][0], rates_coords[problem_index][1]]
		cv2.putText(image, str(score[problem_index][0]), square, cv2.FONT_HERSHEY_SIMPLEX, 2, color, 3)
	return image