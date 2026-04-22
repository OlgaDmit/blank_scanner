import os
import glob

def load_blank_scheme(current_path):
    # Ищем файл .set в папке
    search_pattern = os.path.join(current_path, "*.set")
    config_files = glob.glob(search_pattern)
    if not config_files:
        # Если нет .set, ищем .txt
        config_files = glob.glob(os.path.join(current_path, "*.txt"))
        if not config_files:
            return None
    # Берём первый найденный файл
    scheme_file = config_files[0]
    try:
        with open(scheme_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Проверяем, похоже ли на схему (должно быть много строк с числами)
        if len(lines) >= 7 and lines[4].strip().replace('.', '').isdigit():
            # Это полноценный файл схемы (как blank_template.txt)
            blank_scheme = {}
            blank_scheme['problems_names'] = lines[0].strip().split()
            blank_scheme['rates'] = list(map(int, lines[1].strip().split()))
            blank_scheme['check_keys'] = list(map(int, lines[2].strip().split()))
            blank_scheme['image_size'] = list(map(int, lines[3].strip().split()))
            blank_scheme['max_area'] = float(lines[4].strip())
            blank_scheme['field_sizes'] = list(map(int, lines[5].strip().split()))
            blank_scheme['var_coords'] = list(map(int, lines[6].strip().split()))
            blank_scheme['problems_coords'] = []
            blank_scheme['rates_coords'] = []
            for line in lines[7:]:
                if line.strip():
                    parts = list(map(int, line.strip().split()))
                    blank_scheme['problems_coords'].append(parts[:3])
                    blank_scheme['rates_coords'].append(parts[3:])
            return blank_scheme
        else:
            # Старый формат: первая строка — имя файла схемы
            scheme_filename = lines[0].strip()
            full_scheme_path = os.path.join(current_path, scheme_filename)
            if not os.path.isfile(full_scheme_path):
                return None
            with open(full_scheme_path, 'r', encoding='utf-8') as g:
                # Читаем как выше
                blank_scheme = {}
                blank_scheme['problems_names'] = g.readline().strip().split()
                blank_scheme['rates'] = list(map(int, g.readline().split()))
                blank_scheme['check_keys'] = list(map(int, g.readline().split()))
                blank_scheme['image_size'] = list(map(int, g.readline().split()))
                blank_scheme['max_area'] = float(g.readline())
                blank_scheme['field_sizes'] = list(map(int, g.readline().split()))
                blank_scheme['var_coords'] = list(map(int, g.readline().split()))
                blank_scheme['problems_coords'] = []
                blank_scheme['rates_coords'] = []
                for line in g:
                    parts = list(map(int, line.strip().split()))
                    blank_scheme['problems_coords'].append(parts[:3])
                    blank_scheme['rates_coords'].append(parts[3:])
                return blank_scheme
    except Exception as e:
        print(f"Ошибка загрузки схемы: {e}")
        return None