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

TEMPLATES_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates_storage")
TEMPLATES_INDEX = os.path.join(TEMPLATES_STORAGE, "templates_index.json")

# Создаём папку для хранения шаблонов, если её нет
os.makedirs(TEMPLATES_STORAGE, exist_ok=True)

# ----------------------------------------------------------------------
#  ФУНКЦИИ ДЛЯ РАБОТЫ С ХРАНИЛИЩЕМ ШАБЛОНОВ (ВСТАВИТЬ СЮДА)
# ----------------------------------------------------------------------
def save_template_to_storage(template_path, template_name=None):
    """Сохраняет шаблон во внутреннее хранилище и возвращает его ID."""
    try:
        # Если имя не указано, запрашиваем у пользователя
        if not template_name:
            from tkinter import simpledialog
            template_name = simpledialog.askstring(
                "Название шаблона",
                "Введите название для шаблона (например: ЕГЭ 2026 профиль):",
                parent=tk._default_root
            )
            if not template_name:
                template_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Копируем .png и .set файлы в хранилище
        png_file = template_path
        set_file = os.path.splitext(template_path)[0] + ".set"
        
        if not os.path.exists(png_file) or not os.path.exists(set_file):
            print(f"Ошибка: файлы шаблона не найдены: {png_file}, {set_file}")
            return None
        
        # Создаём папку для этого шаблона в хранилище (используем имя с временной меткой)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = template_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        folder_name = f"{safe_name}_{timestamp}"
        template_folder = os.path.join(TEMPLATES_STORAGE, folder_name)
        os.makedirs(template_folder, exist_ok=True)
        
        # Копируем файлы
        import shutil
        dest_png = os.path.join(template_folder, "blank.png")
        dest_set = os.path.join(template_folder, "blank.set")
        
        shutil.copy2(png_file, dest_png)
        shutil.copy2(set_file, dest_set)
        
        # Обновляем индекс
        index = load_templates_index()
        template_id = folder_name
        index[template_id] = {
            "name": template_name,
            "folder": folder_name,
            "path": template_folder,
            "created": datetime.now().isoformat(),
            "original_path": template_path
        }
        save_templates_index(index)
        
        return template_id
    except Exception as e:
        print(f"Ошибка сохранения шаблона в хранилище: {e}")
        return None

def copy_template_to_work_folder(template_id, target_folder):
    """Копирует шаблон из хранилища в указанную рабочую папку."""
    index = load_templates_index()
    if template_id not in index:
        return False, "Шаблон не найден"
    
    template_info = index[template_id]
    source_folder = template_info["path"]
    
    source_png = os.path.join(source_folder, "blank.png")
    source_set = os.path.join(source_folder, "blank.set")
    
    if not os.path.exists(source_png) or not os.path.exists(source_set):
        return False, "Файлы шаблона повреждены"
    
    import shutil
    # Копируем в целевую папку
    dest_png = os.path.join(target_folder, "blank_template.png")
    dest_set = os.path.join(target_folder, os.path.basename(source_set))
    
    shutil.copy2(source_png, dest_png)
    shutil.copy2(source_set, dest_set)
    
    return True, "Шаблон скопирован успешно"
