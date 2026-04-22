import cv2
import sys
import glob
import os
import tkinter as tk
from preprocessing import process_answer_sheet
from blank_reader import read_preprocessed_blank, print_ans_on_blank, print_score_on_blank, print_areas_on_blank
from gui import ask_text_question, ask_multiple_choice_question

selected_cell = [0, 0]

def check(result, blank_scheme, current_path):
    var = ''.join(result[0]).strip(' ')
    filename = os.path.join(current_path, var + '.var')
    try:
        with open(filename, 'r') as f:
            correct = [line.strip() for line in f]
            #print(correct)
    except Exception:
        print(f'Файл {filename} не найден. Проверка невозможна.')
        return []
    # Проверяем только столько заданий, сколько строк в .var
    num_to_check = len(correct)
    answers_to_check = result[1:1+num_to_check]
    #print(answers_to_check)
    if len(answers_to_check) != num_to_check:
        print(f'Несоответствие: в .var {num_to_check} строк, распознано {len(answers_to_check)} заданий')
        return []

    check_keys = blank_scheme['check_keys'][:num_to_check]
    score = []
    #print(check_keys)
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

def redraw_with_highlight(image, result, areas, score, blank_scheme, selected_cell):
        checked = print_ans_on_blank(image, result, areas)
        if score:
            final = print_score_on_blank(checked, blank_scheme, score)
        else:
            final = checked
        # Draw highlight
        i, j = selected_cell
        if i < len(areas) and j < len(areas[i]):
            x_box, y_box, w, h = areas[i][j]
            cv2.rectangle(final, (x_box, y_box), (x_box + w, y_box + h), (0, 165, 255), 4)
        return final

def point_capture(event, x, y, flags, params):
    image, result, score, areas, blank_scheme, current_path, selected_cell = params

    if event == cv2.EVENT_LBUTTONDOWN:
        for i in range(len(result)):
            for j in range(len(result[i])):
                if (x > areas[i][j][0] and x < areas[i][j][0] + areas[i][j][2] and
                    y > areas[i][j][1] and y < areas[i][j][1] + areas[i][j][3]):
                    selected_cell[0] = i
                    selected_cell[1] = j
                    final = redraw_with_highlight(image, result, areas, score, blank_scheme, selected_cell)
                    cv2.imshow('Image', final)
                    
                    while True:
                        try:
                            root = tk._default_root
                            if root:
                                root.update()
                        except:
                            pass
                        
                        try:
                            if cv2.getWindowProperty('Image', cv2.WND_PROP_VISIBLE) < 1:
                                return
                        except:
                            return
                        
                        key = cv2.waitKey(30) & 0xFF
                        
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
                                final = redraw_with_highlight(final, result, areas, score, blank_scheme, selected_cell)
                                cv2.imshow('Image', final)
                                return
                            if key == 27:
                                cv2.imshow('Image', image)
                                return
                            elif key == 13:
                                cv2.imshow('Image', image)
                                return

