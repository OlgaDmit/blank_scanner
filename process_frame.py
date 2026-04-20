import cv2
import sys
import glob
import os
from preprocessing import process_answer_sheet
from blank_reader import read_preprocessed_blank, print_ans_on_blank, print_score_on_blank, print_areas_on_blank
from gui import ask_text_question, ask_multiple_choice_question

def check(result, blank_scheme, current_path):
    var = ''.join(result[0]).strip(' ')
    filename = os.path.join(current_path, var + '.var')
    try:
        with open(filename, 'r') as f:
            correct = [line.strip() for line in f]
            print(correct)
    except Exception:
        print(f'Файл {filename} не найден. Проверка невозможна.')
        return []
    # Проверяем только столько заданий, сколько строк в .var
    num_to_check = len(correct)
    answers_to_check = result[1:1+num_to_check]
    print(answers_to_check)
    if len(answers_to_check) != num_to_check:
        print(f'Несоответствие: в .var {num_to_check} строк, распознано {len(answers_to_check)} заданий')
        return []

    check_keys = blank_scheme['check_keys'][:num_to_check]
    score = []
    print(check_keys)
    for i in range(num_to_check):
        if check_keys[i] == 0:
            # Это задание не проверяется (например, часть с развёрнутым ответом)
            continue
        ans = ''.join(answers_to_check[i]).strip(' ')
        corr = correct[i]

        if check_keys[i] == 1:          # точное совпадение
            if ans == corr:
                score.append([1, True])
            else:
                score.append([0, False])

        elif check_keys[i] == 2:        # таблица (ответ может быть длиннее или короче)
            if len(ans) > len(corr):
                score.append([0, False])
                continue
            while len(ans) < len(corr):
                ans += ' '
            counter = sum(1 for j in range(len(corr)) if ans[j] != corr[j])
            if counter == 0:
                score.append([2, True])
            elif counter == 1:
                score.append([1, False])
            else:
                score.append([0, False])

        elif check_keys[i] == 3:        # множество (порядок не важен)
            counter = 0
            for c in corr:
                if c not in ans:
                    counter += 1
            counter += len(ans) - len(corr) + counter
            if counter == 0:
                score.append([2, True])
            elif counter == 1:
                score.append([1, False])
            else:
                score.append([0, False])

    return score

def save_dataset(result, digits):
    try:
        data_path = os.path.join('model', 'autosaved')
        for i in range(len(result)):
            for j in range(len(result[i])):
                if digits[i][j] is not None and result[i][j] != ' ':
                    path = os.path.join(data_path, str(result[i][j]))
                    os.makedirs(path, exist_ok=True)
                    files = glob.glob(os.path.join(path, '*.jpg'))
                    last_num = max([int(f.split('/')[-1][:-4]) for f in files]) if files else -1
                    filename = str(last_num + 1) + '.jpg'
                    cv2.imwrite(os.path.join(path, filename), digits[i][j])
    except Exception as e:
        print(f'Ошибка сохранения датасета: {e}')

def point_capture(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        image, result, score, areas, blank_scheme, current_path = params
        for i in range(len(result)):
            for j in range(len(result[i])):
                if (x > areas[i][j][0] and x < areas[i][j][0] + areas[i][j][2] and
                    y > areas[i][j][1] and y < areas[i][j][1] + areas[i][j][3]):
                    chosen = print_ans_on_blank(image, result, areas)
                    cv2.rectangle(chosen, areas[i][j], (0, 165, 255), 3)
                    cv2.imshow('Image', chosen)
                    while True:
                        key = cv2.waitKey(1) & 0xFF
                        if key < 255:
                            if (key >= ord('0') and key <= ord('9')) or key == ord(',') or key == ord(' '):
                                result[i][j] = chr(key)
                                checked = print_ans_on_blank(image, result, areas)
                                new_score = check(result, blank_scheme, current_path)
                                if new_score:
                                    score.clear()
                                    score.extend(new_score)
                                    final = print_score_on_blank(checked, blank_scheme, score)
                                else:
                                    final = checked
                                cv2.imshow('Image', final)
                                return
                            if key == 27:
                                return
                            elif key == 13:
                                return
        print("Missclick")

def process_frame(frame, blank_scheme, current_path, sharpness=1):
    flag, processed_image = process_answer_sheet(frame, sharpness=sharpness)
    if flag:
        image_to_show = print_areas_on_blank(processed_image, blank_scheme)
    else:
        image_to_show = processed_image
    cv2.imshow('Image', image_to_show)

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC - закрыть окно и вернуться
            cv2.destroyWindow('Image')
            return None, sharpness, None
        elif key == 13:  # Enter - продолжить распознавание
            break
        elif key == 2:  # уменьшить резкость
            sharpness *= 0.9
            flag, processed_image = process_answer_sheet(frame, sharpness=sharpness)
            image_to_show = print_areas_on_blank(processed_image, blank_scheme) if flag else processed_image
            cv2.imshow('Image', image_to_show)
        elif key == 3:  # увеличить резкость
            sharpness *= 1.111
            flag, processed_image = process_answer_sheet(frame, sharpness=sharpness)
            image_to_show = print_areas_on_blank(processed_image, blank_scheme) if flag else processed_image
            cv2.imshow('Image', image_to_show)

    cutted_image, result, areas, digits = read_preprocessed_blank(processed_image, blank_scheme)
    checked = print_ans_on_blank(cutted_image, result, areas)
    score = check(result, blank_scheme, current_path)
    print(f"DEBUG: score = {score}")
    print(f"DEBUG: rates_coords = {blank_scheme.get('rates_coords', [])}")
    if score:
        final = print_score_on_blank(checked, blank_scheme, score)
    else:
        final = checked
    cv2.imshow('Image', final)

    cv2.setMouseCallback('Image', point_capture, [cutted_image, result, score, areas, blank_scheme, current_path])

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC - закрыть окно и вернуться
            cv2.destroyWindow('Image')
            return None, sharpness, None
        elif key == 13:  # Enter - сохранить результаты
            print('OK')
            save_dataset(result, digits)
            cv2.destroyWindow('Image')
            return score, sharpness, result