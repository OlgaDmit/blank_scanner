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
from preprocessing import preprocess_one_digit_area

# Путь к исходным изображениям и папке для аугментированных данных
input_dir = "commas/"
output_dir = "commas3200/"
os.makedirs(output_dir, exist_ok=True)

# Определяем аугментации
augmentations = Compose([
    Rotate(limit=15, p=0.5),  # случайный поворот до 15 градусов
    ShiftScaleRotate(rotate_limit=10, p=0.7),  # сдвиг + масштаб + поворот
    RandomScale(scale_limit=0.2, p=0.5),
    RandomBrightnessContrast(brightness_limit=0.1, contrast_limit=0.1, p=0.5),  # изменение яркости/контраста
])

# Загружаем исходные изображения
image_files = [f for f in os.listdir(input_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]

# Аугментируем каждое изображение 9 раз (320 × 10 = 3200)
for img_name in tqdm(image_files):
    img_path = os.path.join(input_dir, img_name)
    image = cv2.imread(img_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Сохраняем оригинал
    base_name = os.path.splitext(img_name)[0]
    
    image = preprocess_one_digit_area(image, 64, 28, invert = False, sharpness = 1)
        
    cv2.imwrite(os.path.join(output_dir, f"0_{base_name}.jpg"), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    
    # Генерируем 19 аугментированных версий
    N = 10
    for i in range(1, N-1):
        augmented = augmentations(image=image)["image"]
        
        augmented = preprocess_one_digit_area(augmented, 64
        
        , 28, invert = False, sharpness = 1)
        
        cv2.imwrite(os.path.join(output_dir, f"{i}_{base_name}.jpg"), cv2.cvtColor(augmented, cv2.COLOR_RGB2BGR))

print(f"Аугментация завершена! Из {len(image_files)} изображений создано {len(image_files) * N}.")