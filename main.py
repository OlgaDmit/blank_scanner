import cv2
import sys
import os
import glob
import json
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

# Импорт ваших модулей
from process_frame import process_frame
from blank_reader import print_score_on_blank
from blank_generator import generate_custom_template

# ----------------------------------------------------------------------
#  функции сохранения / масштабирования (без изменений)
# ----------------------------------------------------------------------
def save_result(score):
    for item in score:
        print(str(item[0]) + '\t', end='')
    print('', flush=True)

def save_settings(path_arr, scaling, sharpness):
    x, y, w, h = scaling[:]
    with open('.blank_ocr_config', 'w') as f:
        f.write(f'scaling: {x} {y} {w} {h}\n')
        f.write(f'sharpness: {sharpness}\n')
        for line in path_arr:
            f.write(line + '\n')

def scale_image(key, x, y, w, h, original_sizes, velocity=10):
    if key == 'Up' and y > 0:
        y -= velocity
        if y < 0: y = 0
    elif key == 'Down' and y + h < original_sizes[0]:
        y += velocity
        if y + h > original_sizes[0]: y = original_sizes[0] - h
    elif key == 'Left' and x > 0:
        x -= velocity
        if x < 0: x = 0
    elif key == 'Right' and x + w < original_sizes[1]:
        x += velocity
        if x + w > original_sizes[1]: x = original_sizes[1] - w
    elif key == 'minus' and w > 1:
        x += w // 20
        y += h // 20
        w = w * 9 // 10
        h = h * 9 // 10
    elif key == 'plus':
        w = w * 10 // 9
        h = h * 10 // 9
        x -= w // 18
        y -= h // 18
        while x < 0: x += 1
        while y < 0: y += 1
        while x + w > original_sizes[1] and x > 0: x -= 1
        while y + h > original_sizes[0] and y > 0: y -= 1
        if x + w > original_sizes[1]: w = original_sizes[1] - x
        if y + h > original_sizes[0]: h = original_sizes[0] - y
    return [x, y, w, h]

# ----------------------------------------------------------------------
#  загрузка конфигурации и рабочей папки
# ----------------------------------------------------------------------
def load_config():
    path_arr = []
    scaling = None
    sharpness = 1.0
    try:
        with open('.blank_ocr_config', 'r') as f:
            for line in f:
                if line.startswith('scaling'):
                    parts = list(map(int, line.split()[1:5]))
                    if len(parts) == 4:
                        scaling = parts
                elif line.startswith('sharpness'):
                    sharpness = float(line.split()[1])
                else:
                    path = line.strip()
                    if os.path.isdir(path):
                        path_arr.append(path)
    except FileNotFoundError:
        pass
    return path_arr, scaling, sharpness