def load_templates_index():
    """Загружает индекс всех сохранённых шаблонов."""
    if os.path.exists(TEMPLATES_INDEX):
        try:
            with open(TEMPLATES_INDEX, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_templates_index(index):
    """Сохраняет индекс шаблонов."""
    try:
        with open(TEMPLATES_INDEX, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка сохранения индекса шаблонов: {e}")

def get_recent_templates(limit=10):
    """Возвращает список недавних шаблонов."""
    index = load_templates_index()
    # Сортируем по дате создания (новые сначала)
    sorted_templates = sorted(
        index.items(),
        key=lambda x: x[1].get("created", ""),
        reverse=True
    )
    return sorted_templates[:limit]

def load_template_from_storage(template_id):
    """Загружает шаблон из хранилища по ID."""
    index = load_templates_index()
    if template_id not in index:
        return None
    template_info = index[template_id]
    set_file = os.path.join(template_info["path"], "blank.set")
    if os.path.exists(set_file):
        return load_blank_scheme(template_info["path"])
    return None

def delete_template_from_storage(template_id):
    """Удаляет шаблон из хранилища."""
    index = load_templates_index()
    if template_id in index:
        import shutil
        template_path = index[template_id]["path"]
        if os.path.exists(template_path):
            shutil.rmtree(template_path)
        del index[template_id]
        save_templates_index(index)
        return True
    return False
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

        # Ищем файлы .set в папке
        set_files = glob.glob(os.path.join(new_path, "*.set"))
        
        if not set_files:
            # Спрашиваем, что делать
            answer = messagebox.askyesnocancel(
                "Схема не найдена",
                f"В папке '{os.path.basename(new_path)}' нет файла схемы (.set).\n\n"
                "Что вы хотите сделать?\n\n"
                "• Да — создать новый шаблон бланка\n"
                "• Нет — указать существующий файл схемы\n"
                "• Отмена — отменить выбор папки"
            )
            
            if answer is None:  # Отмена
                return False
            elif answer:  # Да — создать новый шаблон
                self.open_template_dialog(default_folder=new_path)
                # После создания шаблона проверяем, появился ли .set файл
                set_files = glob.glob(os.path.join(new_path, "*.set"))
                if not set_files:
                    messagebox.showwarning("Внимание", "Шаблон не был создан. Папка не выбрана.")
                    return False
            else:  # Нет — выбрать существующий файл .set
                set_file = filedialog.askopenfilename(
                    title="Выберите файл схемы (.set)",
                    initialdir=new_path,
                    filetypes=[("Файлы схемы", "*.set"), ("Все файлы", "*.*")]
                )
                if not set_file:
                    return False
                # Копируем в папку для единообразия
                import shutil
                target = os.path.join(new_path, os.path.basename(set_file))
                if set_file != target:
                    shutil.copy2(set_file, target)
                set_files = [target]
        
        # Если дошли сюда – папка подходит (есть .set)
        self.current_path = new_path
        if self.current_path in self.path_arr:
            self.path_arr.remove(self.current_path)
        self.path_arr.insert(0, self.current_path)
        if len(self.path_arr) > 10:
            self.path_arr = self.path_arr[:10]
        self.update_combo_list()
        self.update_folder_label()

        # Загружаем схему
        self.blank_scheme = load_blank_scheme(self.current_path)
        if self.blank_scheme is None:
            messagebox.showerror("Ошибка", f"Не удалось загрузить схему из папки {self.current_path}.")
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
    # Сначала спрашиваем, хочет ли пользователь выбрать из сохранённых шаблонов
        answer = messagebox.askyesnocancel(
            "Выбор рабочей папки",
            "Как вы хотите выбрать рабочую папку?\n\n"
            "• Да — выбрать шаблон из библиотеки и создать для него папку\n"
            "• Нет — выбрать существующую папку с бланками\n"
            "• Отмена — отменить"
        )
        
        if answer is None:
            return
        elif answer:
            # Выбор из сохранённых шаблонов
            recent = get_recent_templates()
            if not recent:
                messagebox.showinfo("Нет шаблонов", "У вас пока нет сохранённых шаблонов.\nСначала создайте шаблон.")
                return
            
            select_win = tk.Toplevel(self.root)
            select_win.title("Выбор шаблона из библиотеки")
            select_win.geometry("500x450")
            select_win.transient(self.root)
            select_win.grab_set()
            
            tk.Label(select_win, text="Выберите шаблон:", font=("Arial", 12)).pack(pady=10)
            
            frame = ttk.Frame(select_win)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Arial", 10), height=10)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=listbox.yview)
            
            # Храним соответствие между отображаемым текстом и ID
            template_map = {}
            for template_id, info in recent:
                created = info.get("created", "Unknown")[:19]
                display_text = f"{info['name']} (создан: {created})"
                listbox.insert(tk.END, display_text)
                template_map[display_text] = template_id
            
            def on_select():
                selection = listbox.curselection()
                if not selection:
                    return
                display_text = listbox.get(selection[0])
                template_id = template_map[display_text]
                
                # Спрашиваем, куда скопировать шаблон
                target_folder = filedialog.askdirectory(
                    title="Выберите папку для создания рабочей области с этим шаблоном"
                )
                if not target_folder:
                    return
                
                # Копируем шаблон в выбранную папку
                success, msg = copy_template_to_work_folder(template_id, target_folder)
                if success:
                    messagebox.showinfo("Успех", f"Шаблон скопирован в папку:\n{target_folder}")
                    # Устанавливаем эту папку как рабочую
                    self.set_current_path(target_folder)
                    select_win.destroy()
                else:
                    messagebox.showerror("Ошибка", msg)
            
            ttk.Button(select_win, text="Выбрать и скопировать в новую папку", command=on_select).pack(pady=10)
            ttk.Button(select_win, text="Отмена", command=select_win.destroy).pack(pady=5)
        else:
            # Обычный выбор папки
            new_path = filedialog.askdirectory(title="Выберите рабочую папку с бланками")
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
            
            # Создаём окно с результатами
            result_win = tk.Toplevel(self.root)
            result_win.title("Результаты распознавания")
            result_win.geometry("400x500")
            result_win.transient(self.root)
            result_win.grab_set()
            
            def on_esc(event):
                result_win.destroy()
            
            result_win.bind('<Escape>', on_esc)
            result_win.focus_set()
            
            # Текст с результатами
            text_widget = tk.Text(result_win, wrap=tk.WORD, font=("Courier", 10))
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(text_widget)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=text_widget.yview)
            
            msg = f"Распознано {len(score)} заданий\n\n"
            for i, (points, is_correct) in enumerate(score, 1):
                status = "+" if is_correct else "-"
                msg += f"{i:2d}: {points} {status}\n"
            
            text_widget.insert(tk.END, msg)
            text_widget.config(state=tk.DISABLED)
            
            # Кнопка закрытия
            close_btn = ttk.Button(result_win, text="Закрыть (ESC)", command=result_win.destroy)
            close_btn.pack(pady=10)
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

    def open_template_dialog(self, default_folder=None):
        """Диалог создания шаблона с табличным редактором названий заданий."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание шаблона бланка")
        dialog.geometry("1200x900")
        dialog.minsize(900, 700)
        dialog.transient(self.root)
        dialog.grab_set()

        # ----- Переменные -----
        title_var = tk.StringVar(value="ЕГЭ 2026")
        problems_var = tk.StringVar(value="27")
        test_problems_var = tk.StringVar(value="20")
        fields_number_var = tk.IntVar(value=10)
        columns_var = tk.IntVar(value=3)
        problems_in_column_var = tk.IntVar(value=10)

        # Валидация
        def validate_int(value):
            return value == "" or (value.isdigit() and int(value) >= 1)
        vcmd = (dialog.register(lambda p: validate_int(p)), '%P')

        # Функция пересчёта столбцов
        def update_columns(*args):
            problems_str = problems_var.get().strip()
            if not problems_str:
                return
            try:
                problems = int(problems_str)
                rows = problems_in_column_var.get()
                if rows > 0:
                    new_cols = (problems + rows - 1) // rows
                    columns_var.set(new_cols)
            except:
                pass

        problems_var.trace_add('write', update_columns)
        problems_in_column_var.trace_add('write', update_columns)

        # Обновление полей
        def update_names_field():
            total_str = problems_var.get().strip()
            if not total_str:
                return
            try:
                total = int(total_str)
            except:
                return
            current_text = names_text.get("1.0", tk.END).strip()
            parts = [p.strip() for p in current_text.split(',') if p.strip()]
            name_dict = {}
            for idx, name in enumerate(parts, start=1):
                if idx <= total:
                    name_dict[idx] = name
            new_names = []
            for i in range(1, total + 1):
                if i in name_dict:
                    new_names.append(name_dict[i])
                else:
                    new_names.append(str(i))
            names_text.delete("1.0", tk.END)
            names_text.insert(tk.END, ', '.join(new_names))

        def refresh_scores_and_checks():
            total_str = problems_var.get().strip()
            if not total_str:
                return
            try:
                total = int(total_str)
            except:
                return
            test_str = test_problems_var.get().strip()
            test = int(test_str) if test_str else 0
            if test > total:
                test = total
                test_problems_var.set(str(test))

            try:
                current_scores = list(map(int, scores_text.get("1.0", tk.END).strip().replace(',', ' ').split()))
            except:
                current_scores = []
            if len(current_scores) < total:
                current_scores += [2] * (total - len(current_scores))
            else:
                current_scores = current_scores[:total]

            try:
                current_checks = list(map(int, check_text.get("1.0", tk.END).strip().replace(',', ' ').split()))
            except:
                current_checks = []
            if len(current_checks) < total:
                for i in range(len(current_checks), total):
                    current_checks.append(2 if i < test else 0)
            else:
                current_checks = current_checks[:total]

            for i in range(total):
                if i < test:
                    if current_checks[i] == 0:
                        current_checks[i] = 2
                else:
                    if current_checks[i] == 2:
                        current_checks[i] = 0

            scores_text.delete("1.0", tk.END)
            scores_text.insert(tk.END, ','.join(map(str, current_scores)))
            check_text.delete("1.0", tk.END)
            check_text.insert(tk.END, ','.join(map(str, current_checks)))
            update_names_field()

        def sync_total_and_test(*args):
            total_str = problems_var.get().strip()
            test_str = test_problems_var.get().strip()
            if not total_str or not test_str:
                return
            try:
                total = int(total_str)
                test = int(test_str)
            except:
                return
            if test > total:
                test_problems_var.set(str(total))
            elif total < test:
                problems_var.set(str(test))
            refresh_scores_and_checks()

        problems_var.trace_add('write', lambda *a: (sync_total_and_test(), update_names_field()))
        test_problems_var.trace_add('write', sync_total_and_test)

        # ----- ПРЕДПРОСМОТР -----
        preview_frame = ttk.LabelFrame(dialog, text="Предпросмотр")
        preview_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        canvas = tk.Canvas(preview_frame, bg='white', highlightthickness=0)
        h_scroll = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        v_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        canvas.grid(row=0, column=0, sticky='nsew')
        h_scroll.grid(row=1, column=0, sticky='ew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        preview_image = None

        def update_preview(event=None):
            nonlocal preview_image
            total_str = problems_var.get().strip()
            test_str = test_problems_var.get().strip()
            if not total_str or not test_str:
                canvas.delete("all")
                canvas.create_text(10, 10, anchor='nw', text="Введите количество заданий", fill='red')
                return
            try:
                total = int(total_str)
                test = int(test_str)
            except:
                return
            fields_number = fields_number_var.get()
            columns = columns_var.get()
            rows = problems_in_column_var.get()
            scores_str = scores_text.get("1.0", tk.END).strip()
            rates = list(map(int, scores_str.replace(',', ' ').split()))
            if len(rates) < total:
                rates += [1] * (total - len(rates))
            rates = rates[:total]
            check_str = check_text.get("1.0", tk.END).strip()
            check_keys = list(map(int, check_str.replace(',', ' ').split()))
            if len(check_keys) < total:
                check_keys += [0] * (total - len(check_keys))
            check_keys = check_keys[:total]

            names_str = names_text.get("1.0", tk.END).strip()
            problems_names = [n.strip() for n in names_str.split(',') if n.strip()]
            if len(problems_names) < total:
                problems_names += [str(i) for i in range(len(problems_names)+1, total+1)]
            problems_names = problems_names[:total]

            temp_path = "temp_preview.png"
            try:
                generate_custom_template(
                    output_path=temp_path,
                    title_text=title_var.get(),
                    problems=total,
                    test_problems=test,
                    rates=rates,
                    check_keys=check_keys,
                    problems_in_column=rows,
                    columns=columns,
                    fields_number=fields_number,
                    problems_names=problems_names
                )
                img = Image.open(temp_path)
                cw = canvas.winfo_width()
                ch = canvas.winfo_height()
                if cw > 10 and ch > 10:
                    img.thumbnail((cw, ch), Image.Resampling.LANCZOS)
                else:
                    img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                preview_image = ImageTk.PhotoImage(img)
                canvas.delete("all")
                canvas.create_image(0, 0, anchor='nw', image=preview_image)
                canvas.config(scrollregion=canvas.bbox('all'))
                os.remove(temp_path)
            except Exception as e:
                canvas.delete("all")
                canvas.create_text(10, 10, anchor='nw', text=f"Ошибка: {e}", fill='red')

        canvas.bind('<Configure>', lambda e: update_preview())

        # ----- ПАНЕЛЬ НАСТРОЕК -----
        settings_frame = ttk.LabelFrame(dialog, text="Параметры шаблона", padding=10)
        settings_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        row = 0
        ttk.Label(settings_frame, text="Название экзамена:").grid(row=row, column=0, sticky=tk.W, pady=2)
        title_entry = ttk.Entry(settings_frame, textvariable=title_var, width=30)
        title_entry.grid(row=row, column=1, pady=2)
        title_entry.bind('<KeyRelease>', lambda e: update_preview())
        row += 1

        ttk.Label(settings_frame, text="Общее количество заданий:").grid(row=row, column=0, sticky=tk.W, pady=2)
        problems_entry = tk.Entry(settings_frame, textvariable=problems_var, validate='key', validatecommand=vcmd, width=10)
        problems_entry.grid(row=row, column=1, sticky=tk.W, pady=2)
        problems_entry.bind('<KeyRelease>', lambda e: (update_names_field(), update_preview()))
        row += 1

        ttk.Label(settings_frame, text="Заданий в тестовой части:").grid(row=row, column=0, sticky=tk.W, pady=2)
        test_entry = tk.Entry(settings_frame, textvariable=test_problems_var, validate='key', validatecommand=vcmd, width=10)
        test_entry.grid(row=row, column=1, sticky=tk.W, pady=2)
        test_entry.bind('<KeyRelease>', lambda e: update_preview())
        row += 1

        ttk.Label(settings_frame, text="Количество клеток для ответа:").grid(row=row, column=0, sticky=tk.W, pady=2)
        cells_spin = ttk.Spinbox(settings_frame, from_=1, to=20, textvariable=fields_number_var, width=10)
        cells_spin.grid(row=row, column=1, sticky=tk.W, pady=2)
        cells_spin.bind('<ButtonRelease-1>', lambda e: update_preview())
        row += 1

        ttk.Label(settings_frame, text="Количество столбцов (авто):").grid(row=row, column=0, sticky=tk.W, pady=2)
        cols_spin = ttk.Spinbox(settings_frame, from_=1, to=10, textvariable=columns_var, width=10, state='readonly')
        cols_spin.grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1

        ttk.Label(settings_frame, text="Заданий в столбце:").grid(row=row, column=0, sticky=tk.W, pady=2)
        rows_spin = ttk.Spinbox(settings_frame, from_=1, to=50, textvariable=problems_in_column_var, width=10)
        rows_spin.grid(row=row, column=1, sticky=tk.W, pady=2)
        rows_spin.bind('<ButtonRelease-1>', lambda e: update_preview())
        row += 1

        ttk.Label(settings_frame, text="Баллы за задания (через запятую):").grid(row=row, column=0, sticky=tk.NW, pady=2)
        scores_text = tk.Text(settings_frame, height=5, width=40)
        scores_text.grid(row=row, column=1, pady=2, sticky=tk.W)
        default_rates = "1,1,1,1,2,2,1,1,2,2,1,1,1,2,2,1,2,2,1,1,3,2,2,3,3,3,1"
        scores_text.insert(tk.END, default_rates)
        scores_text.bind('<KeyRelease>', lambda e: update_preview())
        row += 1

        ttk.Label(settings_frame, text="Типы проверки (через запятую):\n(1-точное,2-таблица,3-множество,0-нет)").grid(row=row, column=0, sticky=tk.NW, pady=2)
        check_text = tk.Text(settings_frame, height=5, width=40)
        check_text.grid(row=row, column=1, pady=2, sticky=tk.W)
        default_check = "1,1,1,1,3,2,1,1,3,2,1,1,1,3,2,1,2,3,1,1,0,0,0,0,0,0,0"
        check_text.insert(tk.END, default_check)
        check_text.bind('<KeyRelease>', lambda e: update_preview())
        row += 1

        # НАЗВАНИЯ ЗАДАНИЙ
        ttk.Label(settings_frame, text="Названия заданий (через запятую):").grid(row=row, column=0, sticky=tk.NW, pady=2)
        names_frame = ttk.Frame(settings_frame)
        names_frame.grid(row=row, column=1, sticky=tk.W, pady=2)
        names_text = tk.Text(names_frame, height=5, width=35)
        names_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def edit_names_dialog():
            total_str = problems_var.get().strip()
            if not total_str or not total_str.isdigit():
                messagebox.showerror("Ошибка", "Сначала укажите корректное количество заданий.")
                return
            total = int(total_str)
            current_text = names_text.get("1.0", tk.END).strip()
            names_list = [n.strip() for n in current_text.split(',') if n.strip()]
            if len(names_list) < total:
                names_list += [str(i) for i in range(len(names_list)+1, total+1)]
            names_list = names_list[:total]

            edit_win = tk.Toplevel(dialog)
            edit_win.title("Редактирование названий заданий")
            edit_win.geometry("400x500")
            edit_win.transient(dialog)
            edit_win.grab_set()

            canvas_edit = tk.Canvas(edit_win, borderwidth=0)
            scrollbar = ttk.Scrollbar(edit_win, orient="vertical", command=canvas_edit.yview)
            scrollable_frame = ttk.Frame(canvas_edit)
            scrollable_frame.bind("<Configure>", lambda e: canvas_edit.configure(scrollregion=canvas_edit.bbox("all")))
            canvas_edit.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas_edit.configure(yscrollcommand=scrollbar.set)

            entries = []
            for i, name in enumerate(names_list, start=1):
                frame = ttk.Frame(scrollable_frame)
                frame.pack(fill=tk.X, padx=10, pady=2)
                lbl = ttk.Label(frame, text=f"Задание {i}:", width=12)
                lbl.pack(side=tk.LEFT)
                entry = ttk.Entry(frame, width=30)
                entry.insert(0, name)
                entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
                entries.append(entry)

            btn_frame_edit = ttk.Frame(edit_win)
            btn_frame_edit.pack(pady=10)

            def save_names():
                new_names = []
                for entry in entries:
                    val = entry.get().strip()
                    if not val:
                        val = str(entries.index(entry)+1)
                    new_names.append(val)
                names_text.delete("1.0", tk.END)
                names_text.insert(tk.END, ', '.join(new_names))
                update_preview()
                edit_win.destroy()

            ttk.Button(btn_frame_edit, text="Сохранить", command=save_names).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame_edit, text="Отмена", command=edit_win.destroy).pack(side=tk.LEFT, padx=5)

            canvas_edit.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

        edit_btn = ttk.Button(names_frame, text="✎ Редактировать", command=edit_names_dialog)
        edit_btn.pack(side=tk.LEFT, padx=5)

        default_names = ','.join(str(i) for i in range(1, 28))
        names_text.insert(tk.END, default_names)
        names_text.bind('<KeyRelease>', lambda e: update_preview())
        row += 1

        # ----- ФУНКЦИЯ ЗАГРУЗКИ ИЗ СОХРАНЁННЫХ -----
        def load_from_storage():
            recent = get_recent_templates()
            if not recent:
                messagebox.showinfo("Нет шаблонов", "У вас пока нет сохранённых шаблонов.")
                return
            
            select_win = tk.Toplevel(dialog)
            select_win.title("Выбор шаблона из библиотеки")
            select_win.geometry("500x450")
            select_win.transient(dialog)
            select_win.grab_set()
            
            tk.Label(select_win, text="Выберите шаблон для загрузки в редактор:", font=("Arial", 12)).pack(pady=10)
            
            frame = ttk.Frame(select_win)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Arial", 10), height=10)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=listbox.yview)
            
            template_map = {}
            for template_id, info in recent:
                created = info.get("created", "Unknown")[:19]
                display_text = f"{info['name']} (создан: {created})"
                listbox.insert(tk.END, display_text)
                template_map[display_text] = template_id
            
            def on_select():
                selection = listbox.curselection()
                if not selection:
                    return
                display_text = listbox.get(selection[0])
                template_id = template_map[display_text]
                
                scheme = load_template_from_storage(template_id)
                if scheme:
                    total = len(scheme['rates'])
                    test = len([k for k in scheme['check_keys'] if k != 0])
                    problems_var.set(str(total))
                    test_problems_var.set(str(test))
                    
                    scores_text.delete("1.0", tk.END)
                    scores_text.insert(tk.END, ','.join(map(str, scheme['rates'])))
                    
                    check_text.delete("1.0", tk.END)
                    check_text.insert(tk.END, ','.join(map(str, scheme['check_keys'])))
                    
                    names_text.delete("1.0", tk.END)
                    names = scheme.get('problems_names', [str(i) for i in range(1, total+1)])
                    names_text.insert(tk.END, ', '.join(names))
                    
                    update_preview()
                    select_win.destroy()
                    messagebox.showinfo("Успех", f"Шаблон загружен в редактор")
                else:
                    messagebox.showerror("Ошибка", "Не удалось загрузить шаблон")
            
            ttk.Button(select_win, text="Загрузить в редактор", command=on_select).pack(pady=10)
            ttk.Button(select_win, text="Отмена", command=select_win.destroy).pack(pady=5)

        # ----- КНОПКИ УПРАВЛЕНИЯ (ГЛАВНОЕ - ОНИ ДОЛЖНЫ БЫТЬ ЗДЕСЬ) -----
        btn_frame = ttk.Frame(settings_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)

        def do_generate():
            total_str = problems_var.get().strip()
            test_str = test_problems_var.get().strip()
            if not total_str or not test_str:
                messagebox.showerror("Ошибка", "Заполните количество заданий")
                return
            try:
                total = int(total_str)
                test = int(test_str)
            except:
                messagebox.showerror("Ошибка", "Некорректное число заданий")
                return

            if default_folder:
                initial_dir = default_folder
                initial_file = "blank_template.png"
            else:
                initial_dir = self.current_path if self.current_path else ""
                initial_file = "blank_template.png"

            file_path = filedialog.asksaveasfilename(
                initialdir=initial_dir,
                initialfile=initial_file,
                defaultextension=".png",
                filetypes=[("PNG images", "*.png"), ("All files", "*.*")]
            )
            if not file_path:
                return
            try:
                fields_number = fields_number_var.get()
                columns = columns_var.get()
                rows = problems_in_column_var.get()
                scores_str = scores_text.get("1.0", tk.END).strip()
                rates = list(map(int, scores_str.replace(',', ' ').split()))
                if len(rates) < total:
                    rates += [1] * (total - len(rates))
                rates = rates[:total]

                check_str = check_text.get("1.0", tk.END).strip()
                check_keys = list(map(int, check_str.replace(',', ' ').split()))
                if len(check_keys) < total:
                    check_keys += [0] * (total - len(check_keys))
                check_keys = check_keys[:total]

                names_str = names_text.get("1.0", tk.END).strip()
                problems_names = [n.strip() for n in names_str.split(',') if n.strip()]
                if len(problems_names) < total:
                    problems_names += [str(i) for i in range(len(problems_names)+1, total+1)]
                problems_names = problems_names[:total]

                generate_custom_template(
                    output_path=file_path,
                    title_text=title_var.get(),
                    problems=total,
                    test_problems=test,
                    rates=rates,
                    check_keys=check_keys,
                    problems_in_column=rows,
                    columns=columns,
                    fields_number=fields_number,
                    problems_names=problems_names
                )
                messagebox.showinfo("Успех", f"Шаблон сохранён:\n{file_path}")
                
                answer = messagebox.askyesno(
                    "Сохранить в библиотеку",
                    "Сохранить этот шаблон в библиотеку для быстрого доступа?"
                )
                if answer:
                    from tkinter import simpledialog
                    template_name = simpledialog.askstring(
                        "Название шаблона",
                        "Введите название для шаблона:",
                        parent=dialog
                    )
                    template_id = save_template_to_storage(file_path, template_name)
                    if template_id:
                        messagebox.showinfo("Успех", f"Шаблон сохранён в библиотеке")
                
                if default_folder:
                    self.set_current_path(default_folder)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        # ВОТ ЗДЕСЬ СОЗДАЮТСЯ КНОПКИ - ПРОВЕРЬТЕ, ЧТО ОНИ ЕСТЬ
        ttk.Button(btn_frame, text="Обновить предпросмотр", command=update_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Загрузить из сохранённых", command=load_from_storage).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Сгенерировать и сохранить", command=do_generate).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Инициализация
        update_names_field()
        dialog.after(100, update_preview)

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