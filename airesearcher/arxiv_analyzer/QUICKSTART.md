# Быстрый старт ArXiv Analyzer

## 1. Установка

```bash
# Переходим в директорию модуля
cd backend/modules/arxiv_analyzer

# Устанавливаем зависимости  
pip install -r requirements.txt

# Настраиваем API ключ Gemini
export GEMINI_API_KEY="your_gemini_api_key_here"
```

## 2. Быстрый тест

```bash
# Быстрая демонстрация (3 минуты)
python demo.py --quick

# Полная демонстрация (10-15 минут)
python demo.py
```

## 3. Программное использование

```python
import asyncio
from backend.modules.arxiv_analyzer.main import ArxivAnalyzer

async def quick_analysis():
    analyzer = ArxivAnalyzer()
    
    # Запуск анализа
    results = await analyzer.run_full_analysis(
        max_papers_per_query=5,  # Статей на запрос
        max_total_papers=20,     # Максимум статей
        use_llm_ranking=True     # LLM ранжирование
    )
    
    # Показ результатов
    analyzer.print_summary(results)
    
    # Получение топ статьи
    if results.get('top_papers'):
        top_paper = results['top_papers'][0]
        print(f"Лучшая статья: {top_paper['title']}")
        print(f"Оценка: {top_paper['score']}")

# Запуск
asyncio.run(quick_analysis())
```

## 4. Что происходит внутри

1. **Генерация запросов** 📝
   - Читает `docsforllm/initialtask.md`
   - Генерирует 5-7 поисковых запросов для arXiv
   
2. **Поиск статей** 🔍
   - Выполняет запросы к arXiv API
   - Убирает дубликаты
   
3. **Анализ статей** 🧠
   - Оценивает каждую статью по 15 критериям
   - Использует structured output с Pydantic
   
4. **Ранжирование** 📊
   - Взвешивает оценки по категориям
   - Опционально использует LLM для глубокого анализа

## 5. Результаты

Получаете JSON с:
- Топ-10 статей с оценками
- Детальный анализ по всем критериям  
- Обоснование ранжирования
- Ссылки на PDF статей

## 6. Частые проблемы

**Ошибка API ключа:**
```bash
export GEMINI_API_KEY="your_actual_key"
```

**Файл задачи не найден:**
Убедитесь что запускаете из корня проекта где есть `docsforllm/initialtask.md`

**Медленная работа:**
Используйте `--quick` флаг или уменьшите параметры:
```python
max_papers_per_query=3
max_total_papers=10
use_llm_ranking=False
```

## 7. Продвинутое использование

```python
# Анализ конкретных модулей
from backend.modules.arxiv_analyzer.query_generator import QueryGenerator
from backend.modules.arxiv_analyzer.paper_analyzer import PaperAnalyzer

# Генерация запросов
generator = QueryGenerator() 
queries = await generator.generate_queries()

# Анализ одной статьи
analyzer = PaperAnalyzer()
analysis = await analyzer.analyze_paper(paper_info)
```

Готово! 🎉 