import math
import numpy as np
from scipy.ndimage.measurements import center_of_mass
import cv2
from matplotlib import pyplot as plt


def process_answer_sheet(img, max_area_percentage = 0.002, sharpness = 1):
	# 1. Загрузка изображения с обработкой возможных теней
#	img = cv2.imread(image_path)
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	
	# 2. Улучшение контраста и уменьшение теней --- не нужно
#	clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
#	enhanced = clahe.apply(gray)
	
	# 3. Адаптивная бинаризация для компенсации неравномерного освещения --- вообще не нужно этой адаптивности, квадраты и так достаточно черные
#	binary = cv2.adaptiveThreshold(enhanced, 100, 
#	                              cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
#	                              cv2.THRESH_BINARY_INV, 11, 2)
	
	# 4. Удаление мелких шумов --- тоже не нужно 
#	kernel = np.ones((3,3), np.uint8)
#	processed = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

	# Бинаризация
	mean_brightness = cv2.mean(gray)[0]
	_, binary = cv2.threshold(gray, mean_brightness / sharpness, 255, cv2.THRESH_BINARY)
	
	# Инвертируем изображение, чтобы искать белые квадраты
	inverted = cv2.bitwise_not(binary)
	
	# 5. Поиск маркерных квадратов по углам
	contours, _ = cv2.findContours(inverted, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	
	#    for cnt in contours:
	#    	x,y,w,h = cv2.boundingRect(cnt)
	#    	print(x,y, '\n')
	
	# Фильтрация по площади (0.15-0.25% от общей площади)
	total_area = img.shape[0] * img.shape[1]
	max_area_percentage
	max_area = max_area_percentage * total_area
	min_area = max_area / 4
	max_brightness = mean_brightness / 2
#	print('Bright', max_brightness)
	
	corner_squares = []
	cont = []
	for cnt in contours:
		mask = np.zeros_like(gray)
		cv2.drawContours(mask, [cnt], -1, 255, -1)
		mean_brightness = cv2.mean(gray, mask=mask)[0]
		if mean_brightness < max_brightness:
			area = cv2.contourArea(cnt)
			if min_area < area < max_area:
				x,y,w,h = cv2.boundingRect(cnt)
				aspect_ratio = float(w)/h
				if 0.7 < aspect_ratio < 1.4:  # Проверка на квадратность
					corner_squares.append((x, y, w, h))
					cont.append(cnt)
	            
#	for cnt in cont:
#		x,y,w,h = cv2.boundingRect(cnt) #cnt[:] #
#		mask = np.zeros_like(processed)
#		cv2.drawContours(mask, [cnt], -1, 255, -1)
#		mean_brightness = cv2.mean(enhanced, mask=mask)[0]
#		print(x,y,w,h, mean_brightness)
	#		if mean_brightness < max_brightness:
	#			print(mean_brightness)
	
	# 6. Если найдено 4 квадрата, определяем углы бланка
	if len(corner_squares) == 4:
		# Сортируем квадраты: левый верхний, правый верхний, правый нижний, левый нижний
		corner_squares.sort(key=lambda s: (s[1], s[0]))
		top_squares = sorted(corner_squares[:2], key=lambda s: s[0])
		bottom_squares = sorted(corner_squares[2:], key=lambda s: s[0])
		ordered_squares = top_squares + bottom_squares
		
		src_points = np.float32([
			[ordered_squares[0][0], ordered_squares[0][1]],
			[ordered_squares[1][0] + ordered_squares[1][2], ordered_squares[1][1]],
			[ordered_squares[2][0], ordered_squares[2][1] + ordered_squares[2][3]],
			[ordered_squares[3][0] + ordered_squares[3][2], ordered_squares[3][1] + ordered_squares[3][3
			]]
		])
		
		# 7. Перспективная коррекция с учетом возможной трапециевидности
		# Вычисляем ширину и высоту выходного изображения
		width = max(
		    int(np.linalg.norm(src_points[1] - src_points[0])),
		    int(np.linalg.norm(src_points[3] - src_points[2])) )
		height = max(
		    int(np.linalg.norm(src_points[2] - src_points[0])),
		    int(np.linalg.norm(src_points[3] - src_points[1])))
		    
		
		dst_points = np.float32([
		    [0, 0],
		    [width, 0],
		    [0, height],
		    [width, height]
		])
		
		# Вычисляем матрицу преобразования и применяем ее
		matrix = cv2.getPerspectiveTransform(src_points, dst_points)
		result = cv2.warpPerspective(img, matrix, (width, height))
		
		return [1, result]
	
	# Если не найдено 4 квадрата, возвращаем обработанное изображение без перспективной коррекции
	
#	colored = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
	colored = cv2.cvtColor(inverted, cv2.COLOR_GRAY2RGB)
	
#	for cnt in corner_squares:
#		cv2.rectangle(colored, [cnt[0], cnt[1]], [cnt[0] + cnt[2], cnt[1] + cnt[3]], [0, 255, 0], 1)
		
	for cnt in cont:
		cv2.drawContours(colored, [cnt], -1, [0, 255, 0], 1)
	
	return [0, colored]
	


def cut_black_borders(image):
	# Обрезка черных краев
	if np.sum(image) == 0:
		return []
	while np.sum(image[0]) == 0:
		image = image[1:]
	while np.sum(image[:,0]) == 0:
		image = np.delete(image,0,1)
	while np.sum(image[-1]) == 0:
		image = image[:-1]
	while np.sum(image[:,-1]) == 0:
		image = np.delete(image,-1,1)
	return image
	
def place_in_square(image, box_side):
	rows, cols = image.shape
	# изменяем размер, чтобы помещалось в box 20x20 пикселей
	if rows > cols:   
		factor = box_side / rows
		rows = box_side
		cols = int(round(cols*factor))
		image = cv2.resize(image, (cols,rows))
	else:
		factor = box_side / cols
		cols = box_side
		rows = int(round(rows*factor))
		image = cv2.resize(image, (cols, rows))
	return image
	
def extend_black(image, box_side):
	# добавляем вокруг 20х20 черные поля, чтобы стало 28х28
	rows, cols = image.shape
	
	
	
	colsPadding = (int(math.ceil((box_side-cols)/2.0)),int(math.floor((box_side-cols)/2.0)))
	rowsPadding = (int(math.ceil((box_side-rows)/2.0)),int(math.floor((box_side-rows)/2.0)))
	image = np.pad(image,(rowsPadding,colsPadding),'constant')
	return image
	
def move_cm_to_center(image):
	rows,cols = image.shape
	cy,cx = center_of_mass(image)
	shiftx = np.round(cols/2.0-cx).astype(int)
	shifty = np.round(rows/2.0-cy).astype(int)
	rows,cols = image.shape
	M = np.float32([[1,0,shiftx],[0,1,shifty]])
	image = cv2.warpAffine(image,M,(cols,rows))
	return image
	
def preprocess_one_digit_area(image, real_box_size, target_box_size, invert = True, sharpness = 1.1):
	
	if sharpness:
		mean_brightness = cv2.mean(image)[0]
		_, image = cv2.threshold(image, mean_brightness / sharpness, 255, cv2.THRESH_BINARY)
#		_, image = cv2.threshold(image, 255 - (255 - mean_brightness) / sharpness, 255, cv2.THRESH_BINARY)
	if invert:
		image = cv2.bitwise_not(image)
	
	img_size = max(image.shape)
	new_size = img_size + real_box_size
	image = extend_black(image, img_size + real_box_size)
	image = move_cm_to_center(image)
	a = new_size // 2
	b = real_box_size // 2
	image = image[a - b : a + b, a - b : a + b]
	image = cv2.resize(image, (target_box_size, target_box_size))
	return image