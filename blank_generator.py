import os
import sys
from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------------
#  Вспомогательные функции для рисования
# ----------------------------------------------------------------------
def draw_rectangle(draw, coords, l, **kwargs):
    x, y, w, h = coords[:]
    for i in range(x, x + w, l):
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

def get_text_size(font, text):
    try:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        return font.getsize(text)

def make_number(draw, coords, number, fonts, box_size, box_margin,
                number_of_boxes, l, rate, **kwargs):
    x, y = coords[:]
    w, h = box_size[:]
    margin_x, margin_y = box_margin[:]
    roman, bold = fonts[:]

    text_width, _ = get_text_size(roman, "00")
    text_x_end = x + text_width
    draw.text((text_x_end, y + h * 9 // 10), str(number),
              font=bold, fill=(0, 0, 0, 255), anchor='rs')

    boxes_x = text_x_end + 2 * margin_x
    boxes_x_cutting = boxes_x - margin_x // 2
    boxes_y_cutting = y - margin_y
    draw_boxes(draw, [boxes_x, y], box_size, margin_x, number_of_boxes, l, **kwargs)

    boxes_x_end = boxes_x + (number_of_boxes) * (w + margin_x) - margin_x
    rating_x = boxes_x_end + (2 * margin_x if number_of_boxes else 0)
    rating_y = y + h * 9 // 10
    draw.text([rating_x, rating_y], "__", font=roman, fill=(0, 0, 0, 255), anchor='ls')
    under_width, _ = get_text_size(roman, "__")
    draw.text([rating_x + under_width * 11 // 10, rating_y],
              "/" + str(rate), font=roman, fill=(0, 0, 0, 255), anchor='ls')

    return [boxes_x_cutting, boxes_y_cutting, number_of_boxes, rating_x, rating_y]

# ----------------------------------------------------------------------
#  Получение системного шрифта
# ----------------------------------------------------------------------
def get_system_font(size, bold=False):
    if sys.platform == 'win32':
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
        ]
    elif sys.platform == 'darwin':
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Helvetica-Bold.ttf" if bold else "/System/Library/Fonts/Helvetica.ttc"
        ]
    else:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