def process_frame(frame, blank_scheme, current_path, sharpness=1):
    window_name = 'Image'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)
    
    flag, processed_image = process_answer_sheet(frame, sharpness=sharpness)
    if flag:
        image_to_show = print_areas_on_blank(processed_image, blank_scheme)
    else:
        image_to_show = processed_image
    
    cv2.imshow(window_name, image_to_show)

    while True:
        try:
            root = tk._default_root
            if root:
                root.update()
        except:
            pass
        
        try:
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                cv2.destroyAllWindows()
                return [None, sharpness, None, 'cancelled']  # ADDED FLAG
        except:
            cv2.destroyAllWindows()
            return [None, sharpness, None, 'cancelled']  # ADDED FLAG
        
        key = cv2.waitKey(30) & 0xFF
        
        if key == 27:  # ESC
            cv2.destroyWindow(window_name)
            return [None, sharpness, None, 'cancelled']  # ADDED FLAG
        elif key == 13:  # Enter
            break
        elif key == ord('-') or key == ord('_'):
            sharpness *= 0.9
            flag, processed_image = process_answer_sheet(frame, sharpness=sharpness)
            image_to_show = print_areas_on_blank(processed_image, blank_scheme) if flag else processed_image
            cv2.imshow(window_name, image_to_show)
        elif key == ord('=') or key == ord('+'):
            sharpness *= 1.111
            flag, processed_image = process_answer_sheet(frame, sharpness=sharpness)
            image_to_show = print_areas_on_blank(processed_image, blank_scheme) if flag else processed_image
            cv2.imshow(window_name, image_to_show)


    cutted_image, result, areas, digits = read_preprocessed_blank(processed_image, blank_scheme)
    checked = print_ans_on_blank(cutted_image, result, areas)
    score = check(result, blank_scheme, current_path)

    # Track selected cell for arrows navigation
    global selected_cell
    selected_cell = [0, 0]
    for i in range(len(result)):
        for j in range(len(result[i])):
            if result[i][j] != ' ':
                selected_cell = [i, j]
                break
        if selected_cell != [0, 0]:
            break
    
    if score:
        final = print_score_on_blank(checked, blank_scheme, score)
    else:
        final = checked

    final = redraw_with_highlight(final, result, areas, score, blank_scheme, selected_cell)
    cv2.imshow(window_name, final)
    cv2.setMouseCallback(window_name, point_capture, [cutted_image, result, score, areas, blank_scheme, current_path, selected_cell])

    while True:
        try:
            root = tk._default_root
            if root:
                root.update()
        except:
            pass
        
        try:
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                cv2.destroyAllWindows()
                return [None, sharpness, None, 'cancelled']
        except:
            cv2.destroyAllWindows()
            return [None, sharpness, None, 'cancelled']
        
        key = cv2.waitKeyEx(30)
        key_masked = key & 0xFF
        
        # ARROW KEY NAVIGATION
        if key == 2424832:  # Left arrow
            i, j = selected_cell
            if j > 0:
                selected_cell[1] = j - 1
                final = redraw_with_highlight(cutted_image, result, areas, score, blank_scheme, selected_cell)
                cv2.imshow(window_name, final)
        elif key == 2555904:  # Right arrow
            i, j = selected_cell
            if j < len(areas[i]) - 1:
                selected_cell[1] = j + 1
                final = redraw_with_highlight(cutted_image, result, areas, score, blank_scheme, selected_cell)
                cv2.imshow(window_name, final)
        elif key == 2490368:  # Up arrow
            i, j = selected_cell
            if i > 0:
                selected_cell[0] = i - 1
                if selected_cell[1] >= len(areas[selected_cell[0]]):
                    selected_cell[1] = len(areas[selected_cell[0]]) - 1
                final = redraw_with_highlight(cutted_image, result, areas, score, blank_scheme, selected_cell)
                cv2.imshow(window_name, final)
        elif key == 2621440:  # Down arrow
            i, j = selected_cell
            if i < len(areas) - 1:
                selected_cell[0] = i + 1
                if selected_cell[1] >= len(areas[selected_cell[0]]):
                    selected_cell[1] = len(areas[selected_cell[0]]) - 1
                final = redraw_with_highlight(cutted_image, result, areas, score, blank_scheme, selected_cell)
                cv2.imshow(window_name, final)
        
        # DIGIT / COMMA / SPACE
        elif key_masked >= ord('0') and key_masked <= ord('9'):
            i, j = selected_cell
            result[i][j] = chr(key_masked)
            new_score = check(result, blank_scheme, current_path)
            if new_score:
                score.clear()
                score.extend(new_score)
            final = redraw_with_highlight(cutted_image, result, areas, score, blank_scheme, selected_cell)
            cv2.imshow(window_name, final)
        elif key_masked == ord(','):
            i, j = selected_cell
            result[i][j] = ','
            new_score = check(result, blank_scheme, current_path)
            if new_score:
                score.clear()
                score.extend(new_score)
            final = redraw_with_highlight(cutted_image, result, areas, score, blank_scheme, selected_cell)
            cv2.imshow(window_name, final)
        elif key_masked == ord(' ') or key_masked == 8 or key_masked == 127:
            i, j = selected_cell
            result[i][j] = ' '
            new_score = check(result, blank_scheme, current_path)
            if new_score:
                score.clear()
                score.extend(new_score)
            final = redraw_with_highlight(cutted_image, result, areas, score, blank_scheme, selected_cell)
            cv2.imshow(window_name, final)
        
        elif key_masked == 27:  # ESC
            cv2.destroyWindow(window_name)
            return [None, sharpness, None, 'cancelled']
        elif key_masked == 13:  # Enter
            print('OK')
            save_dataset(result, digits)
            cv2.destroyWindow(window_name)
            return [score, sharpness, result, 'success']