import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import csv
from datetime import datetime
from excel_saver import find_excel_file, open_workbook, save_workbook, find_variant_sheet
from excel_saver import get_all_students, find_student_row, write_scores_to_sheet, get_sheet_by_name, get_all_sheets
from google_sheets_saver import (
    get_authenticated_service, load_google_sheet_link, save_google_sheet_link,
    get_all_sheets, get_all_students, find_student_row, write_scores_to_sheet
)
import pyperclip

class ResultsWindow:

    def __init__(self, parent, score, recognized_answers, current_path, blank_scheme, theme_colors=None):
        self.parent = parent
        self.root = parent
        self.score = score
        self.recognized_answers = recognized_answers
        self.current_path = current_path
        self.blank_scheme = blank_scheme
        self.theme_colors = theme_colors or {}

        self.last_recognized_answers = recognized_answers
        self.last_score = score

        self.result_win = tk.Toplevel(parent)
        self.result_win.title("Результаты распознавания")
        self.result_win.geometry("500x600")
        self.result_win.transient(parent)
        self.result_win.grab_set()
        
        def on_esc(event):
            self.result_win.destroy()
            
        self.result_win.bind('<Escape>', on_esc)
        self.result_win.focus_set()

        # Фрейм с прокруткой
        canvas = tk.Canvas(self.result_win)
        scrollbar = ttk.Scrollbar(self.result_win, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Заголовок
        variant = ''.join(recognized_answers[0]).strip() if recognized_answers else "???"
        ttk.Label(scrollable_frame, text=f"Вариант: {variant}", 
                font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Label(scrollable_frame, text=f"Распознано {len(score)} заданий", 
                font=("Arial", 12, "bold")).pack(pady=5)
        
        # Разделитель
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill=tk.X, pady=5)

        # Результаты по заданиям
        frame_tasks = ttk.Frame(scrollable_frame)
        frame_tasks.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Заголовки столбцов
        header_frame = ttk.Frame(frame_tasks)
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="Задание", width=10, anchor=tk.CENTER).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="Баллы", width=10, anchor=tk.CENTER).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="Статус", width=10, anchor=tk.CENTER).pack(side=tk.LEFT)
        
        ttk.Separator(frame_tasks, orient='horizontal').pack(fill=tk.X, pady=2)

        # Список результатов с прокруткой
        tasks_canvas = tk.Canvas(frame_tasks, height=300)
        tasks_scrollbar = ttk.Scrollbar(frame_tasks, orient="vertical", command=tasks_canvas.yview)
        tasks_frame = ttk.Frame(tasks_canvas)
        tasks_frame.bind(
            "<Configure>",
            lambda e: tasks_canvas.configure(scrollregion=tasks_canvas.bbox("all"))
        )
        tasks_canvas.create_window((0, 0), window=tasks_frame, anchor="nw")
        tasks_canvas.configure(yscrollcommand=tasks_scrollbar.set)
        
        total_points = 0
        for i, (points, is_correct) in enumerate(score, 1):
            frame = ttk.Frame(tasks_frame)
            frame.pack(fill=tk.X, pady=1)
            
            status = "✓" if is_correct else "✗"
            color = "green" if is_correct else "red"
            
            ttk.Label(frame, text=f"Задание {i}:", width=10).pack(side=tk.LEFT)
            ttk.Label(frame, text=str(points), width=10).pack(side=tk.LEFT)
            ttk.Label(frame, text=status, foreground=color, font=("Arial", 10, "bold"), width=10).pack(side=tk.LEFT)
            
            total_points += points
        
        tasks_canvas.pack(side="left", fill="both", expand=True)
        tasks_scrollbar.pack(side="right", fill="y")

        # Итого
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(scrollable_frame, text=f"ИТОГО: {total_points} баллов", 
                font=("Arial", 14, "bold"), foreground="blue").pack(pady=5)
        
        # Кнопки действий
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(pady=10)
        
        def save_to_excel_callback():
            self.result_win.destroy()
            self.save_to_excel(recognized_answers, score)
        
        ttk.Button(btn_frame, text="Сохранить в Excel", command=save_to_excel_callback).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Сохранить в Google Sheets", command=self.save_to_google_sheets_callback).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Сохранить как файл", command=self.on_save_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Скопировать баллы", command=self.copy_scores_to_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Закрыть (ESC)", command=self.result_win.destroy).pack(side=tk.LEFT, padx=5)
        
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def on_save_results(self):
        if self.last_recognized_answers is None:
            messagebox.showwarning("Нет данных", "Сначала выполните сканирование.")
            return
        self.save_results_dialog(self.last_recognized_answers, self.last_score)  

    def _browse_folder(self, var):
        folder = filedialog.askdirectory(title="Выберите папку для сохранения результатов")
        if folder:
            var.set(folder) 

    def save_results_dialog(self, recognized_answers, score):
        if not recognized_answers:
            messagebox.showwarning("Нет данных", "Нет результатов для сохранения.")
            return

        dialog = tk.Toplevel(self.result_win)
        dialog.title("Сохранение результатов")
        dialog.geometry("500x300")
        dialog.transient(self.result_win)
        dialog.grab_set()

        student_name_var = tk.StringVar()
        folder_var = tk.StringVar(value=self.current_path if self.current_path else "")
        format_var = tk.StringVar(value="TXT")

        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Имя ученика / ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=student_name_var, width=30).grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(main_frame, text="Папка для сохранения:").grid(row=1, column=0, sticky=tk.W, pady=5)
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Entry(folder_frame, textvariable=folder_var, width=30).pack(side=tk.LEFT)
        ttk.Button(folder_frame, text="Обзор", command=lambda: self._browse_folder(folder_var)).pack(side=tk.LEFT, padx=5)

        ttk.Label(main_frame, text="Формат:").grid(row=2, column=0, sticky=tk.W, pady=5)
        format_combo = ttk.Combobox(main_frame, textvariable=format_var, values=["TXT", "CSV", "JSON"], state="readonly")
        format_combo.grid(row=2, column=1, sticky=tk.W, pady=5)

        def do_save():
            folder = folder_var.get()
            if not folder:
                messagebox.showerror("Ошибка", "Выберите папку для сохранения.")
                return
            if not os.path.isdir(folder):
                try:
                    os.makedirs(folder)
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось создать папку:\n{e}")
                    return

            student = student_name_var.get().strip()
            if not student:
                student = "unknown"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"{student}_{timestamp}"

            variant = ''.join(recognized_answers[0]).strip() if recognized_answers else "???"
            answers = recognized_answers[1:] if len(recognized_answers) > 1 else []
            scores = score if score else []

            data = {
                "student": student,
                "timestamp": timestamp,
                "datetime": datetime.now().isoformat(),
                "variant": variant,
                "answers": {},
                "scores": {}
            }
            for i, ans in enumerate(answers, 1):
                data["answers"][f"task_{i}"] = ''.join(ans).strip()
            for i, (points, is_correct) in enumerate(scores, 1):
                data["scores"][f"task_{i}"] = {"points": points, "correct": is_correct}
            data["total_points"] = sum(p for p, _ in scores) if scores else None

            file_path = os.path.join(folder, base_name)
            try:
                if format_var.get() == "TXT":
                    file_path += ".txt"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"Ученик: {student}\n")
                        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Вариант: {variant}\n\n")
                        f.write("Ответы:\n")
                        for i, ans in enumerate(answers, 1):
                            ans_str = ''.join(ans).strip() or "—"
                            f.write(f"  {i:2d}: {ans_str}\n")
                        if scores:
                            f.write("\nБаллы:\n")
                            for i, (points, correct) in enumerate(scores, 1):
                                status = "+" if correct else "-"
                                f.write(f"  {i:2d}: {points} {status}\n")
                            f.write(f"\nСумма баллов: {sum(p for p,_ in scores)}\n")
                elif format_var.get() == "CSV":
                    file_path += ".csv"
                    with open(file_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(["student", "timestamp", "variant"] + [f"task_{i}" for i in range(1, len(answers)+1)] + [f"score_{i}" for i in range(1, len(scores)+1)] + ["total"])
                        row = [student, timestamp, variant] + [''.join(a).strip() for a in answers] + [p for p,_ in scores] + [sum(p for p,_ in scores)]
                        writer.writerow(row)
                else:  # JSON
                    file_path += ".json"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Успех", f"Результаты сохранены в:\n{file_path}")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Сохранить", command=do_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5) 

    def save_to_google_sheets_callback(self):
        self.result_win.destroy()
        self.save_to_google_sheets(self.recognized_answers, self.score)

    def save_to_google_sheets(self, recognized_answers, score):
        """Сохранить результаты в Google Sheets."""
        if not self.current_path:
            messagebox.showerror("Ошибка", "Не выбрана рабочая папка.")
            return False

        import re

        # 1. Получить ссылку на Google Sheets из файла в рабочей папке
        spreadsheet_ref, link_file = load_google_sheet_link(self.current_path)
        if not spreadsheet_ref:
            # Спрашиваем, хочет ли пользователь указать ссылку
            answer = messagebox.askyesno(
                "Ссылка не найдена",
                "В рабочей папке нет файла со ссылкой на Google Sheets.\n"
                "Хотите указать ссылку сейчас?"
            )
            if not answer:
                return False
            spreadsheet_ref = get_spreadsheet_id_from_user(self.root)
            if not spreadsheet_ref:
                return False
            # Сохраняем ссылку в папку
            save_google_sheet_link(self.current_path, spreadsheet_ref)
        else:
            # Используем найденную ссылку
            pass

        # 2. Аутентификация
        service = get_authenticated_service(self.root)
        if not service:
            return False
        # Извлекаем ID таблицы (если пользователь ввёл URL)
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', spreadsheet_ref)
        spreadsheet_id = match.group(1) if match else spreadsheet_ref
        # 3. Определяем номер варианта
        variant_str = ''.join(recognized_answers[0]).strip()
        variant_match = re.search(r'\d+', variant_str)
        detected_variant = int(variant_match.group()) if variant_match else None

        # 4. Получаем все листы
        all_sheets = get_all_sheets(service, spreadsheet_id)
        if not all_sheets:
            messagebox.showerror("Ошибка", "Не удалось получить список листов.\nПроверьте доступ к таблице.")
            return False

        # 5. Выбираем лист (автоматически по варианту или вручную)
        sheet = None
        if detected_variant:
            # ищем лист, содержащий номер варианта
            for sheet_name in all_sheets:
                if str(detected_variant) in sheet_name:
                    sheet = sheet_name
                    break
        if sheet:
            answer = messagebox.askyesno(
                "Лист найден",
                f"Обнаружен вариант {detected_variant}\n"
                f"Будут использованы данные с листа: '{sheet}'\n\n"
                "Продолжить с этим листом?"
            )
            if not answer:
                sheet = None

        if not sheet:
            # диалог выбора листа
            sheet_win = tk.Toplevel(self.root)
            sheet_win.title("Выбор листа")
            sheet_win.geometry("400x300")
            sheet_win.transient(self.root)
            sheet_win.grab_set()

            tk.Label(sheet_win, text="Выберите лист с результатами:", font=("Arial", 12)).pack(pady=10)
            frame = ttk.Frame(sheet_win)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=listbox.yview)
            for name in all_sheets:
                listbox.insert(tk.END, name)

            selected = [None]
            def on_select():
                sel = listbox.curselection()
                if sel:
                    selected[0] = listbox.get(sel[0])
                    sheet_win.destroy()
                else:
                    messagebox.showwarning("Выбор", "Пожалуйста, выберите лист.")
            ttk.Button(sheet_win, text="Выбрать", command=on_select).pack(pady=10)
            ttk.Button(sheet_win, text="Отмена", command=sheet_win.destroy).pack(pady=5)

            self.root.wait_window(sheet_win)
            if not selected[0]:
                return False
            sheet = selected[0]

        # 6. Список учеников
        students = get_all_students(service, spreadsheet_id, sheet)
        if not students:
            messagebox.showerror("Ошибка", "На листе нет учеников (столбец A).\nДолжны быть начиная с 3 строки.")
            return False

        # 7. Диалог выбора ученика
        student_win = tk.Toplevel(self.root)
        student_win.title("Выберите ученика")
        student_win.geometry("400x400")
        student_win.transient(self.root)
        student_win.grab_set()

        tk.Label(student_win, text="Выберите ученика из списка:", font=("Arial", 12)).pack(pady=10)
        search_frame = ttk.Frame(student_win)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        frame = ttk.Frame(student_win)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        for student in students:
            listbox.insert(tk.END, student)

        def filter_students(event=None):
            text = search_entry.get().strip().lower()
            listbox.delete(0, tk.END)
            for s in students:
                if text in s.lower():
                    listbox.insert(tk.END, s)
        search_entry.bind('<KeyRelease>', filter_students)

        selected_student = [None]
        def on_select():
            sel = listbox.curselection()
            if sel:
                selected_student[0] = listbox.get(sel[0])
                student_win.destroy()
            else:
                messagebox.showwarning("Выбор", "Выберите ученика.")
        def on_double_click(event):
            on_select()
        listbox.bind('<Double-Button-1>', on_double_click)
        ttk.Button(student_win, text="Выбрать", command=on_select).pack(pady=10)
        ttk.Button(student_win, text="Отмена", command=student_win.destroy).pack(pady=5)

        self.root.wait_window(student_win)
        if not selected_student[0]:
            return False

        # 8. Найти строку ученика
        row_idx = find_student_row(service, spreadsheet_id, sheet, selected_student[0])
        if not row_idx:
            answer = messagebox.askyesno(
                "Ученик не найден",
                f"Ученик '{selected_student[0]}' не найден.\nХотите добавить его в конец списка?"
            )
            if answer:
                # Получить последнюю строку с данными
                # Для простоты – добавим в конец через запись в столбец A
                range_name = f"{sheet}!A{len(students)+3}"
                body = {'values': [[selected_student[0]]]}
                try:
                    service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range=range_name,
                        valueInputOption='RAW',
                        body=body
                    ).execute()
                    row_idx = len(students) + 3
                    messagebox.showinfo("Добавлен", f"Ученик добавлен в строку {row_idx}")
                except HttpError as e:
                    messagebox.showerror("Ошибка", f"Не удалось добавить ученика:\n{e}")
                    return False
            else:
                return False

        # 9. Формируем список баллов (27 значений)
        points_list = [p for p, _ in score]
        # Дополняем до 27, если меньше
        if len(points_list) < 27:
            points_list += [0] * (27 - len(points_list))
        # 10. Запись в таблицу
        success = write_scores_to_sheet(service, spreadsheet_id, sheet, row_idx, points_list)
        if success:
            messagebox.showinfo("Успех",
                f"Результаты сохранены в Google Sheets\n"
                f"Лист: {sheet}\nУченик: {selected_student[0]}\n"
                f"Сумма баллов: {sum(points_list)}")
            return True
            return True
        else:
            messagebox.showerror("Ошибка", "Не удалось записать данные в таблицу.")
            return False
    def copy_scores_to_clipboard(self):
        """Копирует только баллы в буфер обмена одной строкой через табуляцию."""
        if not self.score:
            messagebox.showwarning("Нет данных", "Нет результатов для копирования.")
            return
        
        # Формируем строку: только баллы через табуляцию
        points_list = [str(points) for points, _ in self.score]
        output = "\t".join(points_list)
        
        pyperclip.copy(output)
        
        # Показываем небольшой фрагмент для подтверждения
        preview = output[:100] + ('...' if len(output) > 100 else '')
        messagebox.showinfo("Скопировано", f"Баллы скопированы в буфер обмена.\n\n{preview}")
    def save_to_excel(self, recognized_answers, score):
        """
        Сохраняет результаты в Excel-файл.
        recognized_answers[0] — номер варианта.
        score — список из 27 пар [баллы, правильно].
        """
        if not self.current_path:
            messagebox.showerror("Ошибка", "Не выбрана рабочая папка.")
            return False

        import re

        # 1. Находим Excel-файл в рабочей папке
        excel_path = find_excel_file(self.current_path)
        if not excel_path:
            answer = messagebox.askyesno("Файл Excel не найден",
                                        "В рабочей папке нет файла .xlsx.\nХотите выбрать его вручную?")
            if answer:
                excel_path = filedialog.askopenfilename(
                    title="Выберите файл Excel с таблицей результатов",
                    filetypes=[("Excel files", "*.xlsx")]
                )
                if not excel_path:
                    return False
            else:
                return False

        # 2. Открываем книгу
        try:
            wb = open_workbook(excel_path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть Excel-файл:\n{e}")
            return False

        # 3. Определяем номер варианта из бланка
        variant_str = ''.join(recognized_answers[0]).strip()
        variant_match = re.search(r'\d+', variant_str)
        detected_variant = int(variant_match.group()) if variant_match else None
        
        # 4. Выбираем лист (вариант)
        all_sheets = get_all_sheets(wb)
        
        # Сначала пробуем найти автоматически
        sheet = None
        if detected_variant:
            sheet = find_variant_sheet(wb, detected_variant)
        
        if sheet:
            # Спрашиваем подтверждение
            answer = messagebox.askyesno(
                "Лист найден",
                f"Обнаружен вариант {detected_variant}\n"
                f"Будут использованы данные с листа: '{sheet.title}'\n\n"
                "Продолжить с этим листом?"
            )
            if not answer:
                sheet = None
        
        if not sheet:
            # Показываем диалог выбора листа
            sheet_win = tk.Toplevel(self.root)
            sheet_win.title("Выбор варианта")
            sheet_win.geometry("400x300")
            sheet_win.transient(self.root)
            sheet_win.grab_set()
            
            tk.Label(sheet_win, text="Выберите лист с результатами:", font=("Arial", 12)).pack(pady=10)
            
            frame = ttk.Frame(sheet_win)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=listbox.yview)
            
            for sheet_name in all_sheets:
                listbox.insert(tk.END, sheet_name)
            
            selected_sheet = None
            
            def on_sheet_select():
                nonlocal selected_sheet
                selection = listbox.curselection()
                if selection:
                    selected_sheet = listbox.get(selection[0])
                    sheet_win.destroy()
                else:
                    messagebox.showwarning("Выбор", "Пожалуйста, выберите лист.")
            
            ttk.Button(sheet_win, text="Выбрать", command=on_sheet_select).pack(pady=10)
            ttk.Button(sheet_win, text="Отмена", command=sheet_win.destroy).pack(pady=5)
            
            self.root.wait_window(sheet_win)
            
            if not selected_sheet:
                wb.close()
                return False
            
            sheet = get_sheet_by_name(wb, selected_sheet)
            if not sheet:
                messagebox.showerror("Ошибка", f"Не удалось найти лист '{selected_sheet}'")
                wb.close()
                return False

        # 5. Получаем список учеников
        students = get_all_students(sheet)
        if not students:
            messagebox.showerror("Ошибка", "На листе нет учеников (столбец A).")
            wb.close()
            return False

        # 6. Диалог выбора ученика
        student_win = tk.Toplevel(self.root)
        student_win.title("Выберите ученика")
        student_win.geometry("400x400")
        student_win.transient(self.root)
        student_win.grab_set()

        tk.Label(student_win, text="Выберите ученика из списка:", font=("Arial", 12)).pack(pady=10)

        # Поле поиска
        search_frame = ttk.Frame(student_win)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        frame = ttk.Frame(student_win)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Заполняем список
        for student in students:
            listbox.insert(tk.END, student)
        
        # Функция поиска
        def filter_students(event=None):
            search_text = search_entry.get().strip().lower()
            listbox.delete(0, tk.END)
            for student in students:
                if search_text in student.lower():
                    listbox.insert(tk.END, student)
        
        search_entry.bind('<KeyRelease>', filter_students)

        selected_student = None

        def on_select():
            nonlocal selected_student
            selection = listbox.curselection()
            if selection:
                selected_student = listbox.get(selection[0])
                student_win.destroy()
            else:
                messagebox.showwarning("Выбор", "Пожалуйста, выберите ученика.")
        
        def on_double_click(event):
            on_select()

        listbox.bind('<Double-Button-1>', on_double_click)

        ttk.Button(student_win, text="Выбрать", command=on_select).pack(pady=10)
        ttk.Button(student_win, text="Отмена", command=student_win.destroy).pack(pady=5)

        self.root.wait_window(student_win)

        if not selected_student:
            wb.close()
            return False

        # 7. Находим строку ученика
        row_idx = find_student_row(sheet, selected_student)
        if not row_idx:
            # Если не нашли, предлагаем добавить вручную
            answer = messagebox.askyesno(
                "Ученик не найден",
                f"Ученик '{selected_student}' не найден в списке.\n\n"
                "Хотите добавить его в конец списка?"
            )
            if answer:
                row_idx = sheet.max_row + 1
                sheet.cell(row=row_idx, column=1, value=selected_student)
                messagebox.showinfo("Добавлен", f"Ученик '{selected_student}' добавлен в строку {row_idx}")
            else:
                wb.close()
                return False

        # 8. Формируем список баллов (27 штук)
        points_list = [p for p, _ in score]

        # 9. Записываем баллы
        write_scores_to_sheet(sheet, row_idx, points_list)

        # 10. Сохраняем
        try:
            save_workbook(wb, excel_path)
            messagebox.showinfo("Успех", 
                f"Результаты сохранены в файл:\n{excel_path}\n"
                f"Лист: {sheet.title}\n"
                f"Ученик: {selected_student}\n"
                f"Вариант: {detected_variant if detected_variant else '?'}\n"
                f"Сумма баллов: {sum(points_list)}")
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")
            return False
        finally:
            wb.close()