def load_blank_scheme(current_path):
    # Ищем файл .set в папке
    search_pattern = os.path.join(current_path, "*.set")
    config_files = glob.glob(search_pattern)
    if not config_files:
        # Если нет .set, ищем .txt
        config_files = glob.glob(os.path.join(current_path, "*.txt"))
        if not config_files:
            return None
    # Берём первый найденный файл
    scheme_file = config_files[0]
    try:
        with open(scheme_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Проверяем, похоже ли на схему (должно быть много строк с числами)
        if len(lines) >= 7 and lines[4].strip().replace('.', '').isdigit():
            # Это полноценный файл схемы (как blank_template.txt)
            blank_scheme = {}
            blank_scheme['problems_names'] = lines[0].strip().split()
            blank_scheme['rates'] = list(map(int, lines[1].strip().split()))
            blank_scheme['check_keys'] = list(map(int, lines[2].strip().split()))
            blank_scheme['image_size'] = list(map(int, lines[3].strip().split()))
            blank_scheme['max_area'] = float(lines[4].strip())
            blank_scheme['field_sizes'] = list(map(int, lines[5].strip().split()))
            blank_scheme['var_coords'] = list(map(int, lines[6].strip().split()))
            blank_scheme['problems_coords'] = []
            blank_scheme['rates_coords'] = []
            for line in lines[7:]:
                if line.strip():
                    parts = list(map(int, line.strip().split()))
                    blank_scheme['problems_coords'].append(parts[:3])
                    blank_scheme['rates_coords'].append(parts[3:])
            return blank_scheme
        else:
            # Старый формат: первая строка — имя файла схемы
            scheme_filename = lines[0].strip()
            full_scheme_path = os.path.join(current_path, scheme_filename)
            if not os.path.isfile(full_scheme_path):
                return None
            with open(full_scheme_path, 'r', encoding='utf-8') as g:
                # Читаем как выше
                blank_scheme = {}
                blank_scheme['problems_names'] = g.readline().strip().split()
                blank_scheme['rates'] = list(map(int, g.readline().split()))
                blank_scheme['check_keys'] = list(map(int, g.readline().split()))
                blank_scheme['image_size'] = list(map(int, g.readline().split()))
                blank_scheme['max_area'] = float(g.readline())
                blank_scheme['field_sizes'] = list(map(int, g.readline().split()))
                blank_scheme['var_coords'] = list(map(int, g.readline().split()))
                blank_scheme['problems_coords'] = []
                blank_scheme['rates_coords'] = []
                for line in g:
                    parts = list(map(int, line.strip().split()))
                    blank_scheme['problems_coords'].append(parts[:3])
                    blank_scheme['rates_coords'].append(parts[3:])
                return blank_scheme
    except Exception as e:
        print(f"Ошибка загрузки схемы: {e}")
        return None
# ----------------------------------------------------------------------
#  GUI-приложение
# ----------------------------------------------------------------------
class BlankOCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Распознавание бланков")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # --- загружаем сохранённые данные ---
        self.path_arr, saved_scaling, self.sharpness = load_config()
        if len(self.path_arr) > 10:
            self.path_arr = self.path_arr[:10]
        self.current_path = None
        self.blank_scheme = None

        # --- параметры кадрирования ---
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
        self.original_sizes = (0, 0)

        # --- захват камеры (исправлено для Windows) ---
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            messagebox.showerror("Ошибка", "Не удалось открыть камеру")
            sys.exit(1)

        ret, frame = self.cap.read()
        if ret:
            self.original_sizes = frame.shape[:2]
            if saved_scaling and self.is_scaling_valid(saved_scaling):
                self.x, self.y, self.w, self.h = saved_scaling
            else:
                self.x = 0
                self.y = 0
                self.w = self.original_sizes[1]
                self.h = self.w // 2

        # --- атрибуты для сохранения результатов ---
        self.last_recognized_answers = None
        self.last_score = None

        # --- создание виджетов ---
        self.video_label = tk.Label(root)
        self.video_label.pack()

        control_frame = tk.Frame(root)
        control_frame.pack(pady=10, fill=tk.X, padx=10)

        self.folder_label = tk.Label(control_frame, text="Текущая папка: не выбрана", anchor='w')
        self.folder_label.pack(fill=tk.X, pady=2)

        folder_sel_frame = tk.Frame(control_frame)
        folder_sel_frame.pack(fill=tk.X, pady=5)

        tk.Label(folder_sel_frame, text="Рабочая папка:").pack(side=tk.LEFT)
        self.folder_combo = ttk.Combobox(folder_sel_frame, values=self.path_arr, state='normal')
        self.folder_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.folder_combo.bind('<Return>', self.on_folder_enter)
        self.folder_combo.bind('<<ComboboxSelected>>', self.on_folder_select)

        self.choose_btn = tk.Button(folder_sel_frame, text="Выбрать папку", command=self.choose_folder_dialog)
        self.choose_btn.pack(side=tk.LEFT, padx=5)

        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(pady=5)

        self.scan_btn = tk.Button(btn_frame, text="Начать сканирование", command=self.start_scan)
        self.scan_btn.pack(side=tk.LEFT, padx=10)

        self.generate_btn = tk.Button(btn_frame, text="Создать бланк", command=self.open_template_dialog)
        self.generate_btn.pack(side=tk.LEFT, padx=10)

        self.save_btn = tk.Button(btn_frame, text="Сохранить результаты", command=self.on_save_results, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=10)

        # --- привязка клавиш ---
        self.root.bind('<Up>', lambda e: self.on_key('Up'))
        self.root.bind('<Down>', lambda e: self.on_key('Down'))
        self.root.bind('<Left>', lambda e: self.on_key('Left'))
        self.root.bind('<Right>', lambda e: self.on_key('Right'))
        self.root.bind('<plus>', lambda e: self.on_key('plus'))
        self.root.bind('<minus>', lambda e: self.on_key('minus'))
        self.root.bind('<Return>', lambda e: self.start_scan())
        self.root.bind('<Escape>', lambda e: self.on_close())

        self.choose_initial_folder()

        self.update_video()

    def is_scaling_valid(self, scaling):
        x, y, w, h = scaling
        return (0 <= x < self.original_sizes[1] and
                0 <= y < self.original_sizes[0] and
                0 < w <= self.original_sizes[1] - x and
                0 < h <= self.original_sizes[0] - y)

    def update_folder_label(self):
        if self.current_path:
            self.folder_label.config(text=f"Текущая папка: {self.current_path}")
        else:
            self.folder_label.config(text="Текущая папка: не выбрана")

    def update_combo_list(self):
        self.folder_combo['values'] = self.path_arr
        if self.current_path and self.current_path in self.path_arr:
            self.folder_combo.set(self.current_path)
        elif self.current_path:
            self.folder_combo.set(self.current_path)
        else:
            self.folder_combo.set('')

    def choose_initial_folder(self):
        if self.current_path is not None:
            return
        if self.path_arr:
            self.set_current_path(self.path_arr[0])
        else:
            self.choose_folder_dialog()

    def set_current_path(self, new_path):
        if not os.path.isdir(new_path):
            messagebox.showerror("Ошибка", f"Папка не существует: {new_path}")
            return False
        self.current_path = new_path
        if self.current_path in self.path_arr:
            self.path_arr.remove(self.current_path)
        self.path_arr.insert(0, self.current_path)
        if len(self.path_arr) > 10:
            self.path_arr = self.path_arr[:10]
        self.update_combo_list()
        self.update_folder_label()
        self.blank_scheme = load_blank_scheme(self.current_path)
        if self.blank_scheme is None:
            messagebox.showerror("Ошибка", f"В папке {self.current_path} нет корректного .set файла.\nВыберите другую папку.")
            self.blank_scheme = None
            return False
        save_settings(self.path_arr, [self.x, self.y, self.w, self.h], self.sharpness)
        return True

    def on_folder_select(self, event=None):
        selected = self.folder_combo.get()
        if selected and os.path.isdir(selected):
            self.set_current_path(selected)
        elif selected:
            messagebox.showerror("Ошибка", f"Папка не существует: {selected}")

    def on_folder_enter(self, event=None):
        path = self.folder_combo.get().strip()
        if not path:
            return
        if os.path.isdir(path):
            self.set_current_path(path)
        else:
            answer = messagebox.askyesno("Папка не найдена",
                                         f"Папка '{path}' не существует.\nХотите выбрать папку через диалог?")
            if answer:
                self.choose_folder_dialog()

    def choose_folder_dialog(self):
        new_path = filedialog.askdirectory(title="Выберите рабочую папку")
        if new_path:
            self.set_current_path(new_path)

    def update_video(self):
        ret, frame = self.cap.read()
        if ret:
            cropped = frame[self.y:self.y+self.h, self.x:self.x+self.w]
            rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.config(image=imgtk)
        self.root.after(30, self.update_video)

    def on_key(self, key):
        new_rect = scale_image(key, self.x, self.y, self.w, self.h,
                               self.original_sizes, velocity=10)
        self.x, self.y, self.w, self.h = new_rect
        save_settings(self.path_arr, [self.x, self.y, self.w, self.h], self.sharpness)

    def start_scan(self):
        if self.blank_scheme is None:
            messagebox.showwarning("Предупреждение", "Сначала выберите рабочую папку с настройками бланка.")
            return
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Ошибка", "Не удалось получить кадр с камеры.")
            return
        cropped = frame[self.y:self.y+self.h, self.x:self.x+self.w]
        # process_frame теперь возвращает (score, sharpness, recognized_answers)
        score, new_sharpness, recognized_answers = process_frame(cropped, self.blank_scheme, self.current_path, self.sharpness)
        self.sharpness = new_sharpness
        save_settings(self.path_arr, [self.x, self.y, self.w, self.h], self.sharpness)
        if score:
            self.last_recognized_answers = recognized_answers
            self.last_score = score
            self.save_btn.config(state=tk.NORMAL)
            save_result(score)
            msg = "\n".join(f"{i+1}: {p[0]} {'+' if p[1] else '-'}" for i, p in enumerate(score))
            messagebox.showinfo("Результат", f"Распознано {len(score)} заданий.\n\n" + msg)
        else:
            messagebox.showwarning("Результат", "Ничего не распознано.")

    def on_save_results(self):
        if self.last_recognized_answers is None:
            messagebox.showwarning("Нет данных", "Сначала выполните сканирование.")
            return
        self.save_results_dialog(self.last_recognized_answers, self.last_score)

    def save_results_dialog(self, recognized_answers, score):
        if not recognized_answers:
            messagebox.showwarning("Нет данных", "Нет результатов для сохранения.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Сохранение результатов")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()

        student_name_var = tk.StringVar()
        folder_var = tk.StringVar(value=self.current_path if self.current_path else "")
        format_var = tk.StringVar(value="TXT")

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Имя ученика / ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=student_name_var, width=30).grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(main_frame, text="Папка для сохранения:").grid(row=1, column=0, sticky=tk.W, pady=5)
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Entry(folder_frame, textvariable=folder_var, width=30).pack(side=tk.LEFT)
        ttk.Button(folder_frame, text="Обзор", command=lambda: self._browse_folder(folder_var)).pack(side=tk.LEFT, padx=5)

        ttk.Label(main_frame, text="Формат:").grid(row=2, column=0, sticky=tk.W, pady=5)
        format_combo = ttk.Combobox(main_frame, textvariable=format_var, values=["TXT", "CSV", "JSON"], state="readonly")
        format_combo.grid(row=2, column=1, sticky=tk.W, pady=5)

        def do_save():
            folder = folder_var.get()
            if not folder:
                messagebox.showerror("Ошибка", "Выберите папку для сохранения.")
                return
            if not os.path.isdir(folder):
                try:
                    os.makedirs(folder)
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось создать папку:\n{e}")
                    return

            student = student_name_var.get().strip()
            if not student:
                student = "unknown"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"{student}_{timestamp}"

            variant = ''.join(recognized_answers[0]).strip() if recognized_answers else "???"
            answers = recognized_answers[1:] if len(recognized_answers) > 1 else []
            scores = score if score else []

            data = {
                "student": student,
                "timestamp": timestamp,
                "datetime": datetime.now().isoformat(),
                "variant": variant,
                "answers": {},
                "scores": {}
            }
            for i, ans in enumerate(answers, 1):
                data["answers"][f"task_{i}"] = ''.join(ans).strip()
            for i, (points, is_correct) in enumerate(scores, 1):
                data["scores"][f"task_{i}"] = {"points": points, "correct": is_correct}
            data["total_points"] = sum(p for p, _ in scores) if scores else None

            file_path = os.path.join(folder, base_name)
            try:
                if format_var.get() == "TXT":
                    file_path += ".txt"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"Ученик: {student}\n")
                        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Вариант: {variant}\n\n")
                        f.write("Ответы:\n")
                        for i, ans in enumerate(answers, 1):
                            ans_str = ''.join(ans).strip() or "—"
                            f.write(f"  {i:2d}: {ans_str}\n")
                        if scores:
                            f.write("\nБаллы:\n")
                            for i, (points, correct) in enumerate(scores, 1):
                                status = "+" if correct else "-"
                                f.write(f"  {i:2d}: {points} {status}\n")
                            f.write(f"\nСумма баллов: {sum(p for p,_ in scores)}\n")
                elif format_var.get() == "CSV":
                    file_path += ".csv"
                    with open(file_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(["student", "timestamp", "variant"] + [f"task_{i}" for i in range(1, len(answers)+1)] + [f"score_{i}" for i in range(1, len(scores)+1)] + ["total"])
                        row = [student, timestamp, variant] + [''.join(a).strip() for a in answers] + [p for p,_ in scores] + [sum(p for p,_ in scores)]
                        writer.writerow(row)
                else:  # JSON
                    file_path += ".json"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Успех", f"Результаты сохранены в:\n{file_path}")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Сохранить", command=do_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _browse_folder(self, var):
        folder = filedialog.askdirectory(title="Выберите папку для сохранения результатов")
        if folder:
            var.set(folder)

    def open_template_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание шаблона бланка")
        dialog.geometry("950x750")
        dialog.transient(self.root)
        dialog.grab_set()

        # Переменные
        title_var = tk.StringVar(value="ЕГЭ 2026")
        problems_var = tk.IntVar(value=27)
        test_problems_var = tk.IntVar(value=20)
        fields_number_var = tk.IntVar(value=10)
        columns_var = tk.IntVar(value=3)
        problems_in_column_var = tk.IntVar(value=10)

        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="Название экзамена:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(frame, textvariable=title_var, width=30).grid(row=row, column=1, pady=2)
        row += 1

        ttk.Label(frame, text="Общее количество заданий:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(frame, from_=1, to=100, textvariable=problems_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1

        ttk.Label(frame, text="Заданий в тестовой части:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(frame, from_=0, to=100, textvariable=test_problems_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1

        ttk.Label(frame, text="Количество клеток для ответа:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(frame, from_=1, to=20, textvariable=fields_number_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1

        ttk.Label(frame, text="Количество столбцов:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(frame, from_=1, to=5, textvariable=columns_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1

        ttk.Label(frame, text="Заданий в столбце:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(frame, from_=1, to=30, textvariable=problems_in_column_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1

        # Баллы
        ttk.Label(frame, text="Баллы (через запятую):").grid(row=row, column=0, sticky=tk.NW, pady=2)
        scores_text = tk.Text(frame, height=6, width=30)
        scores_text.grid(row=row, column=1, pady=2, sticky=tk.W)
        scores_text.insert(tk.END, "1,1,1,1,2,2,1,1,2,2,1,1,1,2,2,1,2,2,1,1,3,2,2,3,3,3,1")
        row += 1

        # Типы проверки (вручную)
        ttk.Label(frame, text="Типы проверки (через запятую, 1/2/3/0):").grid(row=row, column=0, sticky=tk.NW, pady=2)
        check_keys_entry = ttk.Entry(frame, width=30)
        check_keys_entry.grid(row=row, column=1, pady=2, sticky=tk.W)
        row += 1

        # Функция автозаполнения типов по баллам (с учётом test_problems)
        def auto_fill_check_keys():
            try:
                scores_str = scores_text.get("1.0", tk.END).strip()
                if not scores_str:
                    return
                rates = list(map(int, scores_str.replace(',', ' ').split()))
                problems = problems_var.get()
                if len(rates) < problems:
                    rates += [1] * (problems - len(rates))
                rates = rates[:problems]
                test_problems = test_problems_var.get()
                ck = []
                for i, r in enumerate(rates):
                    if i >= test_problems:
                        ck.append(0)
                    else:
                        if r == 1:
                            ck.append(1)
                        elif r == 2:
                            ck.append(2)
                        elif r >= 3:
                            ck.append(3)
                        else:
                            ck.append(0)
                check_keys_entry.delete(0, tk.END)
                check_keys_entry.insert(0, ','.join(map(str, ck)))
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сгенерировать типы: {e}")

        ttk.Button(frame, text="Сгенерировать типы по баллам (тестовая часть → 1/2/3, остальные → 0)",
                command=auto_fill_check_keys).grid(row=row, column=1, pady=5, sticky=tk.W)
        row += 1

        # Предпросмотр
        preview_label = ttk.Label(frame, text="Предпросмотр будет здесь", relief=tk.SUNKEN)
        preview_label.grid(row=0, column=2, rowspan=row, padx=20, sticky=tk.NSEW)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(0, weight=1)

        def update_preview():
            try:
                problems = problems_var.get()
                test_problems = test_problems_var.get()
                fields_number = fields_number_var.get()
                columns = columns_var.get()
                problems_in_column = problems_in_column_var.get()
                scores_str = scores_text.get("1.0", tk.END).strip()
                rates = list(map(int, scores_str.replace(',', ' ').split()))
                if len(rates) < problems:
                    rates += [1] * (problems - len(rates))
                rates = rates[:problems]

                # Парсим check_keys из поля ввода
                ck_str = check_keys_entry.get().strip()
                if ck_str:
                    check_keys = list(map(int, ck_str.replace(',', ' ').split()))
                    if len(check_keys) < problems:
                        check_keys += [0] * (problems - len(check_keys))
                    check_keys = check_keys[:problems]
                else:
                    check_keys = None  # будет авто-генерация в generate_custom_template

                temp_path = "temp_preview.png"
                generate_custom_template(
                    output_path=temp_path,
                    title_text=title_var.get(),
                    problems=problems,
                    test_problems=test_problems,
                    rates=rates,
                    check_keys=check_keys,
                    problems_in_column=problems_in_column,
                    columns=columns,
                    fields_number=fields_number,
                    problems_names=[str(i) for i in range(1, problems+1)]
                )
                img = Image.open(temp_path)
                img.thumbnail((400, 400))
                imgtk = ImageTk.PhotoImage(img)
                preview_label.config(image=imgtk, text="")
                preview_label.image = imgtk
                os.remove(temp_path)
            except Exception as e:
                preview_label.config(text=f"Ошибка: {e}")

        ttk.Button(frame, text="Предпросмотр", command=update_preview).grid(row=row, column=1, pady=5, sticky=tk.W)
        row += 1

        def do_generate():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG images", "*.png"), ("All files", "*.*")]
            )
            if not file_path:
                return
            try:
                problems = problems_var.get()
                test_problems = test_problems_var.get()
                fields_number = fields_number_var.get()
                columns = columns_var.get()
                problems_in_column = problems_in_column_var.get()
                scores_str = scores_text.get("1.0", tk.END).strip()
                rates = list(map(int, scores_str.replace(',', ' ').split()))
                if len(rates) < problems:
                    rates += [1] * (problems - len(rates))
                rates = rates[:problems]

                ck_str = check_keys_entry.get().strip()
                if ck_str:
                    check_keys = list(map(int, ck_str.replace(',', ' ').split()))
                    if len(check_keys) < problems:
                        check_keys += [0] * (problems - len(check_keys))
                    check_keys = check_keys[:problems]
                else:
                    check_keys = None

                generate_custom_template(
                    output_path=file_path,
                    title_text=title_var.get(),
                    problems=problems,
                    test_problems=test_problems,
                    rates=rates,
                    check_keys=check_keys,
                    problems_in_column=problems_in_column,
                    columns=columns,
                    fields_number=fields_number,
                    problems_names=[str(i) for i in range(1, problems+1)]
                )
                messagebox.showinfo("Успех", f"Шаблон сохранён:\n{file_path}")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Сгенерировать", command=do_generate).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def on_close(self):
        if self.cap:
            self.cap.release()
        self.root.destroy()


if __name__ == "__main__":
    # Подавление предупреждений oneDNN (опционально)
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

    root = tk.Tk()
    app = BlankOCRApp(root)
    root.mainloop()