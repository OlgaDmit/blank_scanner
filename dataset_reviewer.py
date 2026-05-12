# dataset_reviewer.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import glob
import cv2
from PIL import Image, ImageTk
import numpy as np


class DatasetReviewer:
    """Window for reviewing and correcting autosaved training images"""
    
    def __init__(self, parent, theme_colors=None):
        self.parent = parent
        self.theme_colors = theme_colors or {}
        self.images = []
        self.current_index = 0
        self.changes = {}
        self.deleted = []
        self.selected_folder = None
        
        self.window = tk.Toplevel(parent)
        self.window.title("Просмотр данных обучения")
        self.window.geometry("500x650")
        self.window.minsize(400, 500)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Start with folder selection
        self.show_folder_selection()
    
    # ------------------------------------------------------------------
    # PHASE 1: Folder Selection
    # ------------------------------------------------------------------
    
    def show_folder_selection(self):
        """First screen: choose which folder to review"""
        for widget in self.window.winfo_children():
            widget.destroy()
        
        self.window.geometry("500x450")
        
        ttk.Label(self.window, text="🔍 Выберите символ для проверки",
                  font=("Arial", 14, "bold")).pack(pady=20)
        
        stats_frame = ttk.LabelFrame(self.window, text="📊 Доступно изображений", padding=10)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        stats_text = tk.Text(stats_frame, height=4, width=45,
                             font=("Consolas", 10), state=tk.DISABLED)
        stats_text.pack()
        
        counts, total = self._count_autosaved_images()
        
        stats_text.config(state=tk.NORMAL)
        class_order = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ',', '-']
        row = ""
        for i, class_name in enumerate(class_order):
            count = counts.get(class_name, 0)
            row += f"{class_name}: {count:3d}   "
            if (i + 1) % 4 == 0:
                stats_text.insert(tk.END, row + "\n")
                row = ""
        if row:
            stats_text.insert(tk.END, row + "\n")
        stats_text.config(state=tk.DISABLED)
        
        ttk.Label(stats_frame, text=f"Всего: {total} изображений",
                  font=("Arial", 10, "bold")).pack(pady=5)
        
        btn_frame = ttk.LabelFrame(self.window, text="Выберите символ", padding=10)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        row1 = ttk.Frame(btn_frame)
        row1.pack(fill=tk.X, pady=3)
        for digit in ['0', '1', '2', '3', '4']:
            count = counts.get(digit, 0)
            text = f"{digit}\n({count} шт.)" if count > 0 else f"{digit}\n(нет)"
            state = 'normal' if count > 0 else 'disabled'
            ttk.Button(row1, text=text, state=state,
                      command=lambda d=digit: self.start_review(d)).pack(side=tk.LEFT, padx=3)
        
        row2 = ttk.Frame(btn_frame)
        row2.pack(fill=tk.X, pady=3)
        for digit in ['5', '6', '7', '8', '9']:
            count = counts.get(digit, 0)
            text = f"{digit}\n({count} шт.)" if count > 0 else f"{digit}\n(нет)"
            state = 'normal' if count > 0 else 'disabled'
            ttk.Button(row2, text=text, state=state,
                      command=lambda d=digit: self.start_review(d)).pack(side=tk.LEFT, padx=3)
        
        row3 = ttk.Frame(btn_frame)
        row3.pack(fill=tk.X, pady=3)
        comma_count = counts.get(',', 0)
        minus_count = counts.get('-', 0)
        ttk.Button(row3, text=f", (запятая)\n({comma_count} шт.)",
                  command=lambda: self.start_review(','),
                  state='normal' if comma_count > 0 else 'disabled').pack(side=tk.LEFT, padx=3)
        ttk.Button(row3, text=f"- (минус)\n({minus_count} шт.)",
                  command=lambda: self.start_review('-'),
                  state='normal' if minus_count > 0 else 'disabled').pack(side=tk.LEFT, padx=3)
        
        ttk.Separator(self.window, orient='horizontal').pack(fill=tk.X, padx=20, pady=5)
        
        bottom_frame = ttk.Frame(self.window, padding=10)
        bottom_frame.pack(fill=tk.X, padx=20)
        
        ttk.Button(bottom_frame, text="Отмена",
                  command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
        self.window.bind('<Escape>', lambda e: self.window.destroy())
    
    def _count_autosaved_images(self):
        """Count images in autosaved folders"""
        data_path = os.path.join('model', 'autosaved')
        counts = {}
        total = 0
        if not os.path.exists(data_path):
            return counts, total
        for folder in os.listdir(data_path):
            folder_path = os.path.join(data_path, folder)
            if os.path.isdir(folder_path):
                jpgs = len(glob.glob(os.path.join(folder_path, '*.jpg')))
                if jpgs > 0:
                    counts[folder] = jpgs
                    total += jpgs
        return counts, total
    
    def start_review(self, folder_name):
        self.selected_folder = folder_name
        data_path = os.path.join('model', 'autosaved')
        
        folder_path = os.path.join(data_path, folder_name)
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith('.jpg'):
                    self.images.append({
                        'path': os.path.join(folder_path, filename),
                        'label': folder_name,
                        'folder': folder_name
                    })
        
        if not self.images:
            messagebox.showinfo("Нет данных", f"Нет изображений для символа '{folder_name}'")
            self.show_folder_selection()
            return
        
        for widget in self.window.winfo_children():
            widget.destroy()
        
        self.window.geometry("500x650")
        self.setup_review_ui()
        self.show_current_image()
    
    # ------------------------------------------------------------------
    # PHASE 2: Image Review
    # ------------------------------------------------------------------
    
    def setup_review_ui(self):
        # Header with back button
        header_frame = ttk.Frame(self.window, padding=10)
        header_frame.pack(fill=tk.X)
        
        ttk.Button(header_frame, text="◀ Назад к выбору",
                   command=self.back_to_selection).pack(side=tk.LEFT)
        
        folder_display = f"'{self.selected_folder}'"
        ttk.Label(header_frame, text=f"Проверка: {folder_display}",
                  font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=20)
        
        ttk.Separator(self.window, orient='horizontal').pack(fill=tk.X, padx=10)
        
        # Image display frame
        self.image_frame = ttk.LabelFrame(self.window, text="Изображение", padding=10)
        self.image_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack(expand=True)
        
        # Current label
        label_info_frame = ttk.Frame(self.window, padding=5)
        label_info_frame.pack(fill=tk.X, padx=20)
        
        ttk.Label(label_info_frame, text="Текущая метка:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.current_label_var = tk.StringVar(value="-")
        ttk.Label(label_info_frame, textvariable=self.current_label_var,
                  font=("Arial", 14, "bold"), foreground="blue").pack(side=tk.LEFT, padx=10)
        
        ttk.Separator(self.window, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)
        
        # Instructions
        instruction_frame = ttk.Frame(self.window, padding=5)
        instruction_frame.pack(fill=tk.X, padx=20)
        
        ttk.Label(instruction_frame,
                  text="⌨️ 0-9, ,(запятая), -(минус), пробел = изменить метку",
                  font=("Arial", 9), foreground="gray").pack()
        ttk.Label(instruction_frame,
                  text="Delete / Backspace = удалить | ← → = навигация | Esc = закрыть",
                  font=("Arial", 9), foreground="gray").pack()
        
        ttk.Separator(self.window, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)
        
        # Navigation
        nav_frame = ttk.Frame(self.window, padding=10)
        nav_frame.pack(fill=tk.X, padx=20)
        
        self.prev_btn = ttk.Button(nav_frame, text="◀ Назад", command=self.prev_image)
        self.prev_btn.pack(side=tk.LEFT)
        
        self.counter_label = ttk.Label(nav_frame, text="", font=("Arial", 10))
        self.counter_label.pack(side=tk.LEFT, expand=True)
        
        self.next_btn = ttk.Button(nav_frame, text="Вперёд ▶", command=self.next_image)
        self.next_btn.pack(side=tk.RIGHT)
        
        # Action buttons
        action_frame = ttk.Frame(self.window, padding=10)
        action_frame.pack(fill=tk.X, padx=20)
        
        ttk.Button(action_frame, text="Сохранить изменения",
                   command=self.save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Закрыть",
                   command=self.on_close).pack(side=tk.RIGHT, padx=5)
        
        # Keyboard bindings
        self.window.bind('<Left>', lambda e: self.prev_image())
        self.window.bind('<Right>', lambda e: self.next_image())
        self.window.bind('<Escape>', lambda e: self.on_close())
        
        for key in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            self.window.bind(key, lambda e, k=key: self.change_label(k))
        self.window.bind('<comma>', lambda e: self.change_label(','))
        self.window.bind('<minus>', lambda e: self.change_label('-'))
        self.window.bind('<space>', lambda e: self.change_label(' '))
        self.window.bind('<Delete>', lambda e: self.delete_current())
        self.window.bind('<BackSpace>', lambda e: self.delete_current())
    
    # ------------------------------------------------------------------
    # Navigation and Editing
    # ------------------------------------------------------------------
    
    def show_current_image(self):
        """Display the current image"""
        if not self.images:
            self.image_label.config(image='')
            self.current_label_var.set("Нет изображений")
            self.counter_label.config(text="0/0")
            return
        
        img_data = self.images[self.current_index]
        img = cv2.imread(img_data['path'])
        if img is None:
            self.current_label_var.set("Ошибка загрузки")
            return
        
        h, w = img.shape[:2]
        img = cv2.resize(img, (w * 3, h * 3), interpolation=cv2.INTER_NEAREST)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        self.photo = ImageTk.PhotoImage(pil_img)
        
        self.image_label.config(image=self.photo)
        self.current_label_var.set(img_data['label'])
        self.counter_label.config(
            text=f"Изображение {self.current_index + 1} из {len(self.images)}"
        )
        self.prev_btn.config(state='normal' if self.current_index > 0 else 'disabled')
        self.next_btn.config(state='normal' if self.current_index < len(self.images) - 1 else 'disabled')
    
    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()
    
    def next_image(self):
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.show_current_image()
    
    def change_label(self, new_label):
        if not self.images:
            return
        img_data = self.images[self.current_index]
        old_label = img_data['label']
        if old_label == new_label:
            return
        self.changes[img_data['path']] = {
            'new_label': new_label,
            'old_label': old_label,
            'old_folder': img_data['folder']
        }
        img_data['label'] = new_label
        self.current_label_var.set(new_label)
    
    def delete_current(self):
        if not self.images:
            return
        img_data = self.images[self.current_index]
        answer = messagebox.askyesno(
            "Удалить изображение?",
            f"Удалить это изображение?\n\n"
            f"Текущая метка: {img_data['label']}\n"
            f"Файл: {os.path.basename(img_data['path'])}"
        )
        if not answer:
            return
        self.deleted.append(img_data['path'])
        self.images.pop(self.current_index)
        if self.current_index >= len(self.images):
            self.current_index = max(0, len(self.images) - 1)
        self.show_current_image()
    
    # ------------------------------------------------------------------
    # Save and Close
    # ------------------------------------------------------------------
    
    def save_changes(self):
        if not self.changes and not self.deleted:
            messagebox.showinfo("Нет изменений", "Нет изменений для сохранения.")
            return
        
        answer = messagebox.askyesno(
            "Сохранить изменения?",
            f"Будет изменено меток: {len(self.changes)}\n"
            f"Будет удалено изображений: {len(self.deleted)}\n\n"
            "Это нельзя отменить. Продолжить?"
        )
        if not answer:
            return
        
        data_path = os.path.join('model', 'autosaved')
        
        for path, info in self.changes.items():
            new_label = info['new_label']
            filename = os.path.basename(path)
            new_folder = os.path.join(data_path, new_label)
            os.makedirs(new_folder, exist_ok=True)
            new_path = os.path.join(new_folder, filename)
            try:
                os.rename(path, new_path)
            except Exception as e:
                print(f"[ERROR] Failed to move {filename}: {e}")
        
        for path in self.deleted:
            try:
                os.remove(path)
            except Exception as e:
                print(f"[ERROR] Failed to delete {path}: {e}")
        
        self.changes = {}
        self.deleted = []
        self.images = []
        self.current_index = 0
        self.show_folder_selection()
        messagebox.showinfo("Готово!", "Изменения сохранены!")
    
    def back_to_selection(self):
        if self.changes or self.deleted:
            answer = messagebox.askyesnocancel("Несохранённые изменения", "Сохранить изменения перед возвратом?")
            if answer is None:
                return
            elif answer:
                self.save_changes()
        self.images = []
        self.current_index = 0
        self.changes = {}
        self.deleted = {}
        self.show_folder_selection()
    
    def on_close(self):
        if self.changes or self.deleted:
            answer = messagebox.askyesnocancel(
                "Несохранённые изменения",
                "У вас есть несохранённые изменения!\n\n"
                "• Да - сохранить и закрыть\n"
                "• Нет - закрыть без сохранения\n"
                "• Отмена - продолжить редактирование"
            )
            if answer is None:
                return
            elif answer:
                self.save_changes()
        self.window.destroy()