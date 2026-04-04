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
    if check_keys is None:
        check_keys = [0] * problems
    if problems_names is None:
        problems_names = [str(i) for i in range(1, problems + 1)]

    # Если columns не задан, вычисляем автоматически
    if columns is None:
        columns = (problems + problems_in_column - 1) // problems_in_column

    # Параметры отрисовки
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

    # Вычисляем ширину бланка в зависимости от количества столбцов
    width = margin_left_fields + columns * ((4 + fields_number) * (field_w + margin_w) + intercolumn_spacing) + 200
    height = field_hh * (problems_in_column + 3) + margin_h

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Шрифты
    roman = get_system_font(field_h, bold=False)
    bold_font = get_system_font(field_h, bold=True)

    # Маркерные квадраты (по углам)
    markers = [
        (0, 0),
        (width - marker_size, 0),
        (0, height - marker_size),
        (width - marker_size, height - marker_size),
    ]
    for x, y in markers:
        draw.rectangle([x, y, x + marker_size, y + marker_size], fill="black")

    # Заголовки
    draw.text((margin_left_headers, margin_top), title_text,
              font=roman, fill=(0, 0, 0, 255))
    draw.text((width // 2 - 5 * field_h, margin_top), "Бланк ответов №1",
              font=bold_font, fill=(0, 0, 0, 255))
    draw.text((width - margin_left_headers - 3 * field_ww - margin_w, margin_top),
              "Вариант №", font=roman, fill=(0, 0, 0, 255), anchor='ra')
    draw_boxes(draw,
               [width - margin_left_headers - 3 * field_ww, margin_top],
               [field_w, field_h], margin_w, 3, 4,
               fill=(200, 200, 200), width=2)
    draw.text((margin_left_headers, margin_top + field_hh),
              "Фамилия, имя:", font=roman, fill=(0, 0, 0, 255))
    draw.line([margin_left_lines - margin_w, field_hh * 2,
               width - margin_left_lines + margin_w, field_hh * 2],
              fill=(0, 0, 0), width=2)

    # Список для координат заданий
    scheme_lines = []
    var_place = [width - 5 * field_ww - margin_w, -(margin_h - margin_top), 3]
    scheme_lines.append(' '.join(map(str, var_place)))

    # Отрисовка заданий
    for i in range(columns):
        for j in range(problems_in_column):
            number = i * problems_in_column + j
            if number >= problems:
                break
            xc_number = margin_left_fields + i * ((4 + fields_number) * (field_w + margin_w) + intercolumn_spacing)
            yc_number = field_hh * (j + 2) + margin_h

            if number < test_problems:
                boxes_x_cutting, boxes_y_cutting, _, rating_x, rating_y = make_number(
                    draw, [xc_number, yc_number],
                    problems_names[number],
                    [roman, bold_font],
                    [field_w, field_h], [margin_w, margin_h],
                    fields_number, 4, rates[number],
                    fill=(200, 200, 200), width=2
                )
                scheme_lines.append(f"{boxes_x_cutting} {boxes_y_cutting} {fields_number} {rating_x} {rating_y}")
            else:
                # Задания без клеток
                text_x_end = xc_number + get_text_size(roman, "00")[0]
                draw.text((text_x_end, yc_number + field_h * 9 // 10), str(problems_names[number]),
                          font=bold_font, fill=(0, 0, 0, 255), anchor='rs')
                boxes_x = text_x_end + 2 * margin_w
                rating_x = boxes_x
                rating_y = yc_number + field_h * 9 // 10
                draw.text([rating_x, rating_y], "__", font=roman, fill=(0, 0, 0, 255), anchor='ls')
                under_width, _ = get_text_size(roman, "__")
                draw.text([rating_x + under_width * 11 // 10, rating_y],
                          "/" + str(rates[number]), font=roman, fill=(0, 0, 0, 255), anchor='ls')
                scheme_lines.append(f"{boxes_x} {yc_number - margin_h} 0 {rating_x} {rating_y}")

    # Нижняя черта
    draw.line([margin_left_lines - margin_w, field_hh * (problems_in_column + 2) + margin_h,
               width - margin_left_lines + margin_w, field_hh * (problems_in_column + 2) + margin_h],
              fill=(0, 0, 0), width=2)

    total_test = sum(rates[:test_problems])
    total_part2 = sum(rates[test_problems:])
    total_all = total_test + total_part2

    draw.text((margin_left_headers, margin_top + field_hh * (problems_in_column + 2) + margin_h),
              f"Тест: __ /{total_test}", font=roman, fill=(0, 0, 0, 255))
    test_width, _ = get_text_size(roman, "Тест: __ /000")
    draw.text((margin_left_headers + test_width + interrates_spacing,
               margin_top + field_hh * (problems_in_column + 2) + margin_h),
              f"II часть: __ /{total_part2}", font=roman, fill=(0, 0, 0, 255))
    draw.text((width - margin_left_headers,
               margin_top + field_hh * (problems_in_column + 2) + margin_h),
              f"Сумма: __ /{total_all}", font=roman, fill=(0, 0, 0, 255), anchor='ra')

    image.save(output_path)

    # Сохраняем схему
    scheme_path = os.path.splitext(output_path)[0] + ".set"
    with open(scheme_path, 'w', encoding='utf-8') as f:
        f.write(' '.join(problems_names) + '\n')
        f.write(' '.join(map(str, rates)) + '\n')
        f.write(' '.join(map(str, check_keys)) + '\n')
        f.write(f"{width} {height}\n")
        f.write(str(marker_size * marker_size / width / height) + '\n')
        f.write(f"{field_w} {field_h} {margin_w} {margin_h}\n")
        f.write(' '.join(map(str, var_place)) + '\n')
        for line in scheme_lines[1:]:
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