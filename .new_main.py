# new_main.py - Clean Dashboard (Step 2: Theme Toggle)
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
from tutorial import open_credits, open_tutorial
from dark_mode import ThemeManager
from config import save_settings, load_config

# Add project root to path for future imports
sys.path.insert(0, os.path.dirname(__file__))


class BlankScannerApp:
    """Main dashboard application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Blank Scanner - Распознавание бланков")
        self.root.geometry("700x700")
        self.root.minsize(600, 600)

        # Load config
        self.path_arr, saved_scaling, self.sharpness, saved_dark_mode = load_config()
        self.recent_folders = self.path_arr

        if saved_scaling:
            self.x, self.y, self.w, self.h = saved_scaling
        else:
            self.x, self.y, self.w, self.h = 0, 0, 640, 320

        self.current_path = self.path_arr[0] if self.path_arr else None
        self.current_folder = self.current_path
        self.blank_scheme = None
        self.last_recognized_answers = None
        self.last_score = None

        # Theme state
        self.dark_mode = False
        self.bg_color = "#f0f0f0"
        self.fg_color = "#000000"
        self.btn_bg = "#2196F3"
        self.folder_btn_bg = "#4CAF50"

        self.root.configure(bg=self.bg_color)

        # Setup UI FIRST
        self.setup_ui()

        # Initialize theme manager
        self.theme_manager = ThemeManager(self)

        # NOW try to load scheme (after UI exists)
        if self.current_path:
            self.try_load_scheme_on_startup()

        # Bind Escape to quit
        self.root.bind('<Escape>', lambda e: self.root.quit())

    
    def setup_ui(self):
        # Title section
        title_frame = tk.Frame(self.root, bg=self.bg_color)
        title_frame.pack(pady=30)
        
        tk.Label(
            title_frame,
            text="📷 Blank Scanner",
            font=("Arial", 28, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack()
        
        tk.Label(
            title_frame,
            text="Система распознавания и проверки бланков",
            font=("Arial", 12),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(pady=(5, 0))
        
        # Separator
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X, padx=40)
        
        # Folder status section
        folder_frame = tk.LabelFrame(
            self.root,
            text=" Рабочая папка ",
            font=("Arial", 10, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=10,
            pady=10
        )
        folder_frame.pack(fill=tk.X, padx=40, pady=20)
        
        self.folder_label = tk.Label(
            folder_frame,
            text="❌ Папка не выбрана",
            font=("Arial", 10),
            bg=self.bg_color,
            fg="gray"
        )
        self.folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Button(
            folder_frame,
            text="📁 Выбрать папку",
            font=("Arial", 10),
            command=self.select_folder,
            bg=self.folder_btn_bg,
            fg="white",
            padx=15,
            pady=5,
            cursor="hand2",
            relief=tk.RAISED,
            borderwidth=1
        ).pack(side=tk.RIGHT)
        
        # Main buttons grid
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)
        
        # Configure grid weights
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.rowconfigure(0, weight=1)
        btn_frame.rowconfigure(1, weight=1)
        btn_frame.rowconfigure(2, weight=1)
        
        # Button style function
        def create_dashboard_button(parent, text, command, row, col):
            frame = tk.Frame(parent, bg=self.bg_color)
            frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            
            btn = tk.Button(
                frame,
                text=text,
                font=("Arial", 12),
                command=command,
                bg=self.btn_bg,
                fg="white",
                padx=20,
                pady=20,
                cursor="hand2",
                relief=tk.RAISED,
                borderwidth=2
            )
            btn.pack(fill=tk.BOTH, expand=True)
            return btn
        
        # Row 0: Scan and Load
        self.scan_btn = create_dashboard_button(
            btn_frame,
            "📷 Начать сканирование\n(с камеры)",
            self.scan_camera,
            row=0, col=0
        )
        
        self.load_btn = create_dashboard_button(
            btn_frame,
            "🖼️ Загрузить изображение\n(из файла)",
            self.load_image,
            row=0, col=1
        )
        
        # Row 1: Train and Template
        self.train_btn = create_dashboard_button(
            btn_frame,
            "🤖 Обучить модель\n(на рукописных цифрах)",
            self.train_model,
            row=1, col=0
        )
        
        self.template_btn = create_dashboard_button(
            btn_frame,
            "📝 Создать бланк\n(шаблон ответов)",
            self.create_template,
            row=1, col=1
        )
        
        # Row 2: Tutorial and Credits
        self.tutorial_btn = create_dashboard_button(
            btn_frame,
            "📖 Руководство\nпользователя",
            self.show_tutorial,
            row=2, col=0
        )
        
        self.credits_btn = create_dashboard_button(
            btn_frame,
            "ℹ️ О программе\nCredits",
            self.show_credits,
            row=2, col=1
        )
        
        # Bottom bar with status and theme toggle
        bottom_frame = tk.Frame(self.root, bg=self.bg_color)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # Status label (left side)
        self.status_label = tk.Label(
            bottom_frame,
            text="🟢 Готов к работе | Выберите рабочую папку",
            font=("Arial", 9),
            bg=self.bg_color,
            fg=self.fg_color,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Theme toggle frame (right side)
        theme_frame = tk.Frame(bottom_frame, bg=self.bg_color)
        theme_frame.pack(side=tk.RIGHT)
        
        self.theme_label = tk.Label(
            theme_frame,
            text="☀️",
            font=("Arial", 14),
            bg=self.bg_color,
            fg=self.fg_color,
            cursor="hand2"
        )
        self.theme_label.pack(side=tk.LEFT, padx=5)
        self.theme_label.bind("<Button-1>", lambda e: self.toggle_theme())
        
        self.theme_text = tk.Label(
            theme_frame,
            text="Светлая тема",
            font=("Arial", 9),
            bg=self.bg_color,
            fg=self.fg_color,
            cursor="hand2"
        )
        self.theme_text.pack(side=tk.LEFT)
        self.theme_text.bind("<Button-1>", lambda e: self.toggle_theme())
    
    # ------------------------------------------------------------------
    # Theme Management
    # ------------------------------------------------------------------
    
    def toggle_theme(self):
        """Toggle between light and dark mode"""
        self.theme_manager.toggle()

    def get_theme_colors(self):
        return {
            'bg': self.bg_color,
            'fg': self.fg_color,
            'btn_bg': self.btn_bg,
            'folder_btn_bg': self.folder_btn_bg
        }
    
    # ------------------------------------------------------------------
    # Button handlers (just print for now)
    # ------------------------------------------------------------------
    
    def try_load_scheme_on_startup(self):
        """Try to load scheme from saved folder on startup"""
        from scheme_loader import load_blank_scheme
        
        if not self.current_path or not os.path.exists(self.current_path):
            return
        
        try:
            self.blank_scheme = load_blank_scheme(self.current_path)
            if self.blank_scheme:
                folder_display = self.current_path
                if len(folder_display) > 50:
                    folder_display = "..." + folder_display[-47:]
                self.folder_label.config(text=f"📁 {folder_display}", fg=self.fg_color)
                self.status_label.config(text="🟢 Схема загружена | Готов к сканированию")
        except Exception as e:
            print(f"[DEBUG] Could not load saved scheme: {e}")
    
    def select_folder(self):
        """Select working folder"""
        from folder_select_window import FolderSelectWindow
        
        selector = FolderSelectWindow(self.root, self.get_theme_colors())
        selector.path_arr = self.recent_folders
        selector.x = self.x
        selector.y = self.y
        selector.w = self.w
        selector.h = self.h
        selector.sharpness = self.sharpness
        selector.dark_mode = self.dark_mode
        
        new_path, blank_scheme = selector.show()
        
        if new_path and blank_scheme:
            self.current_path = new_path
            self.current_folder = new_path
            self.blank_scheme = blank_scheme
            self.recent_folders = selector.path_arr
            self.path_arr = selector.path_arr  # Keep both in sync
            
            # SAVE USING OLD SYSTEM
            save_settings(
                self.path_arr,
                [self.x, self.y, self.w, self.h],
                self.sharpness,
                self.dark_mode
            )
            
            folder_display = new_path
            if len(folder_display) > 50:
                folder_display = "..." + folder_display[-47:]
            self.folder_label.config(text=f"📁 {folder_display}", fg=self.fg_color)
            self.status_label.config(text="🟢 Схема загружена | Готов к сканированию")

    def create_template_with_folder(self, default_folder=None):
        """Create template with pre-filled folder"""
        # This will call your existing template dialog
        self.create_template()  # For now, just call create_template
        # Later we'll enhance this to auto-save to default_folder

    def scan_camera(self):
        if not self.current_folder or not self.blank_scheme:
            messagebox.showwarning("Предупреждение!", "Сначала выберите рабочую папку со схемой!")
            return

        from scan_window import ScanWindow

        config_data = {
            'x': self.x, 'y': self.y, 'w': self.w, 'h': self.h,
            'sharpness': self.sharpness,
            'path_arr': self.path_arr,
            'dark_mode': self.dark_mode
        }

        def on_scan_complete(score, sharpness, recognized_answers):
            self.sharpness = sharpness
            self.last_recognized_answers = recognized_answers
            self.last_score = score

            # Закрываем окно сканирования
            if hasattr(self, 'scan_window') and self.scan_window:
                self.scan_window.on_close()   # или .root.destroy()
                self.scan_window = None

            from results_window import ResultsWindow
            if recognized_answers:
                ResultsWindow(
                    self.root,
                    score if score else [],
                    recognized_answers,
                    self.current_path,
                    self.blank_scheme,
                    theme_colors=self.get_theme_colors()
                )
            else:
                messagebox.showwarning("Результат", "Ничего не распознано.")

        # Сохраняем ссылку на окно
        self.scan_window = ScanWindow(
            self.root, self.blank_scheme, self.current_path, config_data,
            theme_colors=self.get_theme_colors(), on_scan_complete=on_scan_complete
        )
    
    def load_image(self):
        if not self.current_folder or not self.blank_scheme:
            messagebox.showwarning("Предупреждение!", "Сначала выберите рабочую папку со схемой!")
            return

        # Ask user to select an image
        file_path = filedialog.askopenfilename(
            title="Выберите изображение бланка",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return
        
        import cv2

        # Load the image
        frame = cv2.imread(file_path)
        if frame is None:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение:\n{file_path}")
            return
        
        max_width = 1920
        max_height = 1080
        h, w = frame.shape[:2]
        if w > max_width or h > max_height:
            scale = min(max_width / w, max_height / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h))

        # Process it exactly like camera scan
        from process_frame import process_frame

        result = process_frame(frame, self.blank_scheme, self.current_path, self.sharpness)

        if result is None:
            return

        score, new_sharpness, recognized_answers, status = result

        if status == 'cancelled':
            return

        self.sharpness = new_sharpness
        self.last_recognized_answers = recognized_answers
        self.last_score = score

        # Save settings
        save_settings(self.path_arr, [self.x, self.y, self.w, self.h], self.sharpness, self.dark_mode)

        # Show results window
        if recognized_answers:
            from results_window import ResultsWindow
            ResultsWindow(
                self.root,
                score,
                recognized_answers,
                self.current_path,
                self.blank_scheme,
                theme_colors=self.get_theme_colors()
            )
        else:
            messagebox.showwarning("Результат", "Ничего не распознано.")
    
    def train_model(self):
        """Open model training"""
        print("[DEBUG] train_model called")
        messagebox.showinfo("Обучение", "Здесь будет обучение модели")
    
    def create_template(self):
        from template_window import TemplateWindow
        
        def on_template_created(template_path):
            print(f"[DEBUG] Template created: {template_path}")
            # If template was saved to current folder, reload scheme
            if self.current_path and template_path.startswith(self.current_path):
                self.try_load_scheme_on_startup()
        
        TemplateWindow(
            self.root,
            current_path=self.current_path,
            theme_colors=self.get_theme_colors(),
            on_template_created=on_template_created
        )
    
    def show_credits(self):
        open_credits(self.root, self.get_theme_colors())

    def show_tutorial(self):
        open_tutorial(self.root, self.get_theme_colors())



if __name__ == "__main__":
    root = tk.Tk()
    app = BlankScannerApp(root)
    root.mainloop()