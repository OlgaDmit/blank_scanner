import os
import cv2
import numpy as np
from albumentations import (
    Compose, Rotate, ShiftScaleRotate, RandomScale, 
    RandomBrightnessContrast, HorizontalFlip, VerticalFlip
)
from tqdm import tqdm
import math
from scipy.ndimage.measurements import center_of_mass
import matplotlib.pyplot as plt
from preprocessing import preprocess_one_digit_area

# Путь к исходным изображениям и папке для аугментированных данных
input_file = "commas_scan.jpeg"
output_dir = "commas_new_6400/"
os.makedirs(output_dir, exist_ok=True)

# Определяем аугментации
augmentations = Compose([
    Rotate(limit=15, p=0.5),  # случайный поворот до 15 градусов
    ShiftScaleRotate(rotate_limit=10, p=0.7),  # сдвиг + масштаб + поворот
    RandomScale(scale_limit=0.2, p=0.5),
    RandomBrightnessContrast(brightness_limit=0.1, contrast_limit=0.1, p=0.5),  # изменение яркости/контраста
])

# Загружаем исходные изображения
img = cv2.imread(input_file)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)



nx = 26
ny = 8

height, width = gray.shape
w = width // nx
h = height // ny

# Аугментируем каждое изображение 9 раз (320 × 10 = 3200)
for i in range(ny):
    y = i * height // ny
    for j in range(nx):
        x = j * width // nx
        
        image = gray[y + 7 : y+h - 5, x + 5 : x+w - 5]
        
        # Сохраняем оригинал
        base_name = str(i * nx + j)
        
        image = preprocess_one_digit_area(image, 50, 28)
        
        cv2.imwrite(os.path.join(output_dir, f"0_{base_name}.jpg"), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        
        # Генерируем 19 аугментированных версий
        N = 20
        for k in range(1, N-1):
            augmented = augmentations(image=image)["image"]
            
            augmented = preprocess_one_digit_area(augmented, 50, 28, invert = False)
            
            cv2.imwrite(os.path.join(output_dir, f"{k}_{base_name}.jpg"), cv2.cvtColor(augmented, cv2.COLOR_RGB2BGR))

print(f"Аугментация завершена! Из {nx*ny} изображений создано {nx*ny*N}.")