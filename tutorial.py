# tutorial.py
import tkinter as tk
from tkinter import ttk, messagebox


def get_tutorial_text():
    """Return the tutorial content as a string"""
    return """
╔══════════════════════════════════════════════════════════════════╗
║                    РУКОВОДСТВО ПОЛЬЗОВАТЕЛЯ                       ║
║                  Система распознавания бланков                    ║
╚══════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────┐
│ 1. ВЫБОР РАБОЧЕЙ ПАПКИ                                           │
└──────────────────────────────────────────────────────────────────┘
   • В выпадающем списке выберите папку с настройками бланка
   • Или нажмите "Выбрать папку" и укажите путь вручную
   • В папке должен быть файл схемы (.set)

┌──────────────────────────────────────────────────────────────────┐
│ 2. СОЗДАНИЕ БЛАНКА                                               │
└──────────────────────────────────────────────────────────────────┘
   • Нажмите кнопку "Создать бланк"
   • Настройте параметры:
     - Количество заданий
     - Баллы за каждое задание
     - Типы проверки:
       0 = не проверять
       1 = точное совпадение
       2 = таблица/последовательность
       3 = множество (порядок не важен)

┌──────────────────────────────────────────────────────────────────┐
│ 3. НАСТРОЙКА КАМЕРЫ                                              │
└──────────────────────────────────────────────────────────────────┘
   Клавиши управления в главном окне:
   • ← ↑ → ↓  - перемещение области сканирования
   • + / -    - увеличение / уменьшение области

┌──────────────────────────────────────────────────────────────────┐
│ 4. СКАНИРОВАНИЕ                                                  │
└──────────────────────────────────────────────────────────────────┘
   • Нажмите "Начать сканирование" или клавишу Enter
   • В открывшемся окне:
      Enter - продолжить распознавание
      ESC   - отменить
      -/+ - регулировка яркости

┌──────────────────────────────────────────────────────────────────┐
│ 5. ПРОВЕРКА И КОРРЕКТИРОВКА                                      │
└──────────────────────────────────────────────────────────────────┘
   После распознавания:
   • Кликните мышью на любую клетку для исправления
   • Нажмите 0-9 или запятую (пробел для пустой клтеки)
   • Enter - сохранить результат
   • ESC   - отменить

┌──────────────────────────────────────────────────────────────────┐
│ 6. СОХРАНЕНИЕ РЕЗУЛЬТАТОВ                                        │
└──────────────────────────────────────────────────────────────────┘
   • Нажмите "Сохранить результаты"
   • Или "Сохранить в Excel" в окне результатов
   • Выберите формат: TXT, CSV, JSON или Excel

┌──────────────────────────────────────────────────────────────────┐
│ 7. ФАЙЛЫ ОТВЕТОВ (.var)                                          │
└──────────────────────────────────────────────────────────────────┘
   Для автоматической проверки:
   • Создайте в рабочей папке файл с именем варианта (000.var)
   • Каждая строка - правильный ответ на задание

═══════════════════════════════════════════════════════════════════
                    Удачной работы с программой!
═══════════════════════════════════════════════════════════════════
"""


def open_tutorial(parent, theme_colors=None):
    """
    Open a tutorial window with the same theme as parent.
    
    Args:
        parent: The parent Tkinter window
        theme_colors: Optional dict with 'bg', 'fg', 'btn_bg' keys
    """
    # Default light theme if none provided
    if theme_colors is None:
        theme_colors = {
            'bg': '#f0f0f0',
            'fg': '#000000',
            'btn_bg': '#2196F3'
        }
    
    tutorial_window = tk.Toplevel(parent)
    tutorial_window.title("Руководство пользователя")
    tutorial_window.geometry("700x600")
    tutorial_window.minsize(600, 500)
    tutorial_window.configure(bg=theme_colors['bg'])
    
    tutorial_window.transient(parent)
    tutorial_window.grab_set()
    
    # Main frame
    main_frame = tk.Frame(tutorial_window, bg=theme_colors['bg'])
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Text widget with theme colors
    text_bg = theme_colors['bg']
    text_fg = theme_colors['fg']
    
    text_widget = tk.Text(
        main_frame,
        wrap=tk.WORD,
        font=("Consolas", 10),
        padx=15,
        pady=15,
        bg=text_bg,
        fg=text_fg,
        insertbackground=text_fg,
        relief=tk.FLAT,
        borderwidth=0
    )
    text_widget.insert(tk.END, get_tutorial_text())
    text_widget.config(state=tk.DISABLED)
    text_widget.pack(fill=tk.BOTH, expand=True)
    
    # Enable mouse wheel scrolling
    def on_mousewheel(event):
        text_widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
    text_widget.bind("<MouseWheel>", on_mousewheel)
    
    # Close button
    btn_frame = tk.Frame(tutorial_window, bg=theme_colors['bg'])
    btn_frame.pack(pady=10)
    
    close_btn = tk.Button(
        btn_frame,
        text="Закрыть",
        font=("Arial", 10),
        command=tutorial_window.destroy,
        bg=theme_colors['btn_bg'],
        fg="white",
        padx=20,
        pady=5,
        cursor="hand2",
        relief=tk.RAISED,
        borderwidth=1
    )
    close_btn.pack()
    
    tutorial_window.bind("<Escape>", lambda e: tutorial_window.destroy())
    
    return tutorial_window



def open_credits(parent, theme_colors=None):
    """Show credits with theme"""
    if theme_colors is None:
        theme_colors = {
            'bg': '#f0f0f0',
            'fg': '#000000',
            'btn_bg': '#2196F3'
        }
    
    credits_window = tk.Toplevel(parent)
    credits_window.title("Credits")
    credits_window.geometry("400x350")
    credits_window.configure(bg=theme_colors['bg'])
    credits_window.transient(parent)
    credits_window.grab_set()

    credit_text = """ CREDITS
Two close high school friends:
┌────────────────────┬────────────────────────┐
│       Ivan         │       Scherbakov       │
└────────────────────┴────────────────────────┘
┌────────────────────┬────────────────────────┐
│       Mike         │       Kudryavtsev      │
└────────────────────┴────────────────────────┘
One and only, the name-of-whom-must-not-be-spoken-
-but-I-will-make-an-exception-this-time, an
ultimate Physics Teacher
┌────────────────────┬────────────────────────┐
│       Olga         │       Alekseevna       │
└────────────────────┴────────────────────────┘
    """

    text_widget = tk.Text(
        credits_window,
        wrap=tk.WORD,
        font=("Consolas", 10),
        padx=20,
        pady=20,
        bg=theme_colors['bg'],
        fg=theme_colors['fg'],
        relief=tk.FLAT,
        borderwidth=0,
        spacing1=5
    )
    text_widget.insert(tk.END, credit_text)
    text_widget.config(state=tk.DISABLED)
    text_widget.pack(fill=tk.BOTH, expand=True)
    
    close_btn = tk.Button(
        credits_window,
        text="Закрыть",
        font=("Arial", 10),
        command=credits_window.destroy,
        bg=theme_colors['btn_bg'],
        fg="white",
        padx=20,
        pady=5,
        cursor="hand2"
    )
    close_btn.pack(pady=10)
    
    credits_window.bind("<Escape>", lambda e: credits_window.destroy())