# Модуль валидации исследовательских отчетов

Простой модуль для валидации исследовательских отчетов через анализ PDF статей с помощью Gemini API.

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Настройка

1. Получите API ключ Gemini: https://makersuite.google.com/app/apikey
2. Установите переменную окружения:
```bash
export GOOGLE_API_KEY=your_gemini_api_key_here
```

## Структура папок

```
validation_pipe/
├── data/dataset2/
│   ├── input/                    # Папка с hierarchical_research_report.json и PDF
│   ├── topredict/               # Папка с PDF файлами для валидации
│   └── temp/                    # Временная папка для скачивания
├── results/                     # Результаты валидации
├── validation.py               # Основной код валидации
├── downlaod_init_data.py       # Скачивание данных из Google Drive
├── full_workflow.py            # Полный автоматический процесс
├── run_validation.py           # Удобный запуск валидации
├── test_validation.py          # Тестовый скрипт
├── download_config.json        # Конфигурация скачивания
├── requirements.txt            # Зависимости
└── README.md                   # Инструкция
```

## Использование

### 🚀 Полный автоматический workflow (рекомендуется)

Один скрипт для скачивания данных и валидации:
```bash
python full_workflow.py
```

### 📦 Поэтапное выполнение

#### Этап 1: Скачивание данных
```bash
python downlaod_init_data.py
```

#### Этап 2: Валидация
```bash
python run_validation.py
```

### 🔧 Ручное размещение файлов

1. Поместите `hierarchical_research_report.json` в папку `data/dataset2/input/`
2. Поместите PDF файлы для валидации в папку `data/dataset2/topredict/`
3. Запустите валидацию:

```bash
python validation.py
```

### ⚙️ Настройка источника данных

Отредактируйте `download_config.json` для изменения источника:
```json
{
  "google_drive_folder_url": "ваша_ссылка_на_папку",
  "input_pdf_count": 20,
  "predict_pdf_count": 1
}
```

По умолчанию используется папка: https://drive.google.com/drive/folders/1OAECK_1YX0NCqcTLMewNZRgoPKCKYfgt

### 🧪 Тестирование системы

Проверьте готовность системы перед использованием:
```bash
python quick_test.py
```

Этот скрипт проверит:
- Наличие API ключа Gemini
- Установку всех зависимостей  
- Структуру файлов проекта
- Корректность конфигурации
- Подключение к Gemini API

## Что делает валидатор

1. **Загружает** исследовательский отчет из `input/hierarchical_research_report.json`
2. **Находит** все PDF файлы в папке `topredict/`
3. **Извлекает** содержимое каждого PDF через Gemini API
4. **Сравнивает** содержимое PDF с направлениями из отчета
5. **Сохраняет** результаты валидации в папку `results/`

## Результат валидации

Для каждого PDF создается JSON файл с результатами:

```json
{
  "timestamp": "2025-01-24T10:00:00.000000",
  "pdf_file": "example.pdf",
  "validation_status": "matches|no_match|partial_match|error",
  "confidence_score": 0.8,
  "summary": "Подробный анализ на русском языке...",
  "matches_found": [],
  "discrepancies": [],
  "recommendations": []
}
```

## Возможные статусы

- `matches` - Статья соответствует направлениям из отчета
- `no_match` - Статья не соответствует направлениям  
- `partial_match` - Частичное соответствие
- `error` - Ошибка при валидации 