# Инструкция по скачиванию PDF из Google Drive

## 1. Установка зависимостей

```bash
pip install -r gdrive_requirements.txt
```

## 2. Настройка Google Drive API

### Получение credentials.json:

1. Идите на https://console.cloud.google.com/
2. Создайте новый проект или выберите существующий
3. Включите Google Drive API:
   - API & Services → Library
   - Найдите "Google Drive API" и включите
4. Создайте OAuth 2.0 credentials:
   - API & Services → Credentials
   - Create Credentials → OAuth 2.0 Client IDs
   - Application type: Desktop application
   - Скачайте файл как `credentials.json`
5. Поместите `credentials.json` в папку `lcgr/`

## 3. Запуск

```bash
cd lcgr/
python gdrive_pdf_downloader.py
```

## Что происходит:

1. При первом запуске откроется браузер для авторизации
2. Разрешите доступ к Google Drive
3. Скрипт найдет все PDF файлы в указанной папке
4. Скачает их в папку `downloaded_pdfs/`
5. Покажет статистику скачивания

## Настройки в коде:

- `GOOGLE_DRIVE_FOLDER_ID` - ID папки Google Drive (уже настроен)
- `DOWNLOAD_FOLDER` - папка для сохранения файлов

## Важные замечания:

- Файлы с одинаковыми именами будут пропущены
- Прогресс показывается в консоли
- При ошибках скрипт продолжит работу с другими файлами 