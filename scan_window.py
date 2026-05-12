import cv2
import platform
import sys
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import messagebox, ttk
from config import save_settings
from process_frame import process_frame

class ScanWindow:
    def __init__(self, parent, blank_scheme, current_path, config_data, theme_colors=None, on_scan_complete=None):
        self.parent = parent
        self.blank_scheme = blank_scheme
        self.current_path = current_path
        self.theme_colors = theme_colors or {}
        self.on_scan_complete = on_scan_complete

        self.x = config_data.get('x', 0)
        self.y = config_data.get('y', 0)
        self.w = config_data.get('w', 640)
        self.h = config_data.get('h', 320)
        self.sharpness = config_data.get('sharpness', 1.0)
        self.path_arr = config_data.get('path_arr', [])
        self.dark_mode = config_data.get('dark_mode', False)
        saved_scaling = [self.x, self.y, self.w, self.h] if self.x or self.y else None
        self.original_sizes = (0, 0)

        self.root = tk.Toplevel(parent)
        self.root.title("Сканирование с камеры")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # --- захват камеры (исправлено для Windows) ---
        if platform.system() == 'Windows':
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(0)
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

        self.setup_ui()
        
        # --- привязка клавиш ---
        self.root.bind('<Up>', lambda e: self.on_key('Up'))
        self.root.bind('<Down>', lambda e: self.on_key('Down'))
        self.root.bind('<Left>', lambda e: self.on_key('Left'))
        self.root.bind('<Right>', lambda e: self.on_key('Right'))
        self.root.bind('<plus>', lambda e: self.on_key('plus'))
        self.root.bind('=', lambda e: self.on_key('plus'))
        self.root.bind('<minus>', lambda e: self.on_key('minus'))
        self.root.bind('<Return>', lambda e: self.start_scan())
        self.root.bind('<Escape>', lambda e: self.on_close())

        self.update_video()

        self.root.focus_force()
        self.root.focus_set()

    def setup_ui(self):
        self.video_label = tk.Label(self.root, bg="black")
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(control_frame, 
                  text="←↑↓→ перемещать | +/- размер | Enter сканировать | Esc отмена", 
                  font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, 
                   text="📸 Сканировать (Enter)", 
                   command=self.start_scan).pack(side=tk.RIGHT, padx=5)

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
        save_settings(self.path_arr, [self.x, self.y, self.w, self.h], self.sharpness, self.dark_mode)

    def on_close(self):
        if self.cap:
            self.cap.release()
        self.root.destroy()

    def start_scan(self):
        if self.blank_scheme is None:
            messagebox.showwarning("Предупреждение", "Сначала выберите рабочую папку с настройками бланка.")
            return
        
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Ошибка", "Не удалось получить кадр с камеры.")
            return
        
        cropped = frame[self.y:self.y+self.h, self.x:self.x+self.w]
        
        # Disable scan button during processing
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.config(state='disabled')

        use_threading = (platform.system() != 'Darwin')
        if use_threading:
            result_holder = [None]
        
            def do_process():
                try:
                    result = process_frame(cropped, self.blank_scheme, self.current_path, self.sharpness)
                    result_holder[0] = result
                except Exception as e:
                    print(f"[ERROR] Process frame failed: {e}")
                    result_holder[0] = None
        
            import threading
            thread = threading.Thread(target=do_process, daemon=True)
            thread.start()
        
            def check_result():
                if thread.is_alive():
                    self.root.after(100, check_result)
                    return
                self.handle_scan_result(result_holder[0])
            
            self.root.after(100, check_result)
        
        else:
            result = process_frame(cropped, self.blank_scheme, self.current_path, self.sharpness)
            self.handle_scan_result(result)


    def is_scaling_valid(self, scaling):
        x, y, w, h = scaling
        return (0 <= x < self.original_sizes[1] and
                0 <= y < self.original_sizes[0] and
                0 < w <= self.original_sizes[1] - x and
                0 < h <= self.original_sizes[0] - y)

    def handle_scan_result(self, result):
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.config(state='normal')

        if result is None:
            return
        
        score, new_sharpness, recognized_answers, status = result
    
        if status == 'cancelled':
            return
    
        self.sharpness = new_sharpness
        save_settings(self.path_arr, [self.x, self.y, self.w, self.h], self.sharpness, self.dark_mode)

        if recognized_answers and self.on_scan_complete:
            self.on_scan_complete(score, new_sharpness, recognized_answers)


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
