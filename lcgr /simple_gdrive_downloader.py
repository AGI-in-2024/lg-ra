# -*- coding: utf-8 -*-
"""
Простой скрипт для скачивания PDF из публичной Google Drive папки
Без необходимости в credentials.json
"""

import os
import re
import requests
from pathlib import Path
from tqdm import tqdm
from urllib.parse import unquote


# Настройки
GOOGLE_DRIVE_FOLDER_ID = "1OAECK_1YX0NCqcTLMewNZRgoPKCKYfgt"
DOWNLOAD_FOLDER = "downloaded_pdfs"


def setup_download_folder():
    """Создает папку для скачанных файлов"""
    folder_path = Path(DOWNLOAD_FOLDER)
    folder_path.mkdir(exist_ok=True)
    print(f"✅ Папка для скачивания: {folder_path.absolute()}")
    return folder_path


def get_public_folder_files(folder_id):
    """Получает список файлов из публичной папки Google Drive"""
    print("🔍 Поиск файлов в публичной папке...")
    
    try:
        # URL для просмотра публичной папки
        url = f"https://drive.google.com/drive/folders/{folder_id}"
        
        # Получаем HTML страницу
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Ищем все файлы в HTML
        # Паттерн для поиска файлов с их ID и именами
        file_pattern = r'"([a-zA-Z0-9_-]{25,})".*?"([^"]*\.pdf)"'
        matches = re.findall(file_pattern, response.text, re.IGNORECASE)
        
        files = []
        seen_ids = set()
        
        for file_id, file_name in matches:
            # Убираем дубликаты по ID
            if file_id not in seen_ids and file_name.lower().endswith('.pdf'):
                files.append({
                    'id': file_id,
                    'name': file_name
                })
                seen_ids.add(file_id)
        
        print(f"📄 Найдено PDF файлов: {len(files)}")
        return files
        
    except Exception as e:
        print(f"❌ Ошибка при получении списка файлов: {e}")
        return []


def download_file_direct(file_id, file_name, download_folder):
    """Скачивает файл напрямую по ID"""
    try:
        # Прямая ссылка для скачивания
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        # Создаем безопасное имя файла
        safe_file_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        if not safe_file_name.lower().endswith('.pdf'):
            safe_file_name += '.pdf'
        
        file_path = download_folder / safe_file_name
        
        # Скачиваем файл
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(download_url, headers=headers, stream=True)
        
        # Проверяем, что это PDF файл
        content_type = response.headers.get('content-type', '')
        if 'application/pdf' not in content_type and 'html' in content_type:
            # Возможно, нужно подтверждение для больших файлов
            # Ищем ссылку подтверждения
            if 'confirm=' in response.text:
                confirm_pattern = r'confirm=([a-zA-Z0-9_-]+)'
                confirm_match = re.search(confirm_pattern, response.text)
                if confirm_match:
                    confirm_token = confirm_match.group(1)
                    download_url = f"https://drive.google.com/uc?export=download&confirm={confirm_token}&id={file_id}"
                    response = requests.get(download_url, headers=headers, stream=True)
        
        response.raise_for_status()
        
        # Сохраняем файл
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Проверяем размер файла
        if file_path.stat().st_size < 1000:  # Меньше 1KB - вероятно ошибка
            file_path.unlink()  # Удаляем плохой файл
            return False, None
        
        return True, str(file_path)
        
    except Exception as e:
        print(f"❌ Ошибка скачивания {file_name}: {e}")
        return False, None


def download_all_pdfs_simple():
    """Основная функция для скачивания всех PDF"""
    print("🚀 Запуск простого скачивания PDF из публичной Google Drive папки")
    print("=" * 60)
    
    # Создаем папку для скачивания
    download_folder = setup_download_folder()
    
    # Получаем список PDF файлов
    pdf_files = get_public_folder_files(GOOGLE_DRIVE_FOLDER_ID)
    if not pdf_files:
        print("📄 PDF файлы не найдены или папка недоступна")
        return
    
    # Скачиваем все файлы
    print(f"📥 Начинаем скачивание {len(pdf_files)} файлов...")
    
    successful_downloads = 0
    failed_downloads = []
    
    for file_info in tqdm(pdf_files, desc="Скачивание"):
        file_id = file_info['id']
        file_name = file_info['name']
        
        # Создаем безопасное имя файла для проверки
        safe_file_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        if not safe_file_name.lower().endswith('.pdf'):
            safe_file_name += '.pdf'
        
        # Проверяем, не скачан ли файл уже
        file_path = download_folder / safe_file_name
        if file_path.exists():
            print(f"⏭️  Файл уже существует: {safe_file_name}")
            successful_downloads += 1
            continue
        
        # Скачиваем файл
        success, saved_path = download_file_direct(file_id, file_name, download_folder)
        
        if success:
            successful_downloads += 1
            print(f"✅ Скачан: {safe_file_name}")
        else:
            failed_downloads.append(file_name)
    
    # Итоги
    print("=" * 60)
    print(f"✅ Успешно скачано: {successful_downloads} файлов")
    if failed_downloads:
        print(f"❌ Ошибки скачивания: {len(failed_downloads)} файлов")
        for failed_file in failed_downloads:
            print(f"   - {failed_file}")
    
    print(f"📁 Файлы сохранены в: {download_folder.absolute()}")


def main():
    """Главная функция"""
    try:
        download_all_pdfs_simple()
    except KeyboardInterrupt:
        print("\n⏹️  Скачивание прервано пользователем")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")


if __name__ == "__main__":
    main() 