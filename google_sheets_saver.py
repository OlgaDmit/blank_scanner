import os
import pickle
import re
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = 'credentials.json'   # должен лежать в папке программы
TOKEN_FILE = 'token.pickle'

def get_authenticated_service(parent=None):
    """Аутентификация и возврат сервиса Google Sheets."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                messagebox.showerror(
                    "Файл не найден",
                    f"Файл '{CREDENTIALS_FILE}' не найден.\n\n"
                    "Для работы с Google Sheets необходимо:\n"
                    "1. Перейти в Google Cloud Console\n"
                    "2. Создать проект и включить Google Sheets API\n"
                    "3. Создать OAuth 2.0 Client ID (тип Desktop application)\n"
                    "4. Скачать JSON и переименовать в 'credentials.json'\n"
                    "5. Поместить в папку программы",
                    parent=parent
                )
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    try:
        service = build('sheets', 'v4', credentials=creds)
        return service
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось создать сервис:\n{e}", parent=parent)
        return None

def get_spreadsheet_id_from_user(parent):
    """Диалог ввода URL или ID таблицы, возвращает ID."""
    dialog = tk.Toplevel(parent)
    dialog.title("Подключение к Google Sheets")
    dialog.geometry("500x150")
    dialog.transient(parent)
    dialog.grab_set()

    tk.Label(dialog, text="Введите URL или ID таблицы:", font=("Arial", 10)).pack(pady=10)
    entry = tk.Entry(dialog, width=60)
    entry.pack(pady=5, padx=20)
    entry.focus()

    result = [None]

    def on_ok():
        text = entry.get().strip()
        if not text:
            messagebox.showwarning("Ошибка", "Поле не может быть пустым")
            return
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', text)
        result[0] = match.group(1) if match else text
        dialog.destroy()

    def on_cancel():
        dialog.destroy()

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Отмена", command=on_cancel).pack(side=tk.LEFT, padx=5)

    parent.wait_window(dialog)
    return result[0]

def load_google_sheet_link(work_folder):
    """
    Ищет в рабочей папке файл google_sheet_link.txt или любой .txt,
    содержащий слово 'docs.google.com'. Возвращает (spreadsheet_id, file_used) или (None, None).
    """
    if not os.path.isdir(work_folder):
        return None, None
    # Приоритет: google_sheet_link.txt
    main_file = os.path.join(work_folder, "google_sheet_link.txt")
    if os.path.isfile(main_file):
        try:
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return content, main_file
        except:
            pass
    # Иначе любой .txt, содержащий docs.google.com
    for fname in os.listdir(work_folder):
        if fname.endswith('.txt'):
            path = os.path.join(work_folder, fname)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if 'docs.google.com/spreadsheets' in content:
                        return content, path
            except:
                continue
    return None, None

def save_google_sheet_link(work_folder, spreadsheet_id_or_url):
    """Сохраняет ссылку/ID в файл google_sheet_link.txt в рабочей папке."""
    path = os.path.join(work_folder, "google_sheet_link.txt")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(spreadsheet_id_or_url.strip())
    return path

def get_all_sheets(service, spreadsheet_id):
    """Возвращает список названий листов."""
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        return [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]
    except HttpError:
        return []

def get_all_students(service, spreadsheet_id, sheet_name):
    """Возвращает список учеников из столбца A (начиная с 3 строки)."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:A"
        ).execute()
        values = result.get('values', [])
        if len(values) < 3:
            return []
        students = []
        for row in values[2:]:
            if row and row[0].strip():
                val = row[0].strip()
                if not val.startswith('min:') and not val.startswith('max:') and val != '-':
                    students.append(val)
        return students
    except HttpError:
        return []

def find_student_row(service, spreadsheet_id, sheet_name, student_name):
    """Возвращает номер строки (1‑индексация) или None."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:A"
        ).execute()
        values = result.get('values', [])
        student_name_lower = student_name.strip().lower()
        for idx, row in enumerate(values, start=1):
            if row and row[0].strip().lower() == student_name_lower:
                return idx
        # частичное совпадение
        for idx, row in enumerate(values, start=1):
            if row and student_name_lower in row[0].strip().lower():
                return idx
        return None
    except HttpError:
        return None

def write_scores_to_sheet(service, spreadsheet_id, sheet_name, row_idx, scores):
    range_name = f"{sheet_name}!E{row_idx}:AE{row_idx}"
    values = [scores[:27]]
    body = {'values': values}
    try:
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        return True
    except HttpError as e:
        return False