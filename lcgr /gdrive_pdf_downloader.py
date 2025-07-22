# -*- coding: utf-8 -*-
"""
Скрипт для скачивания всех PDF файлов из Google Drive папки
"""

import os
import io
import json
from pathlib import Path
from tqdm import tqdm
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


# Настройки
GOOGLE_DRIVE_FOLDER_ID = "1OAECK_1YX0NCqcTLMewNZRgoPKCKYfgt"
DOWNLOAD_FOLDER = "downloaded_pdfs"
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def setup_download_folder():
    """Создает папку для скачанных файлов"""
    folder_path = Path(DOWNLOAD_FOLDER)
    folder_path.mkdir(exist_ok=True)
    print(f"✅ Папка для скачивания: {folder_path.absolute()}")
    return folder_path


def authenticate_google_drive():
    """Аутентификация в Google Drive API"""
    credentials = None
    token_file = "token.json"
    
    # Проверяем существующие токены
    if os.path.exists(token_file):
        credentials = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    # Если токены недействительны или отсутствуют - запрашиваем новые
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            # Вам понадобится credentials.json файл от Google Cloud Console
            if not os.path.exists('credentials.json'):
                print("❌ Файл credentials.json не найден!")
                print("🔧 Получите его на: https://console.cloud.google.com/")
                print("🔧 API & Services > Credentials > Create Credentials > OAuth 2.0")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        
        # Сохраняем токены для следующего запуска
        with open(token_file, 'w') as token:
            token.write(credentials.to_json())
    
    return credentials


def get_drive_service():
    """Создает сервис для работы с Google Drive"""
    credentials = authenticate_google_drive()
    if not credentials:
        return None
    
    service = build('drive', 'v3', credentials=credentials)
    print("✅ Подключение к Google Drive установлено")
    return service


def get_pdf_files_from_folder(service, folder_id):
    """Получает список всех PDF файлов из папки"""
    print(f"🔍 Поиск PDF файлов в папке...")
    
    try:
        # Запрос всех файлов в папке
        query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(
            q=query,
            fields="files(id, name, size)"
        ).execute()
        
        files = results.get('files', [])
        print(f"📄 Найдено PDF файлов: {len(files)}")
        
        return files
    
    except Exception as e:
        print(f"❌ Ошибка при получении списка файлов: {e}")
        return []


def download_file(service, file_id, file_name, download_folder):
    """Скачивает один файл"""
    try:
        # Создаем запрос на скачивание
        request = service.files().get_media(fileId=file_id)
        
        # Создаем путь для сохранения
        file_path = download_folder / file_name
        
        # Скачиваем файл
        with open(file_path, 'wb') as file_handle:
            downloader = MediaIoBaseDownload(file_handle, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
        
        return True, str(file_path)
    
    except Exception as e:
        print(f"❌ Ошибка скачивания {file_name}: {e}")
        return False, None


def download_all_pdfs():
    """Основная функция для скачивания всех PDF"""
    print("🚀 Запуск скачивания PDF файлов из Google Drive")
    print("=" * 50)
    
    # Создаем папку для скачивания
    download_folder = setup_download_folder()
    
    # Подключаемся к Google Drive
    service = get_drive_service()
    if not service:
        print("❌ Не удалось подключиться к Google Drive")
        return
    
    # Получаем список PDF файлов
    pdf_files = get_pdf_files_from_folder(service, GOOGLE_DRIVE_FOLDER_ID)
    if not pdf_files:
        print("📄 PDF файлы не найдены")
        return
    
    # Скачиваем все файлы
    print(f"📥 Начинаем скачивание {len(pdf_files)} файлов...")
    
    successful_downloads = 0
    failed_downloads = []
    
    for file_info in tqdm(pdf_files, desc="Скачивание"):
        file_id = file_info['id']
        file_name = file_info['name']
        
        # Проверяем, не скачан ли файл уже
        file_path = download_folder / file_name
        if file_path.exists():
            print(f"⏭️  Файл уже существует: {file_name}")
            successful_downloads += 1
            continue
        
        # Скачиваем файл
        success, saved_path = download_file(service, file_id, file_name, download_folder)
        
        if success:
            successful_downloads += 1
            print(f"✅ Скачан: {file_name}")
        else:
            failed_downloads.append(file_name)
    
    # Итоги
    print("=" * 50)
    print(f"✅ Успешно скачано: {successful_downloads} файлов")
    if failed_downloads:
        print(f"❌ Ошибки скачивания: {len(failed_downloads)} файлов")
        for failed_file in failed_downloads:
            print(f"   - {failed_file}")
    
    print(f"📁 Файлы сохранены в: {download_folder.absolute()}")


def main():
    """Главная функция"""
    try:
        download_all_pdfs()
    except KeyboardInterrupt:
        print("\n⏹️  Скачивание прервано пользователем")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")


if __name__ == "__main__":
    main() 