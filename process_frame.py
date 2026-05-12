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
                    return
                            
def move_selection(direction, selected_cell, areas):
    i, j = selected_cell
    
    if direction == 'left':
        if j > 0:
            selected_cell[1] = j - 1
            return True
    elif direction == 'right':
        if j < len(areas[i]) - 1:
            selected_cell[1] = j + 1
            return True
    elif direction == 'up':
        if i > 0:
            selected_cell[0] = i - 1
            if selected_cell[1] >= len(areas[selected_cell[0]]):
                selected_cell[1] = len(areas[selected_cell[0]]) - 1
            return True
    elif direction == 'down':
        new_i = i + 1
        while new_i < len(areas) and len(areas[new_i]) == 0:
            new_i += 1
        if new_i < len(areas):
            selected_cell[0] = new_i
            if selected_cell[1] >= len(areas[selected_cell[0]]):
                selected_cell[1] = len(areas[selected_cell[0]]) - 1
            return True
    return False

def handle_editing_key(key, key_masked, selected_cell, areas, result, cutted_image, 
                       score, blank_scheme, current_path, digits, window_name):
    
    arrow_detected = None
    
    arrow_map = {
        2424832: 'left',
        2555904: 'right',
        2490368: 'up',
        2621440: 'down'
    }
    
    if key in arrow_map:
        arrow_detected = arrow_map[key]
    
    if arrow_detected is None:
        mac_arrow_map = {
            2: 'left',    
            3: 'right',   
            0: 'up',      
            1: 'down'     
        }
        if key > 100000 and key_masked in mac_arrow_map:
            arrow_detected = mac_arrow_map[key_masked]
    
    if arrow_detected:
        if move_selection(arrow_detected, selected_cell, areas):
            final = redraw_with_highlight(cutted_image, result, areas, score, blank_scheme, selected_cell)
            cv2.imshow(window_name, final)
        return 'continue'
    
    # DIGIT / COMMA / MINUS / SPACE
    if (key_masked >= ord('0') and key_masked <= ord('9')) or key_masked == ord(',') or key_masked == ord('-') or key_masked == ord(' '):
        i, j = selected_cell
        result[i][j] = chr(key_masked)
        checked = print_ans_on_blank(cutted_image, result, areas)
        new_score = check(result, blank_scheme, current_path)
        if new_score:
            score.clear()
            score.extend(new_score)
            final = print_score_on_blank(checked, blank_scheme, score)
        else:
            final = checked
        final = redraw_with_highlight(final, result, areas, score, blank_scheme, selected_cell)
        cv2.imshow(window_name, final)
        return 'continue'
    
    # ESC - Cancel
    if key_masked == 27:
        cv2.destroyWindow(window_name)
        return 'cancel'
    
    # ENTER - Save
    if key_masked == 13:
        print('OK')
        save_dataset(result, digits)
        cv2.destroyWindow(window_name)
        return 'save'
    
    return None

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
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 0)
    for _ in range(10):
        cv2.waitKey(1)

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
    
    if score:
        final = print_score_on_blank(checked, blank_scheme, score)
    else:
        final = checked

    final = redraw_with_highlight(final, result, areas, score, blank_scheme, selected_cell)
    cv2.imshow(window_name, final)

    cv2.createTrackbar('Empty %', window_name, 2, 10, lambda x: None)

    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 0)
    for _ in range(10):
        cv2.waitKey(1)
    cv2.setMouseCallback(window_name, point_capture, [cutted_image, result, score, areas, blank_scheme, current_path, selected_cell])

    current_threshold = 0.02

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
        
        key = cv2.waitKeyEx(10)
        key_masked = key & 0xFF

        new_threshold = cv2.getTrackbarPos('Empty %', window_name) / 100.0
        if new_threshold != current_threshold and new_threshold > 0:
            current_threshold = new_threshold
            
            cutted_image, result, areas, digits = read_preprocessed_blank(
                processed_image, blank_scheme, empty_threshold=current_threshold
            )
            
            original_result = []
            for row in result:
                original_result.append(list(row))
            
            selected_cell = [0, 0]
            for i in range(len(result)):
                for j in range(len(result[i])):
                    if result[i][j] != ' ':
                        selected_cell = [i, j]
                        break
                if selected_cell != [0, 0]:
                    break
            
            checked = print_ans_on_blank(cutted_image, result, areas)
            score = check(result, blank_scheme, current_path)
            if score:
                final = print_score_on_blank(checked, blank_scheme, score)
            else:
                final = checked
            final = redraw_with_highlight(final, result, areas, score, blank_scheme, selected_cell)
            cv2.imshow(window_name, final)
            continue
        
        action = handle_editing_key(
            key, key_masked, selected_cell, areas, result, cutted_image,
            score, blank_scheme, current_path, digits, window_name
        )

        if action =='save':
            return [score, sharpness, result, 'success']
        elif action == 'cancel':
            return [None, sharpness, None, 'cancelled']
