import os
import sys
from typing import Optional, List

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Права доступа для Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveUploader:
    """Простая утилита для загрузки файлов на Google Drive"""
    
    def __init__(self):
        """
        Инициализация загрузчика
        
        Использует переменную окружения GOOGLE_APPLICATION_CREDENTIALS для аутентификации
        """
        self.service = None
        
    def authenticate(self):
        """Аутентификация в Google Drive API через Service Account"""
        try:
            # Проверяем переменную окружения
            credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            
            if not credentials_path:
                print("Ошибка: переменная окружения GOOGLE_APPLICATION_CREDENTIALS не установлена!")
                print("Установите её командой:")
                print("export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json")
                return False
                
            if not os.path.exists(credentials_path):
                print(f"Ошибка: файл с ключом Service Account не найден: {credentials_path}")
                return False
            
            # Загружаем учетные данные Service Account
            creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES)
            
            # Создаем сервис Google Drive
            self.service = build('drive', 'v3', credentials=creds)
            print("Успешно подключились к Google Drive!")
            return True
            
        except Exception as error:
            print(f"Ошибка при подключении к Google Drive: {error}")
            return False
    
    def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
        """
        Создает папку на Google Drive
        
        Args:
            folder_name: название папки
            parent_folder_id: ID родительской папки (если нужно создать внутри папки)
            
        Returns:
            ID созданной папки или None при ошибке
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
                
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            folder_id = folder.get('id')
            print(f"Создана папка '{folder_name}' с ID: {folder_id}")
            return folder_id
            
        except HttpError as error:
            print(f"Ошибка при создании папки: {error}")
            return None
    
    def upload_file(self, file_path: str, folder_id: Optional[str] = None) -> Optional[str]:
        """
        Загружает один файл на Google Drive
        
        Args:
            file_path: путь к файлу для загрузки
            folder_id: ID папки на Google Drive (если нужно загрузить в папку)
            
        Returns:
            ID загруженного файла или None при ошибке
        """
        try:
            file_name = os.path.basename(file_path)
            
            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]
                
            media = MediaFileUpload(file_path, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            print(f"Загружен файл '{file_name}' с ID: {file_id}")
            return file_id
            
        except HttpError as error:
            print(f"Ошибка при загрузке файла {file_path}: {error}")
            return None
        except Exception as error:
            print(f"Неожиданная ошибка при загрузке файла {file_path}: {error}")
            return None
    
    def upload_folder(self, local_folder_path: str, drive_folder_name: Optional[str] = None) -> bool:
        """
        Загружает все файлы из локальной папки на Google Drive
        
        Args:
            local_folder_path: путь к локальной папке
            drive_folder_name: название папки на Google Drive (по умолчанию как у локальной папки)
            
        Returns:
            True если загрузка успешна, False если были ошибки
        """
        if not os.path.exists(local_folder_path):
            print(f"Ошибка: папка {local_folder_path} не существует!")
            return False
            
        # Название папки на Google Drive
        if not drive_folder_name:
            drive_folder_name = os.path.basename(local_folder_path)
            
        # Создаем папку на Google Drive
        folder_id = self.create_folder(drive_folder_name)
        if not folder_id:
            return False
            
        # Получаем список файлов в папке
        files_to_upload = []
        for file_name in os.listdir(local_folder_path):
            file_path = os.path.join(local_folder_path, file_name)
            if os.path.isfile(file_path):
                files_to_upload.append(file_path)
                
        if not files_to_upload:
            print(f"В папке {local_folder_path} нет файлов для загрузки")
            return True
            
        print(f"Найдено {len(files_to_upload)} файлов для загрузки")
        
        # Загружаем файлы
        success_count = 0
        for file_path in files_to_upload:
            print(f"Загружаем {os.path.basename(file_path)}...")
            if self.upload_file(file_path, folder_id):
                success_count += 1
                
        print(f"Загружено {success_count} из {len(files_to_upload)} файлов")
        return success_count == len(files_to_upload)


def main():
    """Основная функция для запуска скрипта"""
    
    # Путь к папке по умолчанию
    default_folder = "../main_pipeline/downloaded_pdfs/references_dlya_statiy_2025"
    
    # Получаем путь к папке от пользователя
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = input(f"Введите путь к папке (по умолчанию: {default_folder}): ").strip()
        if not folder_path:
            folder_path = default_folder
    
    # Преобразуем относительный путь в абсолютный
    folder_path = os.path.abspath(folder_path)
    
    print(f"Загружаем файлы из папки: {folder_path}")
    
    # Создаем загрузчик
    uploader = GoogleDriveUploader()
    
    # Аутентифицируемся
    if not uploader.authenticate():
        print("Не удалось подключиться к Google Drive. Проверьте credentials.json")
        return
        
    # Загружаем папку
    success = uploader.upload_folder(folder_path)
    
    if success:
        print("Все файлы успешно загружены!")
    else:
        print("Загрузка завершена с ошибками")


if __name__ == "__main__":
    main() 