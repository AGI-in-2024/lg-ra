#!/usr/bin/env python3

import os
import sys

# Добавляем путь к utils папке
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from google_drive_uploader import GoogleDriveUploader

def main():
    """Загрузка файлов из downloaded_pdfs на Google Drive"""
    
    # Настройки (прописываются в коде)
    local_folder = "downloaded_pdfs/references_dlya_statiy_2025"  # Локальная папка с файлами
    drive_folder_name = "Научные_статьи_longevity_2025"  # Название папки на Google Drive
    
    print("=== Загрузка файлов на Google Drive ===")
    print()
    
    # Получаем путь к папке (можно передать через аргумент командной строки)
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = local_folder
    
    # Проверяем существование папки
    if not os.path.exists(folder_path):
        print(f"Ошибка: папка '{folder_path}' не найдена!")
        return False
    
    # Подсчитываем файлы
    files_count = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
    print(f"Локальная папка: {folder_path}")
    print(f"Папка на Google Drive: {drive_folder_name}")
    print(f"Найдено файлов для загрузки: {files_count}")
    
    if files_count == 0:
        print("Нет файлов для загрузки")
        return True
    
    print()
    print("Начинаем загрузку...")
    
    # Создаем загрузчик и загружаем файлы
    uploader = GoogleDriveUploader()
    
    if not uploader.authenticate():
        print("Ошибка аутентификации. Убедитесь что переменная GOOGLE_APPLICATION_CREDENTIALS установлена")
        return False
    
    # Используем заданное название папки на Google Drive
    success = uploader.upload_folder(folder_path, drive_folder_name)
    
    if success:
        print()
        print("✅ Все файлы успешно загружены на Google Drive!")
    else:
        print()
        print("⚠️ Загрузка завершена с ошибками")
    
    return success

if __name__ == "__main__":
    main() 