import os
import cv2
import numpy as np
from albumentations import Compose, Rotate, ShiftScaleRotate, RandomScale, RandomBrightnessContrast
from preprocessing import preprocess_one_digit_area

input_file = "minus_scan.jpeg"
output_dir = "minus_new_6400/"

os.makedirs(output_dir, exist_ok=True)

augmentations = Compose([
    Rotate(limit=5, p=0.3),
    ShiftScaleRotate(rotate_limit=5, p=0.5),
    RandomScale(scale_limit=0.2, p=0.5),
    RandomBrightnessContrast(brightness_limit=0.1, contrast_limit=0.1, p=0.5),
])

img = cv2.imread(input_file)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

nx = 23  # How many squares across?
ny = 24   # How many squares down?

height, width = gray.shape
w = width // nx
h = height // ny

print(f"Processing {nx}x{ny} grid = {nx*ny} cells...")

for i in range(ny):
    y = i * height // ny
    for j in range(nx):
        x = j * width // nx
        image = gray[y + 7 : y+h - 5, x + 5 : x+w - 5]
        base_name = str(i * nx + j)
        
        image = preprocess_one_digit_area(image, 50, 28)
        cv2.imwrite(os.path.join(output_dir, f"0_{base_name}.jpg"), image)
        
        for k in range(1, 20):
            augmented = augmentations(image=image)["image"]
            augmented = preprocess_one_digit_area(augmented, 50, 28, invert=False)
            cv2.imwrite(os.path.join(output_dir, f"{k}_{base_name}.jpg"), augmented)

print(f"Done! Created minus images in {output_dir}")