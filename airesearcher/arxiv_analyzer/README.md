# ArXiv Analyzer

Модуль для автоматического анализа научных статей из arXiv по чеклисту критериев из `initialtask.md`.

## Возможности

- 🔍 **Генерация поисковых запросов** на основе описания задачи
- 📚 **Поиск статей** в arXiv API с разными стратегиями
- 🧠 **Анализ статей** по 5 категориям с 15+ критериями
- 📊 **Ранжирование** статей по релевантности к задаче
- 💾 **Сохранение результатов** в JSON формате

## Архитектура

```
ArxivAnalyzer
├── QueryGenerator     # Генерация поисковых запросов
├── ArxivClient        # Поиск статей в arXiv
├── PaperAnalyzer      # Анализ по чеклисту
└── PriorityRanker     # Ранжирование результатов
```

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте переменную окружения с API ключом Gemini:
```bash
export GEMINI_API_KEY="your_gemini_api_key"
```

## Быстрый старт

```python
import asyncio
from backend.modules.arxiv_analyzer.main import ArxivAnalyzer

async def main():
    analyzer = ArxivAnalyzer()
    
    # Запуск полного анализа
    results = await analyzer.run_full_analysis(
        max_papers_per_query=10,    # Статей на запрос
        max_total_papers=50,        # Максимум статей всего
        use_llm_ranking=True        # Использовать LLM для ранжирования
    )
    
    # Показ результатов
    analyzer.print_summary(results)
    
    # Сохранение в файл
    await analyzer.save_results(results)

if __name__ == "__main__":
    asyncio.run(main())
```

## Модули

### 1. QueryGenerator

Генерирует поисковые запросы для arXiv на основе описания задачи:

```python
from backend.modules.arxiv_analyzer.query_generator import QueryGenerator

generator = QueryGenerator()
queries = await generator.generate_queries(max_results_per_query=10)
```

**Стратегии поиска:**
- `Broad Overview` - широкий обзор области
- `Focused Search` - фокусный поиск по ключевым концепциям
- `Architecture/Methodology Search` - технические подходы
- `Benchmark/Dataset Search` - бенчмарки и датасеты
- `Review Search` - обзорные статьи

### 2. ArxivClient

Выполняет поиск статей в arXiv API:

```python
from backend.modules.arxiv_analyzer.arxiv_client import ArxivClient

async with ArxivClient() as client:
    papers = await client.search_papers(query)
    # или для множественных запросов
    results = await client.search_multiple_queries(queries)
```

### 3. PaperAnalyzer

Анализирует статьи по 5 категориям чеклиста:

```python
from backend.modules.arxiv_analyzer.paper_analyzer import PaperAnalyzer

analyzer = PaperAnalyzer()
analysis = await analyzer.analyze_paper(paper_info)
```

**Категории анализа:**
1. **Приоритизация и Генерация Идей** (25%)
   - Алгоритм поиска направлений
   - Обоснование релевантности
   - Выявление пробелов в знаниях
   - Баланс популярности/новизны

2. **Оценка и Валидация** (20%)
   - Качество бенчмарков
   - Конкретные метрики
   - Методология оценки
   - Привлечение экспертов

3. **Архитектура и Взаимодействие Агентов** (25%)
   - Роли и процедуры
   - Коммуникация агентов
   - Память и контекст
   - Механизмы самокоррекции

4. **Работа со Знаниями** (15%)
   - Извлечение знаний
   - Представление знаний
   - Разрешение конфликтов

5. **Практическая Реализация** (15%)
   - Инструменты и фреймворки
   - Открытость кода
   - Воспроизводимость

### 4. PriorityRanker

Ранжирует статьи по приоритетности:

```python
from backend.modules.arxiv_analyzer.priority_ranker import PriorityRanker

ranker = PriorityRanker()
# Простое ранжирование
ranked_papers = ranker.rank_papers_simple(analyses)
# Или с LLM анализом
ranked_papers = await ranker.rank_papers_with_llm(analyses)
```

## Конфигурация

Настройки в `config.py`:

```python
# API настройки
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

# Параметры анализа
ANALYSIS_TEMPERATURE = 0.1
DEFAULT_MAX_RESULTS = 10

# Веса категорий для ранжирования
CATEGORY_WEIGHTS = {
    "prioritization": 0.25,
    "validation": 0.2,
    "architecture": 0.25,
    "knowledge": 0.15,
    "implementation": 0.15
}
```

## Результаты

Модуль возвращает структурированные результаты:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "duration_seconds": 45.2,
  "statistics": {
    "queries_generated": 5,
    "papers_found": 47,
    "papers_analyzed": 30,
    "valid_analyses": 28
  },
  "top_papers": [
    {
      "rank": 1,
      "score": 0.854,
      "title": "Multi-Agent Framework for Autonomous Research",
      "arxiv_id": "2024.0001",
      "key_insights": ["Novel priority detection", "Hybrid architecture"],
      "relevance": "High relevance for autonomous research systems...",
      "pdf_url": "https://arxiv.org/pdf/2024.0001.pdf"
    }
  ]
}
```

## Примеры использования

### Анализ с ограниченными ресурсами

```python
# Быстрый анализ (меньше API вызовов)
results = await analyzer.run_full_analysis(
    max_papers_per_query=5,
    max_total_papers=15,
    use_llm_ranking=False
)
```

### Глубокий анализ

```python
# Полный анализ с LLM ранжированием
results = await analyzer.run_full_analysis(
    max_papers_per_query=15,
    max_total_papers=100,
    use_llm_ranking=True
)
```

### Анализ отдельных модулей

```python
# Только генерация запросов
generator = QueryGenerator()
queries = await generator.generate_queries()

# Только поиск статей
async with ArxivClient() as client:
    papers = await client.search_papers(queries[0])

# Только анализ статьи
analyzer = PaperAnalyzer()
analysis = await analyzer.analyze_paper(papers[0])
```

## Требования

- Python 3.8+
- Gemini API ключ
- Интернет-соединение для arXiv API

## Лицензия

MIT License 