# Модуль 2 - Extractor v2.0 🔬

Агент деконструкции научного знания для проекта Longevity Knowledge Graph.

## Описание

Этот модуль извлекает структурированную научную нарративу из исследовательских документов, используя **Gemini модели** через OpenAI compatibility API и structured output. Модуль способен анализировать как текстовые документы, так и PDF файлы с поддержкой vision capabilities.

### Ключевые возможности

- 🧠 **Семантический анализ** научных текстов с выделением компонентов научного процесса
- 📄 **Поддержка PDF** с анализом текста, изображений, диаграмм и таблиц (до 1000 страниц)
- 🏗️ **Structured Output** - гарантированная структура данных через Pydantic
- 🔗 **Knowledge Triples** - извлечение связей в формате субъект-предикат-объект
- ⚡ **Batch Processing** - пакетная обработка документов из JSONL файлов

## Установка

1. Клонируйте репозиторий и перейдите в папку backend:
```bash
cd backend
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Получите API ключ Gemini:
   - Перейдите на [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Создайте новый API ключ
   - Установите переменную окружения:
```bash
export GEMINI_API_KEY=your_api_key_here
```

## Структура данных

### Типы научных утверждений

Модуль классифицирует текст на следующие типы:

1. **Hypothesis** - Гипотезы, которые авторы собираются проверить
2. **Method** - Описание использованных техник и протоколов
3. **Result** - Объективное изложение полученных данных
4. **Conclusion** - Интерпретация результатов и выводы
5. **Dataset** - Упоминание использованных наборов данных
6. **Comment** - Фоновые утверждения и контекст

### Формат вывода

```json
{
  "source_id": "unique_document_id",
  "source_url": "https://example.com/paper.pdf",
  "scientific_narrative": [
    {
      "statement_type": "Hypothesis",
      "statement_content": "We hypothesized that caloric restriction works through mTOR inhibition",
      "knowledge_triples": [
        {
          "subject": "caloric restriction",
          "predicate": "inhibits",
          "object": "mTOR pathway"
        }
      ]
    }
  ]
}
```

## Использование

### Быстрый тест

```bash
python test_extractor.py
```

### Обработка одного документа

```python
from extractor import ScientificNarrativeExtractor

extractor = ScientificNarrativeExtractor()

result = extractor.process_single_document(
    title="Your paper title",
    abstract="Your paper abstract",
    source_id="paper_001"
)

print(f"Извлечено утверждений: {len(result.scientific_narrative)}")
```

### Пакетная обработка JSONL

```bash
python extractor.py --input documents.jsonl --output extracted_narrative.jsonl
```

### Анализ PDF документов

```python
from pdf_reader import PDFReader

reader = PDFReader()

# Из URL
result = reader.extract_scientific_narrative_from_pdf_url(
    "https://example.com/paper.pdf"
)

# Из локального файла
result = reader.extract_scientific_narrative_from_pdf_file(
    "local_paper.pdf"
)

# Краткое резюме
summary = reader.summarize_pdf("paper.pdf", is_url=False)
print(summary)
```

### CLI для PDF

```bash
# Извлечение текста
python pdf_reader.py --pdf paper.pdf --action read

# Создание резюме
python pdf_reader.py --pdf paper.pdf --action summarize

# Извлечение научной нарративы
python pdf_reader.py --pdf paper.pdf --action extract --output result.json

# Работа с URL
python pdf_reader.py --pdf https://example.com/paper.pdf --url --action extract
```

### Workflow примеры

```bash
# Запуск полного пайплайна
python workflow_example.py

# Демо с пакетной обработкой
python document_storage.py
```

## Примеры

### Демо с примерами

```bash
python example_usage.py
```

### Формат входных данных (JSONL)

```json
{"source_id": "pmid_12345", "title": "Paper title", "abstract": "Paper abstract", "source_url": "https://pubmed.ncbi.nlm.nih.gov/12345"}
```

## Конфигурация

Настройки можно изменить в `config.py`:

```python
class ExtractorConfig:
    DEFAULT_MODEL = "gemini-2.5-flash"  # Модель Gemini
    TEMPERATURE = 0.1                   # Температура генерации
    MAX_CONTENT_LENGTH = 2000           # Макс. длина текста для анализа
