import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os


class VarEditorWindow:

    def __init__(self, parent, current_path=None, blank_scheme=None, theme_colors=None):
        self.parent = parent
        self.current_path = current_path
        self.blank_scheme = blank_scheme
        self.theme_colors = theme_colors or {}

        self.num_tasks = len(blank_scheme['problems_names']) if blank_scheme else 27
        self.answer_entries = []

        self.window = tk.Toplevel(parent)
        self.window.title("Редактор .var файла")
        self.window.geometry('500x700')
        self.window.minsize(400, 500)
        self.window.transient(parent)
        self.window.grab_set()

        self.setup_variant_section()
        self.setup_answers_section()
        self.setup_buttons()

        self.window.bind('<Escape>', lambda e: self.window.destroy())
        self.window.focuse_set()

    def setup_variant_section(self):
        frame = ttk.Frame(self.window, padding=10)
        frame.pack(fill=tk.X)
        
        ttk.Label(frame, text="Вариант №:", font=("Arial", 12)).pack(side=tk.LEFT)
        
        self.variant_var = tk.StringVar(value="001")
        vcmd = (self.window.register(lambda p: p.isdigit() or p == ""), '%P')
        variant_entry = ttk.Entry(frame, textvariable=self.variant_var, width=8, font=("Arial", 12))
        variant_entry.pack(side=tk.LEFT, padx=10)
        
        self.filename_label = ttk.Label(frame, text="→ 001.var", font=("Arial", 10))
        self.filename_label.pack(side=tk.LEFT, padx=10)
        
        self.variant_var.trace_add('write', self.update_filename_label)
        
        ttk.Separator(self.window, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)

    def update_filename_label(self, *args):
        variant = self.variant_var.get().strip()
        if variant:
            self.filename_label.config(text=f"→ {variant}.var")
        else:
            self.filename_label.config(text="→ ?.var")

    def setup_answers_section(self):
        """Scrollable area with answer inputs"""
        # Frame for scrollable content
        outer_frame = ttk.Frame(self.window)
        outer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Canvas and scrollbar
        canvas = tk.Canvas(outer_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)

        ttk.Label(self.scrollable_frame, text="Ответы (по одному на строку):", 
                  font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        for i in range(1, self.num_tasks + 1):
            task_name = self.blank_scheme['problems_names'][i-1] if self.blank_scheme else str(i)
            
            frame = ttk.Frame(self.scrollable_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=f"{task_name}:", width=12).pack(side=tk.LEFT)
            
            answer_var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=answer_var, width=30)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.answer_entries.append(answer_var)

    def setup_buttons(self):
        btn_frame = ttk.Frame(self.window, padding=10)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="📂 Загрузить .var", command=self.load_var).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 Сохранить .var", command=self.save_var).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Закрыть", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

    def load_var(self):
        if not self.current_path:
            file_path = filedialog.askopenfilename(
                title="Выберите .var файл",
                filetypes=[("VAR files", "*.var"), ("All files", "*.*")]
            )
        else:
            file_path = filedialog.askopenfilename(
                title="Выберите .var файл",
                initialdir=self.current_path,
                filetypes=[("VAR files", "*.var"), ("All files", "*.*")]
            )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                answers = [line.strip() for line in f if line.strip()]
            
            basename = os.path.basename(file_path)
            variant = os.path.splitext(basename)[0]
            if variant.isdigit():
                self.variant_var.set(variant)
            
            for i, answer in enumerate(answers):
                if i < len(self.answer_entries):
                    self.answer_entries[i].set(answer)
            
            messagebox.showinfo("Успех", f"Загружено {len(answers)} ответов из:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{e}")

    def save_var(self):
        variant = self.variant_var.get().strip()
        if not variant:
            messagebox.showerror("Ошибка", "Введите номер варианта!")
            return
        
        filename = f"{variant}.var"
        
        if self.current_path:
            initial_dir = self.current_path
        else:
            initial_dir = ""
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить .var файл",
            initialdir=initial_dir,
            initialfile=filename,
            defaultextension=".var",
            filetypes=[("VAR files", "*.var"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:

            answers = []
            for entry in self.answer_entries:
                answer = entry.get().strip()
                if answer:
                    answers.append(answer)
                else:
                    answers.append("")  # Empty line for unanswered
            
            while answers and answers[-1] == "":
                answers.pop()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                for answer in answers:
                    f.write(answer + '\n')
            
            messagebox.showinfo("Успех", f"Файл сохранён:\n{file_path}\n\nЗаписано {len(answers)} ответов.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")