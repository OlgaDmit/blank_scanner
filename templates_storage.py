import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import os
import json
import shutil
from scheme_loader import load_blank_scheme

TEMPLATES_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates_storage")
TEMPLATES_INDEX = os.path.join(TEMPLATES_STORAGE, "templates_index.json")
os.makedirs(TEMPLATES_STORAGE, exist_ok=True)

def save_template_to_storage(template_path, template_name=None):
    """Сохраняет шаблон во внутреннее хранилище и возвращает его ID."""
    try:
        # Если имя не указано, запрашиваем у пользователя
        if not template_name:
            from tkinter import simpledialog
            template_name = simpledialog.askstring(
                "Название шаблона",
                "Введите название для шаблона (например: ЕГЭ 2026 профиль):",
                parent=tk._default_root
            )
            if not template_name:
                template_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Копируем .png и .set файлы в хранилище
        png_file = template_path
        set_file = os.path.splitext(template_path)[0] + ".set"
        
        if not os.path.exists(png_file) or not os.path.exists(set_file):
            print(f"Ошибка: файлы шаблона не найдены: {png_file}, {set_file}")
            return None
        
        # Создаём папку для этого шаблона в хранилище (используем имя с временной меткой)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = template_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        folder_name = f"{safe_name}_{timestamp}"
        template_folder = os.path.join(TEMPLATES_STORAGE, folder_name)
        os.makedirs(template_folder, exist_ok=True)
        
        # Копируем файлы
        import shutil
        dest_png = os.path.join(template_folder, "blank.png")
        dest_set = os.path.join(template_folder, "blank.set")
        
        shutil.copy2(png_file, dest_png)
        shutil.copy2(set_file, dest_set)
        
        # Обновляем индекс
        index = load_templates_index()
        template_id = folder_name
        index[template_id] = {
            "name": template_name,
            "folder": folder_name,
            "path": template_folder,
            "created": datetime.now().isoformat(),
            "original_path": template_path
        }
        save_templates_index(index)
        
        return template_id
    except Exception as e:
        print(f"Ошибка сохранения шаблона в хранилище: {e}")
        return None
    
def copy_template_to_work_folder(template_id, target_folder):
    """Копирует шаблон из хранилища в указанную рабочую папку."""
    index = load_templates_index()
    if template_id not in index:
        return False, "Шаблон не найден"
    
    template_info = index[template_id]
    source_folder = template_info["path"]
    
    source_png = os.path.join(source_folder, "blank.png")
    source_set = os.path.join(source_folder, "blank.set")
    
    if not os.path.exists(source_png) or not os.path.exists(source_set):
        return False, "Файлы шаблона повреждены"
    
    import shutil
    # Копируем в целевую папку
    dest_png = os.path.join(target_folder, "blank_template.png")
    dest_set = os.path.join(target_folder, os.path.basename(source_set))
    
    shutil.copy2(source_png, dest_png)
    shutil.copy2(source_set, dest_set)

    return True, "Шаблон скопирован успешно"

def load_templates_index():
    """Загружает индекс всех сохранённых шаблонов."""
    if os.path.exists(TEMPLATES_INDEX):
        try:
            with open(TEMPLATES_INDEX, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_templates_index(index):
    """Сохраняет индекс шаблонов."""
    try:
        with open(TEMPLATES_INDEX, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка сохранения индекса шаблонов: {e}")

def get_recent_templates(limit=10):
    """Возвращает список недавних шаблонов."""
    index = load_templates_index()
    # Сортируем по дате создания (новые сначала)
    sorted_templates = sorted(
        index.items(),
        key=lambda x: x[1].get("created", ""),
        reverse=True
    )
    return sorted_templates[:limit]

def load_template_from_storage(template_id):
    """Загружает шаблон из хранилища по ID."""
    index = load_templates_index()
    if template_id not in index:
        return None
    template_info = index[template_id]
    set_file = os.path.join(template_info["path"], "blank.set")
    if os.path.exists(set_file):
        return load_blank_scheme(template_info["path"])
    return None

def delete_template_from_storage(template_id):
    """Удаляет шаблон из хранилища."""
    index = load_templates_index()
    if template_id in index:
        import shutil
        template_path = index[template_id]["path"]
        if os.path.exists(template_path):
            shutil.rmtree(template_path)
        del index[template_id]
        save_templates_index(index)
        return True
    return False