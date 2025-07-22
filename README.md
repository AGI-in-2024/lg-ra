# Longevity Knowledge Graph 🧬

Система для сбора, структурирования и анализа научных знаний о долголетии и старении.

## 🏗️ Модульная архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Модуль 1:     │    │   Модуль 2:     │    │   Модуль 3:     │    │   Модуль 4:     │
│   Harvester     │───▶│   Extractor     │───▶│   Architect     │───▶│   AI Agent      │
│                 │    │                 │    │                 │    │                 │
│ Сбор данных     │    │ Извлечение      │    │ Построение      │    │ Интеллектуальный│
│ из источников   │    │ знаний          │    │ графа знаний    │    │ анализ графа    │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 Модули

### 🔍 Модуль 1: Harvester
*Планируется к разработке*

Автоматический сбор научных данных из:
- PubMed / PMC
- arXiv
- bioRxiv
- Institutional repositories

**Выход**: `harvested_data.jsonl`

### 🧠 Модуль 2: Extractor ✅
*Готов к использованию*

Извлечение структурированных знаний из документов:
- **Knowledge Extraction**: сущности + отношения
- **Document Classification**: область исследований + уровень зрелости  
- **PDF Analysis**: анализ PDF с vision capabilities
- **LLM Processing**: GPT-4/Gemini + structured output

**Вход**: `harvested_data.jsonl` или PDF файлы  
**Выход**: `extracted_data.jsonl`

### 🏗️ Модуль 3: Architect
*Планируется к разработке*

Построение графа знаний:
- Создание Neo4j базы данных
- Загрузка извлеченных знаний
- Создание связей и индексов
- API для доступа к графу

**Вход**: `extracted_data.jsonl`  
**Выход**: Neo4j Knowledge Graph

### 🤖 Модуль 4: AI Agent
*Планируется к разработке*

Интеллектуальный анализ:
- Запросы на естественном языке
- Поиск паттернов и insights
- Генерация гипотез
- Визуализация знаний

**Вход**: Neo4j Knowledge Graph  
**Выход**: Аналитические insights

## 🚀 Быстрый старт

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Настройка API ключей

```bash
export OPENAI_API_KEY=your_openai_key_here
# или
export GEMINI_API_KEY=your_gemini_key_here
```

### Использование Модуля 2 (Extractor)

```bash
cd modules/extractor

# Обработка JSONL файла
python extractor.py --input data.jsonl --output results.jsonl

# Анализ PDF
python pdf_reader.py --pdf paper.pdf --action extract

# Полный workflow с PDF
python workflow_example.py
```

## 📁 Структура проекта

```
lg-ra/
├── modules/                    # Основные модули
│   ├── harvester/             # Модуль 1: Сбор данных
│   ├── extractor/             # Модуль 2: Извлечение знаний ✅
│   │   ├── extractor.py           # LLM извлечение
│   │   ├── pdf_reader.py          # PDF анализ
│   │   ├── document_storage.py    # Хранение документов
│   │   ├── workflow_example.py    # Workflow примеры
│   │   ├── models.py              # Pydantic схемы
│   │   └── prompts/               # LLM промпты
│   ├── architect/             # Модуль 3: Граф знаний
│   └── ai_agent/              # Модуль 4: AI агент
├── shared/                    # Общие утилиты
├── config/                    # Конфигурация
├── web/                       # Web интерфейс
└── requirements.txt           # Зависимости
```

## 🔬 Возможности Модуля 2

### Knowledge Extraction
- **Entities**: Гены, белки, болезни, химические соединения
- **Relationships**: Каузальные связи, функциональные отношения
- **Classification**: Область исследований + уровень зрелости

### PDF Analysis  
- 📖 Чтение PDF до 1000 страниц
- 🖼️ Анализ изображений и диаграмм  
- 📊 Извлечение таблиц
- ☁️ File API для больших файлов

### Structured Output
- 🏗️ Pydantic + Instructor для гарантированной структуры
- 💾 Автоматическое кэширование результатов
- ⚡ Асинхронная пакетная обработка

## 🎯 Примеры использования

### Анализ научной статьи

```python
from modules.extractor.extractor import KnowledgeExtractor
from modules.extractor.models import InputDocument

# Создаем экстрактор
extractor = KnowledgeExtractor()

# Обрабатываем документ
document = InputDocument(
    source_id="pmid_12345",
    title="SIRT1 activation extends lifespan in mice",
    abstract="We show that SIRT1 activation by resveratrol..."
)

result = extractor.extract_knowledge(document)
print(f"Extracted {len(result.knowledge_graph.entities)} entities")
```

### PDF Workflow

```python
from modules.extractor.workflow_example import PDFProcessingPipeline

# Полный пайплайн
pipeline = PDFProcessingPipeline("./documents")

# Добавление PDF
pipeline.add_pdf_from_url(
    "https://example.com/longevity_paper.pdf",
    "longevity_001"
)

# Обработка
results = pipeline.process_all_documents()
pipeline.export_results("results.jsonl")
```

## 📊 Формат данных

### Входной формат (Harvester → Extractor)
```json
{
  "source_id": "pmid_12345",
  "source_url": "https://pubmed.ncbi.nlm.nih.gov/12345",
  "title": "Paper title",
  "abstract": "Paper abstract..."
}
```

### Выходной формат (Extractor → Architect)
```json
{
  "source_id": "pmid_12345",
  "source_url": "https://pubmed.ncbi.nlm.nih.gov/12345",
  "classification": {
    "research_area": "longevity_interventions",
    "maturity_level": "basic_research"
  },
  "knowledge_graph": {
    "entities": [
      {"name": "SIRT1", "type": "Gene/Protein"}
    ],
    "relationships": [
      {"subject": "resveratrol", "predicate": "активирует", "object": "SIRT1"}
    ]
  }
}
```

## 🔧 Конфигурация

### Переменные окружения

```bash
# LLM настройки
OPENAI_API_KEY=your_key
GEMINI_API_KEY=your_key  
LLM_MODEL_NAME=gpt-4-turbo-preview
LLM_BASE_URL=https://api.openai.com/v1

# Файлы
INPUT_FILENAME=harvested_data.jsonl
OUTPUT_FILENAME=extracted_data.jsonl

# Производительность
BATCH_SIZE=5
MAX_CONCURRENT=3
CACHE_ENABLED=true
```

## 🚧 Статус разработки

- ✅ **Модуль 2: Extractor** - Готов к использованию
- 🔄 **Модуль 1: Harvester** - В планах
- 🔄 **Модуль 3: Architect** - В планах  
- 🔄 **Модуль 4: AI Agent** - В планах

## 📚 Документация

- [Модуль 2: Extractor](modules/extractor/README.md) - Подробная документация
- [PDF Analysis Guide](modules/extractor/README.md#pdf-analysis) - Анализ PDF
- [Workflow Examples](modules/extractor/README.md#workflow-examples) - Примеры использования

## 🤝 Контрибуция

Модульная архитектура позволяет разрабатывать каждый компонент независимо. Добро пожаловать к участию в разработке!

---

*Проект создан для структурирования и анализа научных знаний о долголетии и механизмах старения.* 