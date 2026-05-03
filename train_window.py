import tkinter as tk
from tkinter import ttk, messagebox
import os
import glob
import numpy as np
import threading

class TrainWindow:
    
    def __init__(self, parent, theme_colors=None):
        self.parent = parent
        self.theme_colors = theme_colors or {}
        self.training_thread = None
        self.is_training = False
        
        self.window = tk.Toplevel(parent)
        self.window.title("Обучение модели")
        self.window.geometry("550x500")
        self.window.minsize(450, 400)
        self.window.transient(parent)
        self.window.grab_set()

        header = ttk.Label(
            self.window,
            text="Обучение модели на рукописных цифрах",
            font=("Arial", 14, "bold")
        )
        header.pack(pady=20)
        
        self.setup_stats_section()
        self.setup_progress_section()
        self.setup_buttons()
        self.update_stats()
        
        self.window.bind('<Escape>', lambda e: self.on_close())

    def setup_stats_section(self):
        stats_frame = ttk.LabelFrame(self.window, text="Доступно данных", padding=10)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.stats_text = tk.Text(stats_frame, height=5, width=50, 
                                   font=("Consolas", 10), state=tk.DISABLED)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        self.total_label = ttk.Label(stats_frame, text="", font=("Arial", 10, "bold"))
        self.total_label.pack(pady=5)

    def count_autosaved_images(self):
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
    
    def update_stats(self):
        counts, total = self.count_autosaved_images()
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        
        class_order = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ',', '-']
        row = ""
        for i, class_name in enumerate(class_order):
            count = counts.get(class_name, 0)
            row += f"{class_name}: {count:3d}   "
            if (i + 1) % 4 == 0:
                self.stats_text.insert(tk.END, row + "\n")
                row = ""
        if row:
            self.stats_text.insert(tk.END, row + "\n")
        
        self.stats_text.config(state=tk.DISABLED)
        
        if total == 0:
            self.total_label.config(text="Нет данных для обучения. Сканируйте бланки!")
        else:
            self.total_label.config(text=f"Всего изображений: {total}")

            
    def setup_progress_section(self):
        self.progress_frame = ttk.LabelFrame(self.window, text="Прогресс", padding=10)
        self.progress_frame.pack(fill=tk.X, padx=20, pady=10)

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(self.progress_frame, text="Готов к обучению", font=("Arial", 9))
        self.status_label.pack()

    def setup_buttons(self):
        btn_frame = ttk.Frame(self.window, padding=10)
        btn_frame.pack(fill=tk.X, padx=20)
        
        self.train_btn = ttk.Button(btn_frame, text="Начать обучение", command=self.start_training)
        self.train_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="❌ Закрыть", command=self.on_close).pack(side=tk.RIGHT, padx=5)

    def start_training(self):
        counts, total = self.count_autosaved_images()
        
        if total < 10:
            messagebox.showwarning("Мало данных", 
                "Недостаточно изображений для обучения!\n"
                "Сканируйте больше бланков и исправляйте ошибки.")
            return
        
        answer = messagebox.askyesno(
            "Начать обучение",
            f"Будет использовано {total} изображений.\n"
            f"Обучение займёт 2-5 минут.\n\n"
            "Начать?"
        )
        if not answer:
            return
        
        self.train_btn.config(state='disabled')
        self.is_training = True
        self.status_label.config(text="Подготовка данных...")
        self.progress_bar.config(value=0)
        
        self.training_thread = threading.Thread(target=self.run_training, daemon=True)
        self.training_thread.start()
        
        self.check_training_progress()
    
    def run_training(self):
        try:
            import cv2
            from tensorflow.keras.models import load_model
            from tensorflow.keras.utils import to_categorical
            from tensorflow.keras.optimizers import SGD
            from sklearn.model_selection import train_test_split
            from preprocessing import preprocess_one_digit_area
            
            model_path = 'model/mnist_new.h5'
            if not os.path.exists(model_path):
                self.update_status("Модель не найдена!")
                return
            
            self.update_status("Загрузка модели...")
            self.update_progress(10)
            model = load_model(model_path)
            
            self.update_status("Загрузка рукописных данных...")
            X_new, y_new = self._load_autosaved_data()
            
            if len(X_new) < 5:
                self.update_status("Слишком мало данных!")
                return
            
            self.update_progress(30)
            
            self.update_status("Добавление данных MNIST...")
            from keras.datasets import mnist
            (x_mnist, y_mnist), _ = mnist.load_data()
            
            # Take a balanced sample
            sample_size = min(5000, len(X_new) * 2)
            indices = np.random.choice(len(x_mnist), sample_size, replace=False)
            x_mnist_sample = x_mnist[indices]
            y_mnist_sample = y_mnist[indices]
            
            # Preprocess MNIST sample
            x_mnist_processed = []
            for img in x_mnist_sample:
                processed = preprocess_one_digit_area(img, 28, 28, invert=False)
                x_mnist_processed.append(processed)
            x_mnist_sample = np.array(x_mnist_processed)
            
            x_mnist_sample = x_mnist_sample.astype('float32') / 255.0
            x_mnist_sample = x_mnist_sample.reshape(-1, 28, 28, 1)
            y_mnist_sample_cat = to_categorical(y_mnist_sample, num_classes=12)
            
            X_combined = np.concatenate([X_new, x_mnist_sample])
            y_combined = np.concatenate([y_new, y_mnist_sample_cat])
            
            self.update_progress(50)
            
            X_train, X_val, y_train, y_val = train_test_split(
                X_combined, y_combined, test_size=0.2, random_state=42
            )
            
            self.update_status("Подготовка модели...")
            for layer in model.layers[:4]:
                layer.trainable = False
            
            # Compile with lower learning rate
            model.compile(
                optimizer=SGD(learning_rate=0.001, momentum=0.9),
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            self.update_progress(60)
            
            epochs = 5
            
            for epoch in range(epochs):
                self.update_status(f"Обучение... Эпоха {epoch + 1}/{epochs}")
                
                history = model.fit(
                    X_train, y_train,
                    batch_size=32,
                    epochs=1,
                    validation_data=(X_val, y_val),
                    verbose=0
                )
                
                progress = 60 + int((epoch + 1) / epochs * 35)
                self.update_progress(progress)
            
            self.update_status("Сохранение модели...")
            model.save('model/mnist_new.h5')
            self.update_progress(100)
            
            self.update_status("Обучение завершено! Модель обновлена.")
            
            # Show completion message (in main thread)
            self.window.after(0, lambda: messagebox.showinfo(
                "Готово!",
                f"Модель успешно обучена!\n\n"
                f"Эпох: {epochs}\n\n"
                "Новая модель сохранена как model/mnist_new.h5"
            ))
            
        except Exception as e:
            self.update_status(f"Ошибка: {str(e)[:100]}")
            print(f"[ERROR] Training failed: {e}")
        
        finally:
            self.is_training = False
            self.window.after(0, lambda: self.train_btn.config(state='normal'))

    def _load_autosaved_data(self):
        import cv2
        from preprocessing import preprocess_one_digit_area
        from tensorflow.keras.utils import to_categorical
        
        data_path = os.path.join('model', 'autosaved')
        images = []
        labels = []
        
        # Map folder names to class indices
        class_map = {
            '0': 0, '1': 1, '2': 2, '3': 3, '4': 4,
            '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            ',': 10, '-': 11
        }
        
        for folder_name in os.listdir(data_path):
            folder_path = os.path.join(data_path, folder_name)
            if not os.path.isdir(folder_path):
                continue
            
            if folder_name not in class_map:
                continue
            label = class_map[folder_name]
            
            for filename in os.listdir(folder_path):
                if filename.endswith('.jpg'):
                    img_path = os.path.join(folder_path, filename)
                    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        img = preprocess_one_digit_area(img, 42, 28, sharpness=1.1)
                        images.append(img)
                        labels.append(label)
        
        X = np.array(images).astype('float32') / 255.0
        X = X.reshape(-1, 28, 28, 1)
        y = to_categorical(np.array(labels), num_classes=12)
        
        return X, y
    
    def update_progress(self, value):
        self.window.after(0, lambda: self.progress_bar.config(value=value))
    
    def update_status(self, text):
        self.window.after(0, lambda: self.status_label.config(text=text))
    
    def check_training_progress(self):
        if self.is_training:
            self.window.after(200, self.check_training_progress)
    
    def on_close(self):
        if self.is_training:
            messagebox.showwarning("Обучение идёт", 
                "Дождитесь завершения обучения!")
            return
        self.window.destroy()