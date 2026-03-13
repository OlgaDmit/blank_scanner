from PIL import Image, ImageDraw, ImageFont
#import numpy as np
#import cv2

def draw_rectangle(draw, coords, l, **kwargs):
	x, y, w, h = coords[:]
	for i in range(x, x+w, l):
		draw.line([i + l / 2, y, i + l, y], **kwargs)
		draw.line([i + l / 2, y + h, i + l, y + h], **kwargs)
	for i in range(y, y + h, l):
		draw.line([x, i + l / 2, x, i + l], **kwargs)
		draw.line([x + w, i + l / 2, x + w, i + l], **kwargs)
		
def draw_boxes(draw, coord, size, margin, number, l, **kwargs):
	x, y = coord[:]
	w, h = size[:]
	step = margin + w
	for i in range(number):
		draw_rectangle(draw, [x + i * step, y, w, h], l, **kwargs)
		
def make_number(draw, coords, number, fonts, box_size, box_margin, number_of_boxes, l, rate, **kwargs):
	x, y = coords[:]
	w, h = box_size[:]
	margin_x, margin_y = box_margin[:]
	roman, bold = fonts[:]
	text_x_end = x + roman.font.getsize("00")[0][0]
	draw.text((text_x_end, y + h * 9 // 10), str(number), font=bold, fill=(0, 0, 0, 255), anchor='rs')
	boxes_x = text_x_end + 2 * margin_x
	boxes_x_cutting = boxes_x - margin_x // 2
	boxes_y_cutting = y - margin_y
	draw_boxes(draw, [boxes_x, y], box_size, margin_x, number_of_boxes, l, **kwargs)
	boxes_x_end = boxes_x + (number_of_boxes) * (w + margin_x) - margin_x
	if number_of_boxes:
		rating_x = boxes_x_end + 2 * margin_x
	else:
		rating_x = boxes_x_end
	rating_y = y + h * 9 // 10
	draw.text([rating_x, y + h * 9 // 10], "__", font=roman, fill=(0, 0, 0, 255),anchor='ls')
	draw.text([rating_x + roman.font.getsize("__")[0][0] * 11//10, y + h * 9 // 10], "/" + str(rate), font=roman, fill=(0, 0, 0, 255),anchor='ls')
	
	return [boxes_x_cutting, boxes_y_cutting, number_of_boxes, rating_x, rating_y]
	
	

def generate_answer_sheet_template(output_path):

	supporting_file = open('blank_template.txt', 'w')

	field_h = 40
	field_w = 36
	margin_h = 30
	margin_w = 18
	field_hh = field_h + margin_h
	field_ww = field_w + margin_w
	margin_left_headers = 100
	margin_left_fields = 40
	margin_left_lines = 40
	margin_top = 20
	intercolumn_spacing = field_w * 2
	interrates_spacing = 150
	
	marker_size = 50
	
#	title_text = "ОГЭ 2026"
#	problems = 22 # OGE 2026
#	test_problems = 16 # OGE 2026
#	rates = [2, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 2, 3, 2, 2, 3, 3, 3] # OGE 2026
#	check_keys = [1, ] # OGE 2026
#	problems_in_column = 8 #(problems - 1) // 3 + 1 # OGE 2026
	
	
	
	title_text = "ЕГЭ 2026"
	problems = 27
	test_problems = 20
	rates = [1, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 2, 2, 1, 2, 2, 1, 1, 3, 2, 2, 3, 3, 3, 1]
	check_keys = [1, 1, 1, 1, 3, 2, 1, 1, 3, 2, 1, 1, 1, 3, 2, 1, 2, 3, 1, 1, 0, 0, 0, 0, 0, 0, 0]
	problems_in_column = 10
	
	columns = 3
	fields_number = 10
	problems_names = [str(i) for i in range(1,27)] + ['К1']
	
	
	
	latin_file_roman = "/Users/mac/Library/Fonts/Latin-Roman.ttf"
	latin_roman = ImageFont.truetype(latin_file_roman, field_h)	
	latin_file_bold = "/Users/mac/Library/Fonts/Latin-Bold.ttf"
	latin_bold = ImageFont.truetype(latin_file_bold, field_h)	
	
	# Создаём белое изображение A4 (2480x3508 пикселей, 300 DPI)
	height = field_hh * (problems_in_column + 3) + margin_h
	width = 1900
	image = Image.new("RGB", (width, height), "white")
	draw = ImageDraw.Draw(image)
	
	supporting_file.write(' '.join([str(i) for i in problems_names]) + '\n')
	supporting_file.write(' '.join([str(i) for i in rates]) + '\n')
	supporting_file.write(' '.join([str(i) for i in check_keys]) + '\n')
	
	supporting_file.write(' '.join([str(i) for i in [width, height]]) + '\n') 
	supporting_file.write(str(marker_size * marker_size / width / height) + '\n')
	field_sizes = [field_w, field_h, margin_w, margin_h]
	supporting_file.write(' '.join([str(i) for i in field_sizes]) + '\n') 
#	supporting_file.write(str(fields_number) + '\n')
	
	
	# draw text, full opacity
	# writer.text((10, 60), "World", font=fnt, fill=(255, 255, 255, 128))
	
	# Область ответов (пример: прямоугольник в нижней части)
	answer_area_x1, answer_area_y1 = 0, 0
	answer_area_x2, answer_area_y2 = width, height
	answer_area_width = answer_area_x2 - answer_area_x1
	answer_area_height = answer_area_y2 - answer_area_y1
	
	# Рисуем чёрные квадраты по углам области ответов
	markers = [
	    (answer_area_x1, answer_area_y1),  # Левый верхний
	    (answer_area_x2 - marker_size, answer_area_y1),  # Правый верхний
	    (answer_area_x1, answer_area_y2 - marker_size),  # Левый нижний
	    (answer_area_x2 - marker_size, answer_area_y2 - marker_size),  # Правый нижний
	]
	
	for x, y in markers:
	    draw.rectangle([x, y, x + marker_size, y + marker_size], fill="black")
	    
	draw.text((margin_left_headers, margin_top), title_text, font=latin_roman, fill=(0, 0, 0, 255))
	draw.text((width // 2 - 5 * field_h, margin_top), "Бланк ответов №1", font=latin_bold, fill=(0, 0, 0, 255))
	draw.text((width - margin_left_headers - 3 * field_ww - margin_w, margin_top), "Вариант №", font=latin_roman, fill=(0, 0, 0, 255), anchor='ra')
	draw_boxes(draw, [width - margin_left_headers - 3 * field_ww, margin_top], [field_w, field_h], margin_w, 3, 4, fill=(200, 200, 200), width=2)
	var_place = [width - 5 * field_ww - margin_w, - (margin_h - margin_top), 3]
	supporting_file.write(' '.join([str(i) for i in var_place]) + '\n') 
	
	draw.text((margin_left_headers, margin_top + field_hh), "Фамилия, имя:", font=latin_roman, fill=(0, 0, 0, 255))
	
	draw.line([margin_left_lines - margin_w, field_hh * 2, width - margin_left_lines + margin_w, field_hh * 2], fill=(0, 0, 0), width=2)
	
	test_number_places = []
	for i in range(columns):
		for j in range(problems_in_column):
			number = i * problems_in_column + j
			xc_number = margin_left_fields + i * ( (4 + fields_number) * (field_w + margin_w) + intercolumn_spacing)
			yc_number = field_hh * (j + 2) + margin_h
			if (number < test_problems):        #(3 + number_of_boxes) * (w + box_margin)
				position = make_number(draw, [xc_number, yc_number], problems_names[number], [latin_roman, latin_bold], [field_w, field_h], [margin_w, margin_h], fields_number, 4, rates[number], fill=(200, 200, 200), width=2)
				supporting_file.write(' '.join([str(i) for i in position]) + '\n')
				
#				test_number_places.append([xc_cutting, yc_cutting, w_cutting, h_cutting])
			elif (number < problems):
				make_number(draw, [xc_number, yc_number], problems_names[number], [latin_roman, latin_bold], [field_w, field_h], [margin_w, margin_h], 0, 4, rates[number], fill=(200, 200, 200), width=2)
			else:
				break
	
	draw.line([margin_left_lines - margin_w, field_hh * (problems_in_column + 2) + margin_h, width - margin_left_lines + margin_w, field_hh * (problems_in_column + 2) + margin_h], fill=(0, 0, 0), width=2)
	
	draw.text((margin_left_headers, margin_top + field_hh * (problems_in_column + 2) + margin_h), "Тест: __ /" + str(sum(rates[0:test_problems])), font=latin_roman, fill=(0, 0, 0, 255))
	draw.text((margin_left_headers + latin_roman.font.getsize("Тест: __ /000")[0][0] + interrates_spacing, margin_top + field_hh * (problems_in_column + 2) + margin_h), "II часть: __ / " + str(sum(rates[test_problems:])), font=latin_roman, fill=(0, 0, 0, 255))
	draw.text((width - margin_left_headers, margin_top + field_hh * (problems_in_column + 2) + margin_h), "Сумма: __ / " + str(sum(rates)), font=latin_roman, fill=(0, 0, 0, 255), anchor = 'ra')
	
	# Сохраняем шаблон
	image.save(output_path)
	print(f"Шаблон сохранён в {output_path}")
	
	
def load_var_scheme_file(path):
	supporting_file = open(path, 'r')
	blank_scheme = {}
	blank_scheme['rates'] = map(int, supporting_file.readline().split())
	blank_scheme['check_keys'] = map(int, supporting_file.readline().split())
	blank_scheme['image_size'] = map(int, supporting_file.readline().split())
	blank_scheme['max_area'] = float(supporting_file.readline())
	blank_scheme['field_sizes'] = map(int, supporting_file.readline().split())
#	fields_number = int(supporting_file.readline())
	blank_scheme['var_coords'] = map(int, supporting_file.readline().split())
	problems_coords = []
	rates_coords = []
	for line in supporting_file:
		problems_coords.append(list(map(int, line.split()[:3])) )
		rates_coords.append(list(map(int, line.split()[3:])) )
	blank_scheme['problems_coords'] = problems_coords
	blank_scheme['rates_coords'] = rates_coords
	return blank_scheme

if __name__ == "__main__":

	generate_answer_sheet_template("answer_sheet_template.png")