# ----------------------------------------------------------------------
#  Основная функция генерации шаблона
# ----------------------------------------------------------------------
def generate_custom_template(output_path, title_text="ЕГЭ 2026",
                             problems=27, test_problems=20,
                             rates=None, check_keys=None,
                             problems_in_column=10, columns=None,
                             fields_number=10, problems_names=None):
    if rates is None:
        rates = [1] * problems
    if problems_names is None:
        problems_names = [str(i) for i in range(1, problems + 1)]

    # ----- Гарантированная обработка check_keys -----
    new_check_keys = [0] * problems
    if check_keys is not None:
        temp = list(check_keys)[:problems]
        for i in range(min(test_problems, problems)):
            if i < len(temp):
                new_check_keys[i] = temp[i]
            else:
                new_check_keys[i] = 1   # тип проверки по умолчанию для тестовых
    else:
        for i in range(test_problems):
            new_check_keys[i] = 1
    check_keys = new_check_keys
    # -----------------------------------------------

    # Количество клеток для каждого задания
    boxes_per_problem = [fields_number if i < test_problems else 0 for i in range(problems)]

    # Определяем количество столбцов
    if columns is None:
        columns = (problems + problems_in_column - 1) // problems_in_column

    # Разбивка заданий по столбцам
    column_indices = []
    for col in range(columns):
        start = col * problems_in_column
        end = min(start + problems_in_column, problems)
        column_indices.append(list(range(start, end)))

    # Параметры отрисовки (константы)
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

    # Вспомогательная функция для вычисления ширины столбца по максимальному числу клеток
    def column_width(max_boxes):
        # Ширина номера (2 цифры) - примерно 2*field_w
        number_width = 2 * field_w
        # Ширина клеток: max_boxes клеток + отступы между ними
        if max_boxes > 0:
            cells_width = max_boxes * (field_w + margin_w) - margin_w
        else:
            cells_width = 0
        # Ширина поля для балла (прочерк + "/" + число) - примерно 3*field_w
        score_width = 3 * field_w
        # Отступы между блоками: номер -> клетки -> балл (2 отступа по margin_w)
        spacing = 2 * margin_w
        return number_width + spacing + cells_width + spacing + score_width

    # Вычисляем максимальное количество клеток в каждом столбце
    max_boxes_per_col = []
    for indices in column_indices:
        max_box = max(boxes_per_problem[i] for i in indices) if indices else 0
        max_boxes_per_col.append(max_box)

    # Ширины столбцов
    col_widths = [column_width(mb) for mb in max_boxes_per_col]

    # Общая ширина бланка
    width = (margin_left_fields +
             sum(col_widths) +
             intercolumn_spacing * (columns - 1) +
             margin_left_fields)   # правый отступ
    height = field_hh * (problems_in_column + 3) + margin_h

    # Создание изображения
    image = Image.new("RGB", (int(width), int(height)), "white")
    draw = ImageDraw.Draw(image)

    # Шрифты
    roman = get_system_font(field_h, bold=False)
    bold_font = get_system_font(field_h, bold=True)

    # Маркерные квадраты
    markers = [
        (0, 0),
        (width - marker_size, 0),
        (0, height - marker_size),
        (width - marker_size, height - marker_size),
    ]
    for mx, my in markers:
        draw.rectangle([mx, my, mx + marker_size, my + marker_size], fill="black")

    # Заголовки
    draw.text((margin_left_headers, margin_top), title_text, font=roman, fill=(0, 0, 0))
    draw.text((width // 2 - 5 * field_h, margin_top), "Бланк ответов №1", font=bold_font, fill=(0, 0, 0))
    # Поле варианта
    var_field_width = 3 * (field_w + margin_w) - margin_w
    var_x = width - margin_left_headers - var_field_width
    draw.text((var_x - margin_w, margin_top), "Вариант №", font=roman, fill=(0, 0, 0), anchor='ra')
    draw_boxes(draw, [var_x, margin_top], [field_w, field_h], margin_w, 3, 4, fill=(200, 200, 200), width=2)
    var_place = [var_x - 2 * margin_w, -(margin_h - margin_top), 3]

    # Фамилия, имя
    draw.text((margin_left_headers, margin_top + field_hh), "Фамилия, имя:", font=roman, fill=(0, 0, 0))
    draw.line([margin_left_lines - margin_w, field_hh * 2,
               width - margin_left_lines + margin_w, field_hh * 2], fill=(0, 0, 0), width=2)

    # Координаты X для каждого столбца
    col_x = []
    current_x = margin_left_fields
    for cw in col_widths:
        col_x.append(int(current_x))
        current_x += cw + intercolumn_spacing

    scheme_lines = []
    # Отрисовка заданий
    for col in range(columns):
        for row, prob_idx in enumerate(column_indices[col]):
            if prob_idx >= problems:
                break
            y = int(field_hh * (row + 2) + margin_h)
            x0 = col_x[col]
            num_boxes = boxes_per_problem[prob_idx]
            if prob_idx < test_problems:
                # Задания с клетками
                boxes_x_cutting, boxes_y_cutting, _, rating_x, rating_y = make_number(
                    draw, [x0, y], problems_names[prob_idx],
                    [roman, bold_font], [field_w, field_h], [margin_w, margin_h],
                    num_boxes, 4, rates[prob_idx],
                    fill=(200, 200, 200), width=2
                )
                scheme_lines.append(f"{boxes_x_cutting} {boxes_y_cutting} {num_boxes} {rating_x} {rating_y}")
            else:
                # Задания без клеток (только номер и балл)
                text_width, _ = get_text_size(roman, "00")
                text_x_end = x0 + text_width
                draw.text((text_x_end, y + field_h * 9 // 10), str(problems_names[prob_idx]),
                          font=bold_font, fill=(0, 0, 0), anchor='rs')
                boxes_x = text_x_end + 2 * margin_w
                rating_x = int(boxes_x)
                rating_y = int(y + field_h * 9 // 10)
                draw.text([rating_x, rating_y], "__", font=roman, fill=(0, 0, 0), anchor='ls')
                under_width, _ = get_text_size(roman, "__")
                draw.text([rating_x + under_width * 11 // 10, rating_y],
                          f"/{rates[prob_idx]}", font=roman, fill=(0, 0, 0), anchor='ls')
                scheme_lines.append(f"{int(boxes_x)} {int(y - margin_h)} 0 {rating_x} {rating_y}")

    # Нижняя черта
    draw.line([margin_left_lines - margin_w, field_hh * (problems_in_column + 2) + margin_h,
               width - margin_left_lines + margin_w, field_hh * (problems_in_column + 2) + margin_h],
              fill=(0, 0, 0), width=2)

    total_test = sum(rates[:test_problems])
    total_part2 = sum(rates[test_problems:])
    total_all = total_test + total_part2

    draw.text((margin_left_headers, margin_top + field_hh * (problems_in_column + 2) + margin_h),
              f"Тест: __ /{total_test}", font=roman, fill=(0, 0, 0))
    test_width, _ = get_text_size(roman, "Тест: __ /000")
    draw.text((margin_left_headers + test_width + interrates_spacing,
               margin_top + field_hh * (problems_in_column + 2) + margin_h),
              f"II часть: __ /{total_part2}", font=roman, fill=(0, 0, 0))
    draw.text((width - margin_left_headers,
               margin_top + field_hh * (problems_in_column + 2) + margin_h),
              f"Сумма: __ /{total_all}", font=roman, fill=(0, 0, 0), anchor='ra')

    image.save(output_path)

    # Сохраняем схему
    final_check_keys = list(check_keys)[:problems]  # обрезаем
    for i in range(test_problems, problems):
        final_check_keys[i] = 0

    # Сохраняем схему
    scheme_path = os.path.splitext(output_path)[0] + ".set"
    with open(scheme_path, 'w', encoding='utf-8') as f:
        f.write(' '.join(problems_names) + '\n')
        f.write(' '.join(map(str, rates)) + '\n')
        f.write(' '.join(map(str, final_check_keys)) + '\n')   # исправленный список
        f.write(f"{int(width)} {int(height)}\n")
        f.write(str(marker_size * marker_size / width / height) + '\n')
        f.write(f"{field_w} {field_h} {margin_w} {margin_h}\n")
        f.write(' '.join(map(str, var_place)) + '\n')
        for line in scheme_lines:
            f.write(line + '\n')

    print(f"Шаблон сохранён в {output_path}")
    print(f"Файл схемы: {scheme_path}")
    return scheme_path

def generate_answer_sheet_template(output_path):
    generate_custom_template(output_path)

def load_var_scheme_file(path):
    with open(path, 'r') as f:
        blank_scheme = {}
        blank_scheme['rates'] = list(map(int, f.readline().split()))
        blank_scheme['check_keys'] = list(map(int, f.readline().split()))
        blank_scheme['image_size'] = list(map(int, f.readline().split()))
        blank_scheme['max_area'] = float(f.readline())
        blank_scheme['field_sizes'] = list(map(int, f.readline().split()))
        blank_scheme['var_coords'] = list(map(int, f.readline().split()))
        problems_coords = []
        rates_coords = []
        for line in f:
            parts = list(map(int, line.split()))
            problems_coords.append(parts[:3])
            rates_coords.append(parts[3:])
        blank_scheme['problems_coords'] = problems_coords
        blank_scheme['rates_coords'] = rates_coords
        blank_scheme['problems_names'] = [str(i) for i in range(1, len(problems_coords)+1)]
        return blank_scheme

def load_var_scheme_file_enhanced(path):
    return load_var_scheme_file(path)

if __name__ == "__main__":
    generate_answer_sheet_template("answer_sheet_template.png")