```

## Архитектура

```
backend/
├── models.py              # Pydantic модели данных
├── config.py              # Конфигурация
├── extractor.py           # Основной модуль экстрактора
├── pdf_reader.py          # Модуль чтения PDF
├── document_storage.py    # Система хранения документов
├── workflow_example.py    # Полные workflow пайплайны
├── test_extractor.py      # Тесты модуля
└── requirements.txt       # Зависимости
```

## Система хранения документов

### DocumentStorage - Управление PDF файлами

```python
from document_storage import DocumentStorage, DocumentProcessor

# Создание хранилища
storage = DocumentStorage({'local_storage_path': './documents'})
processor = DocumentProcessor(storage)

# Добавление документов
doc_ref = processor.add_pdf_for_processing(
    source="https://example.com/paper.pdf",
    source_id="paper_001",
    is_url=True,
    metadata={'topic': 'longevity', 'year': 2024}
)

# Обработка документа
result = processor.process_document_with_extractor("paper_001")
```

### Стратегии хранения

1. **LOCAL** - Локальные файлы с кешированием
2. **URL** - Ссылки на внешние документы  
3. **S3** - Облачные хранилища (планируется)
4. **DATABASE** - База данных (планируется)

### Полный Workflow Pipeline

```python
from workflow_example import PDFProcessingPipeline

# Создание пайплайна
pipeline = PDFProcessingPipeline("./pdf_storage")

# Добавление документов
pipeline.add_pdf_from_url(
    "https://example.com/research.pdf", 
    "research_001",
    metadata={'topic': 'mTOR'}
)

# Пакетная обработка
results = pipeline.process_all_documents()

# Экспорт результатов
pipeline.export_results("results.jsonl")

# Статистика
stats = pipeline.get_pipeline_stats()
```

## Возможности PDF Reader

- 📖 **Чтение PDF до 1000 страниц**
- 🖼️ **Анализ изображений и диаграмм**
- 📊 **Извлечение таблиц**
- 🔄 **Сравнение множественных PDF**
- ☁️ **File API для больших файлов (>20MB)**
- 🌐 **Поддержка URL и локальных файлов**

## Технические детали

- **Модель**: Gemini 2.0/2.5 Flash
- **API**: OpenAI compatibility для structured output + нативный Gemini API для PDF
- **Лимиты**: до 1000 страниц PDF, каждая страница = 258 токенов
- **Разрешение**: автоматическое масштабирование до 3072x3072 пикселей

## Производительность

- Structured output обеспечивает консистентность данных
- Автоматическое определение размера файла для выбора API
- Прогресс-бары для пакетной обработки
- Обработка ошибок с продолжением работы

## Следующие шаги

После извлечения научной нарративы данные готовы для **Модуля 3** - загрузки в граф знаний Neo4j с созданием узлов для:
- Papers (статьи)
- Statements (утверждения)
- Entities (сущности)
- Relations (отношения)

## Источники PDF документов

### 📥 Как документы попадают в систему

1. **URL ссылки** - PubMed, arXiv, bioRxiv, institutional repositories
2. **Локальные файлы** - Загруженные исследователями PDF
3. **API интеграции** - Автоматический harvesting из баз данных
4. **Batch upload** - Массовая загрузка через конфигурационные файлы

### 🔄 Процесс обработки

```
PDF источник → DocumentStorage → PDF Reader → Extractor → Structured JSON → Knowledge Graph
```

### 📊 Интеграция с Harvester модулем

```python
# Результат от Harvester модуля (JSONL)
{"source_id": "pmid_12345", "title": "Paper title", "abstract": "...", "pdf_url": "https://..."}

# Передача в Extractor v2.0
pipeline = PDFProcessingPipeline()
pipeline.add_pdf_from_url(pdf_url, source_id, metadata)
result = pipeline.process_document(source_id)
```

## Поддержка

При возникновении проблем:
1. Проверьте API ключ: `echo $GEMINI_API_KEY`
2. Запустите тест: `python test_extractor.py`
3. Проверьте лимиты API Gemini
4. Для PDF проблем: проверьте доступность URL и размер файла

---

*Модуль создан для проекта Longevity Knowledge Graph - системы извлечения и структурирования научных знаний о долголетии.* 