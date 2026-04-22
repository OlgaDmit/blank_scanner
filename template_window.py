import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
from datetime import datetime

from blank_generator import generate_custom_template
from templates_storage import save_template_to_storage, get_recent_templates, load_template_from_storage


class TemplateWindow:
    
    def __init__(self, parent, current_path=None, default_folder=None, theme_colors=None, on_template_created=None):
        self.parent = parent
        self.current_path = current_path
        self.default_folder = default_folder
        self.theme_colors = theme_colors or {}
        self.on_template_created = on_template_created
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Создание шаблона бланка")
        self.dialog.geometry("1200x900")
        self.dialog.minsize(900, 700)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Переменные
        self.title_var = tk.StringVar(value="ЕГЭ 2026")
        self.problems_var = tk.StringVar(value="27")
        self.test_problems_var = tk.StringVar(value="20")
        self.fields_number_var = tk.IntVar(value=10)
        self.columns_var = tk.IntVar(value=3)
        self.problems_in_column_var = tk.IntVar(value=10)

        self.problems_var.trace_add('write', self.update_columns)
        self.problems_in_column_var.trace_add('write', self.update_columns)

        self.setup_preview_frame()
        self.setup_settings_panel()
        self.problems_var.trace_add('write', lambda *a: (self.sync_total_and_test(), self.update_names_field()))
        self.test_problems_var.trace_add('write', self.sync_total_and_test)

    # Валидация
    def validate_int(self, value):
        return value == "" or (value.isdigit() and int(value) >= 1)
        
    def get_vcmd(self):
        return (self.dialog.register(lambda p: self.validate_int(p)), '%P')

    # Функция пересчёта столбцов
    def update_columns(self, *args):
        problems_str = self.problems_var.get().strip()
        if not problems_str:
            return
        try:
            problems = int(problems_str)
            rows = self.problems_in_column_var.get()
            if rows > 0:
                new_cols = (problems + rows - 1) // rows
                self.columns_var.set(new_cols)
        except:
            pass


    def setup_preview_frame(self):
        # ----- ПРЕДПРОСМОТР -----
        preview_frame = ttk.LabelFrame(self.dialog, text="Предпросмотр")
        preview_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(preview_frame, bg='white', highlightthickness=0)
        h_scroll = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        h_scroll.grid(row=1, column=0, sticky='ew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        self.preview_image = None

    def setup_settings_panel(self):

        # ----- ПАНЕЛЬ НАСТРОЕК -----
        settings_frame = ttk.LabelFrame(self.dialog, text="Параметры шаблона", padding=10)
        settings_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        row = 0
        ttk.Label(settings_frame, text="Название экзамена:").grid(row=row, column=0, sticky=tk.W, pady=2)
        title_entry = ttk.Entry(settings_frame, textvariable=self.title_var, width=30)
        title_entry.grid(row=row, column=1, pady=2)
        title_entry.bind('<KeyRelease>', lambda e: self.update_preview())
        row += 1

        ttk.Label(settings_frame, text="Общее количество заданий:").grid(row=row, column=0, sticky=tk.W, pady=2)
        problems_entry = tk.Entry(settings_frame, textvariable=self.problems_var, validate='key', validatecommand=self.get_vcmd(), width=10)
        problems_entry.grid(row=row, column=1, sticky=tk.W, pady=2)
        problems_entry.bind('<KeyRelease>', lambda e: (self.update_names_field(), self.update_preview()))
        row += 1

        ttk.Label(settings_frame, text="Заданий в тестовой части:").grid(row=row, column=0, sticky=tk.W, pady=2)
        test_entry = tk.Entry(settings_frame, textvariable=self.test_problems_var, validate='key', validatecommand=self.get_vcmd(), width=10)
        test_entry.grid(row=row, column=1, sticky=tk.W, pady=2)
        test_entry.bind('<KeyRelease>', lambda e: self.update_preview())
        row += 1

        ttk.Label(settings_frame, text="Количество клеток для ответа:").grid(row=row, column=0, sticky=tk.W, pady=2)
        cells_spin = ttk.Spinbox(settings_frame, from_=1, to=20, textvariable=self.fields_number_var, width=10)
        cells_spin.grid(row=row, column=1, sticky=tk.W, pady=2)
        cells_spin.bind('<ButtonRelease-1>', lambda e: self.update_preview())
        row += 1

        ttk.Label(settings_frame, text="Количество столбцов (авто):").grid(row=row, column=0, sticky=tk.W, pady=2)
        cols_spin = ttk.Spinbox(settings_frame, from_=1, to=10, textvariable=self.columns_var, width=10, state='readonly')
        cols_spin.grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1

        ttk.Label(settings_frame, text="Заданий в столбце:").grid(row=row, column=0, sticky=tk.W, pady=2)
        rows_spin = ttk.Spinbox(settings_frame, from_=1, to=50, textvariable=self.problems_in_column_var, width=10)
        rows_spin.grid(row=row, column=1, sticky=tk.W, pady=2)
        rows_spin.bind('<ButtonRelease-1>', lambda e: self.update_preview())
        row += 1

        ttk.Label(settings_frame, text="Баллы за задания (через запятую):").grid(row=row, column=0, sticky=tk.NW, pady=2)
        self.scores_text = tk.Text(settings_frame, height=5, width=40)
        self.scores_text.grid(row=row, column=1, pady=2, sticky=tk.W)
        default_rates = "1,1,1,1,2,2,1,1,2,2,1,1,1,2,2,1,2,2,1,1,3,2,2,3,3,3,1"
        self.scores_text.insert(tk.END, default_rates)
        self.scores_text.bind('<KeyRelease>', lambda e: self.update_preview())
        row += 1

        ttk.Label(settings_frame, text="Типы проверки (через запятую):\n(1-точное,2-таблица,3-множество,0-нет)").grid(row=row, column=0, sticky=tk.NW, pady=2)
        self.check_text = tk.Text(settings_frame, height=5, width=40)
        self.check_text.grid(row=row, column=1, pady=2, sticky=tk.W)
        default_check = "1,1,1,1,3,2,1,1,3,2,1,1,1,3,2,1,2,3,1,1,0,0,0,0,0,0,0"
        self.check_text.insert(tk.END, default_check)
        self.check_text.bind('<KeyRelease>', lambda e: self.update_preview())
        row += 1

        # НАЗВАНИЯ ЗАДАНИЙ
        ttk.Label(settings_frame, text="Названия заданий (через запятую):").grid(row=row, column=0, sticky=tk.NW, pady=2)
        names_frame = ttk.Frame(settings_frame)
        names_frame.grid(row=row, column=1, sticky=tk.W, pady=2)
        self.names_text = tk.Text(names_frame, height=5, width=35)
        self.names_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def edit_names_dialog():
            total_str = self.problems_var.get().strip()
            if not total_str or not total_str.isdigit():
                messagebox.showerror("Ошибка", "Сначала укажите корректное количество заданий.")
                return
            total = int(total_str)
            current_text = self.names_text.get("1.0", tk.END).strip()
            names_list = [n.strip() for n in current_text.split(',') if n.strip()]
            if len(names_list) < total:
                names_list += [str(i) for i in range(len(names_list)+1, total+1)]
            names_list = names_list[:total]

            edit_win = tk.Toplevel(self.dialog)
            edit_win.title("Редактирование названий заданий")
            edit_win.geometry("400x500")
            edit_win.transient(self.dialog)
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
                self.names_text.delete("1.0", tk.END)
                self.names_text.insert(tk.END, ', '.join(new_names))
                self.update_preview()
                edit_win.destroy()

            ttk.Button(btn_frame_edit, text="Сохранить", command=save_names).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame_edit, text="Отмена", command=edit_win.destroy).pack(side=tk.LEFT, padx=5)

            canvas_edit.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

        edit_btn = ttk.Button(names_frame, text="✎ Редактировать", command=edit_names_dialog)
        edit_btn.pack(side=tk.LEFT, padx=5)

        default_names = ','.join(str(i) for i in range(1, 28))
        self.names_text.insert(tk.END, default_names)
        self.names_text.bind('<KeyRelease>', lambda e: self.update_preview())
        row += 1

        # ----- КНОПКИ УПРАВЛЕНИЯ (ГЛАВНОЕ - ОНИ ДОЛЖНЫ БЫТЬ ЗДЕСЬ) -----
        btn_frame = ttk.Frame(settings_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        # ВОТ ЗДЕСЬ СОЗДАЮТСЯ КНОПКИ - ПРОВЕРЬТЕ, ЧТО ОНИ ЕСТЬ
        ttk.Button(btn_frame, text="Обновить предпросмотр", command=self.update_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Загрузить из сохранённых", command=self.load_from_storage).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Сгенерировать и сохранить", command=self.do_generate).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

        self.update_names_field()
        self.dialog.after(100, self.update_preview)

    # Обновление полей
    def update_names_field(self):
        total_str = self.problems_var.get().strip()
        if not total_str:
            return
        try:
            total = int(total_str)
        except:
            return
        current_text = self.names_text.get("1.0", tk.END).strip()
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
        self.names_text.delete("1.0", tk.END)
        self.names_text.insert(tk.END, ', '.join(new_names))

    def refresh_scores_and_checks(self):
            total_str = self.problems_var.get().strip()
            if not total_str:
                return
            try:
                total = int(total_str)
            except:
                return
            test_str = self.test_problems_var.get().strip()
            test = int(test_str) if test_str else 0
            if test > total:
                test = total
                self.test_problems_var.set(str(test))

            try:
                current_scores = list(map(int, self.scores_text.get("1.0", tk.END).strip().replace(',', ' ').split()))
            except:
                current_scores = []
            if len(current_scores) < total:
                current_scores += [2] * (total - len(current_scores))
            else:
                current_scores = current_scores[:total]

            try:
                current_checks = list(map(int, self.check_text.get("1.0", tk.END).strip().replace(',', ' ').split()))
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

            self.scores_text.delete("1.0", tk.END)
            self.scores_text.insert(tk.END, ','.join(map(str, current_scores)))
            self.check_text.delete("1.0", tk.END)
            self.check_text.insert(tk.END, ','.join(map(str, current_checks)))
            self.update_names_field()
    
    def sync_total_and_test(self, *args):
            total_str = self.problems_var.get().strip()
            test_str = self.test_problems_var.get().strip()
            if not total_str or not test_str:
                return
            try:
                total = int(total_str)
                test = int(test_str)
            except:
                return
            if test > total:
                self.test_problems_var.set(str(total))
            elif total < test:
                self.problems_var.set(str(test))
            self.refresh_scores_and_checks()
    
    def update_preview(self, event=None):
            total_str = self.problems_var.get().strip()
            test_str = self.test_problems_var.get().strip()
            if not total_str or not test_str:
                self.canvas.delete("all")
                self.canvas.create_text(10, 10, anchor='nw', text="Введите количество заданий", fill='red')
                return
            try:
                total = int(total_str)
                test = int(test_str)
            except:
                return
            fields_number = self.fields_number_var.get()
            columns = self.columns_var.get()
            rows = self.problems_in_column_var.get()
            scores_str = self.scores_text.get("1.0", tk.END).strip()
            rates = list(map(int, scores_str.replace(',', ' ').split()))
            if len(rates) < total:
                rates += [1] * (total - len(rates))
            rates = rates[:total]
            check_str = self.check_text.get("1.0", tk.END).strip()
            check_keys = list(map(int, check_str.replace(',', ' ').split()))
            if len(check_keys) < total:
                check_keys += [0] * (total - len(check_keys))
            check_keys = check_keys[:total]

            names_str = self.names_text.get("1.0", tk.END).strip()
            problems_names = [n.strip() for n in names_str.split(',') if n.strip()]
            if len(problems_names) < total:
                problems_names += [str(i) for i in range(len(problems_names)+1, total+1)]
            problems_names = problems_names[:total]

            temp_path = "temp_preview.png"
            try:
                generate_custom_template(
                    output_path=temp_path,
                    title_text=self.title_var.get(),
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
                cw = self.canvas.winfo_width()
                ch = self.canvas.winfo_height()
                if cw > 10 and ch > 10:
                    img.thumbnail((cw, ch), Image.Resampling.LANCZOS)
                else:
                    img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                self.preview_image = ImageTk.PhotoImage(img)
                self.canvas.delete("all")
                self.canvas.create_image(0, 0, anchor='nw', image=self.preview_image)
                self.canvas.config(scrollregion=self.canvas.bbox('all'))
                os.remove(temp_path)
            except Exception as e:
                self.canvas.delete("all")
                self.canvas.create_text(10, 10, anchor='nw', text=f"Ошибка: {e}", fill='red')
    
    # ----- ФУНКЦИЯ ЗАГРУЗКИ ИЗ СОХРАНЁННЫХ -----
    def load_from_storage(self):
        recent = get_recent_templates()
        if not recent:
            messagebox.showinfo("Нет шаблонов", "У вас пока нет сохранённых шаблонов.")
            return
        
        select_win = tk.Toplevel(self.dialog)
        select_win.title("Выбор шаблона из библиотеки")
        select_win.geometry("500x450")
        select_win.transient(self.dialog)
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
                self.problems_var.set(str(total))
                self.test_problems_var.set(str(test))
                
                self.scores_text.delete("1.0", tk.END)
                self.scores_text.insert(tk.END, ','.join(map(str, scheme['rates'])))
                
                self.check_text.delete("1.0", tk.END)
                self.check_text.insert(tk.END, ','.join(map(str, scheme['check_keys'])))
                
                self.names_text.delete("1.0", tk.END)
                names = scheme.get('problems_names', [str(i) for i in range(1, total+1)])
                self.names_text.insert(tk.END, ', '.join(names))
                
                self.update_preview()
                select_win.destroy()
                messagebox.showinfo("Успех", f"Шаблон загружен в редактор")
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить шаблон")
        
        ttk.Button(select_win, text="Загрузить в редактор", command=on_select).pack(pady=10)
        ttk.Button(select_win, text="Отмена", command=select_win.destroy).pack(pady=5)

    def do_generate(self):
            total_str = self.problems_var.get().strip()
            test_str = self.test_problems_var.get().strip()
            if not total_str or not test_str:
                messagebox.showerror("Ошибка", "Заполните количество заданий")
                return
            try:
                total = int(total_str)
                test = int(test_str)
            except:
                messagebox.showerror("Ошибка", "Некорректное число заданий")
                return

            if self.default_folder:
                initial_dir = self.default_folder
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
                fields_number = self.fields_number_var.get()
                columns = self.columns_var.get()
                rows = self.problems_in_column_var.get()
                scores_str = self.scores_text.get("1.0", tk.END).strip()
                rates = list(map(int, scores_str.replace(',', ' ').split()))
                if len(rates) < total:
                    rates += [1] * (total - len(rates))
                rates = rates[:total]

                check_str = self.check_text.get("1.0", tk.END).strip()
                check_keys = list(map(int, check_str.replace(',', ' ').split()))
                if len(check_keys) < total:
                    check_keys += [0] * (total - len(check_keys))
                check_keys = check_keys[:total]

                names_str = self.names_text.get("1.0", tk.END).strip()
                problems_names = [n.strip() for n in names_str.split(',') if n.strip()]
                if len(problems_names) < total:
                    problems_names += [str(i) for i in range(len(problems_names)+1, total+1)]
                problems_names = problems_names[:total]

                generate_custom_template(
                    output_path=file_path,
                    title_text=self.title_var.get(),
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
                        parent=self.dialog
                    )
                    template_id = save_template_to_storage(file_path, template_name)
                    if template_id:
                        messagebox.showinfo("Успех", f"Шаблон сохранён в библиотеке")
                
                self.dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
