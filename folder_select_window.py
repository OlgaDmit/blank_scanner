import os
import glob
from templates_storage import get_recent_templates, copy_template_to_work_folder
from scheme_loader import load_blank_scheme
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import shutil

class FolderSelectWindow:

    def __init__(self, parent, theme_colors=None):
        self.parent = parent
        self.root = parent
        self.theme_colors = theme_colors or {}
        self.current_path = None
        self.blank_scheme = None
        self.path_arr = []
        self.x = self.y = self.w = self.h = 0
        self.sharpness = 1.0
        self.dark_mode = False

    def show(self):
        self.choose_folder_dialog()
        return self.current_path, self.blank_scheme
    
    def update_combo_list(self):
        """Placeholder - will be overridden or ignored"""
        pass
    
    def update_folder_label(self):
        """Placeholder - will be overridden or ignored"""
        pass
    
    def open_template_dialog(self, default_folder=None):
        """Open template creator and save to default folder"""
        from template_window import TemplateWindow
        
        def on_template_created(template_path):
            # Template was saved - now set this folder as working folder
            folder = os.path.dirname(template_path)
            self.current_path = folder
            self.result_path = folder
            
            # Load the scheme
            from scheme_loader import load_blank_scheme
            self.blank_scheme = load_blank_scheme(folder)
        
        TemplateWindow(
            self.parent,
            current_path=default_folder,
            default_folder=default_folder,
            theme_colors=self.theme_colors,
            on_template_created=on_template_created
        )

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

            return True

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
