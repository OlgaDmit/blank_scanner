import cv2
import numpy as np
import os
from tensorflow import keras
from preprocessing import preprocess_one_digit_area

def read_preprocessed_blank(image, blank_scheme):
    # Загружаем модель с проверкой существования
    model_path = 'model/mnist_new.h5'
    if os.path.exists(model_path):
        model = keras.models.load_model(model_path)
    else:
        print("Модель не найдена, распознавание будет пропущено")
        model = None

    imwidth, imheight = blank_scheme['image_size']
    w, h, mw, mh = blank_scheme['field_sizes']
    var_coords = blank_scheme['var_coords']
    problems_coords = blank_scheme['problems_coords']
    problems_coords = [var_coords] + problems_coords

    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.resize(image, (imwidth, imheight))

    recognized_answers = []
    areas = []
    digits_all = []

    for problem_x, problem_y, fields_number in problems_coords:
        recognized_digits = []
        areas_digits = []
        digits = []
        for digit_index in range(fields_number):
            digit_x = problem_x + digit_index * (w + mw) + mw // 2
            digit_y = problem_y + mh // 2
            digit = image[digit_y:digit_y + h + mh, digit_x:digit_x + w + mw]
            digits.append(digit)
            digit = preprocess_one_digit_area(digit, 42, 28, sharpness=1.1)
            areas_digits.append([digit_x, digit_y, w + mw, h + mh])

            white_pixel_ratio = np.sum(digit > 128) / digit.size
            if digit.max() == 0 or white_pixel_ratio < 0.02 or model is None:
                recognized_digits.append(' ')
                continue

            digit = digit.astype('float32') / 255.0
            digit = np.expand_dims(digit, axis=-1)
            prediction = model.predict(np.array([digit]), verbose=0)
            recognized_digit = np.argmax(prediction)
            confidence = np.max(prediction)

            if confidence < 0.5:
                recognized_digits.append(' ')
            else:
                if recognized_digit < 10:
                    recognized_digits.append(str(recognized_digit))
                elif recognized_digit == 10:
                    recognized_digits.append(',')
                elif recognized_digit == 11:
                    recognized_digits.append('-')

        recognized_answers.append(recognized_digits)
        areas.append(areas_digits)
        digits_all.append(digits)

    colored = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    return [colored, recognized_answers, areas, digits_all]

def print_areas_on_blank(image, blank_scheme):
    imwidth, imheight = blank_scheme['image_size']
    w, h, mw, mh = blank_scheme['field_sizes']
    var_coords = blank_scheme['var_coords']
    problems_coords = blank_scheme['problems_coords']
    problems_coords = [var_coords] + problems_coords
    image = cv2.resize(image, (imwidth, imheight))
    for problem_x, problem_y, fields_number in problems_coords:
        for digit_index in range(fields_number):
            digit_x = problem_x + digit_index * (w + mw) + mw // 2
            digit_y = problem_y + mh // 2
            square = [digit_x, digit_y, w + mw, h + mh]
            cv2.rectangle(image, square, (255, 0, 255), 1)
    return image

def print_ans_on_blank(temp_image, recognized_answers, areas):
    image = temp_image.copy()
    for problem_index in range(len(recognized_answers)):
        for digit_index in range(len(recognized_answers[problem_index])):
            square = areas[problem_index][digit_index]
            cv2.rectangle(image, square, (0, 255, 0), 1)
            cv2.putText(image, recognized_answers[problem_index][digit_index],
                        [square[0] + square[2]//2, square[1] + square[3]],
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
    return image

def print_score_on_blank(temp_image, blank_scheme, score):
    rates_coords = blank_scheme['rates_coords']
    image = temp_image.copy()
    for problem_index in range(len(score)):
        color = (0, 150, 0) if score[problem_index][1] else (0, 0, 255)
        square = [rates_coords[problem_index][0], rates_coords[problem_index][1]]
        cv2.putText(image, str(score[problem_index][0]), square, cv2.FONT_HERSHEY_SIMPLEX, 2, color, 3)
    return image