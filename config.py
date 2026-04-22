import os

def save_settings(path_arr, scaling, sharpness, dark_mode=False):
    x, y, w, h = scaling[:]
    
    with open('.blank_ocr_config', 'w') as f:
        f.write(f'scaling: {x} {y} {w} {h}\n')
        f.write(f'sharpness: {sharpness}\n')
        f.write(f'dark_mode: {dark_mode}\n')
        for line in path_arr:
            f.write(line + '\n')

def load_config():
    path_arr = []
    scaling = None
    sharpness = 1.0
    dark_mode = False
    try:
        with open('.blank_ocr_config', 'r') as f:
            for line in f:
                if line.startswith('scaling'):
                    parts = list(map(int, line.split()[1:5]))
                    if len(parts) == 4:
                        scaling = parts
                elif line.startswith('sharpness'):
                    sharpness = float(line.split()[1])
                elif line.startswith('dark_mode'):  # ADD THIS BLOCK
                    dark_mode = line.split()[1].lower() == 'true'
                else:
                    path = line.strip()
                    if os.path.isdir(path):
                        path_arr.append(path)
    except FileNotFoundError:
        pass
    return path_arr, scaling, sharpness, dark_mode