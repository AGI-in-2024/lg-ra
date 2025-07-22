"""
Генератор поисковых запросов для arXiv на основе описания задачи
"""

import asyncio
from typing import List
from openai import OpenAI

try:
    from .models import ArxivQuery, SearchStrategy, QueryGeneration
    from .config import (
        GEMINI_API_KEY, 
        GEMINI_BASE_URL, 
        GEMINI_MODEL,
        TASK_DESCRIPTION_PATH,
        ANALYSIS_TEMPERATURE
    )
except ImportError:
    from models import ArxivQuery, SearchStrategy, QueryGeneration
    from config import (
        GEMINI_API_KEY, 
        GEMINI_BASE_URL, 
        GEMINI_MODEL,
        TASK_DESCRIPTION_PATH,
        ANALYSIS_TEMPERATURE
    )


class QueryGenerator:
    """Генератор поисковых запросов для arXiv"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=GEMINI_API_KEY,
            base_url=GEMINI_BASE_URL
        )
    
    def load_task_description(self) -> str:
        """Загружает описание задачи из файла"""
        try:
            with open(TASK_DESCRIPTION_PATH, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл с описанием задачи не найден: {TASK_DESCRIPTION_PATH}")
    
    def create_query_prompt(self, task_description: str) -> str:
        """Создает промпт для генерации поисковых запросов"""
        return f"""# РОЛЬ
Ты — ведущий AI-исследователь и эксперт по научной литературе. Твоя специализация — state-of-the-art архитектуры и методы обучения LLM. Ты мастерски превращаешь абстрактные исследовательские идеи в точные поисковые запросы для arXiv.

# ЗАДАЧА
Твоя задача — взять на вход описание приоритетного направления в области ИИ и сгенерировать набор из 5-7 профессиональных поисковых запросов для arXiv. Запросы должны быть составлены так, чтобы найти самые релевантные, фундаментальные и прорывные статьи по теме.

# ВХОДНЫЕ ДАННЫЕ
## Описание Приоритетного Направления:
{task_description}

# ИНСТРУКЦИИ
1. **Проанализируй** описание задачи. Выдели ключевые концепции (например, "knowledge distillation", "reasoning"), архитектуры ("SLM", "Transformer"), и цели ("improve performance", "reduce hallucinations").
2. **Используй синонимы** и принятую в сообществе терминологию (например, "reasoning abilities", "chain-of-thought", "step-by-step reasoning").
3. **Применяй синтаксис arXiv:** используй `AND`, `OR`, `NOT` и префиксы `ti:`, `abs:`, `au:`, `all:`.
4. **Создай диверсифицированный портфель запросов:**
   * **Широкий запрос (Broad Overview):** Для общего понимания ландшафта.
   * **Фокусный запрос (Focused Search):** Нацеленный на точное пересечение ключевых идей.
   * **Архитектурный/Методологический запрос (Architecture/Methodology Search):** Для поиска статей, описывающих конкретные технические подходы.
   * **Запрос на бенчмарки и датасеты (Benchmark/Dataset Search):** Для поиска статей, вводящих новые способы оценки или наборы данных.
   * **Обзорный запрос (Review Search):** Для поиска обзорных статей и survey.
5. **Формат вывода:** Твой ответ будет автоматически структурирован как объект с полем queries, содержащим массив запросов.

# ПРИМЕР ЗАПРОСОВ:
- **Broad Overview**: широкий обзор области  
- **Focused Search**: точное пересечение ключевых концепций
- **Architecture/Methodology Search**: технические подходы и архитектуры
- **Benchmark/Dataset Search**: бенчмарки и методы оценки
- **Review Search**: обзорные статьи и survey
"""

    async def generate_queries(self, max_results_per_query: int = 10) -> List[ArxivQuery]:
        """Генерирует поисковые запросы на основе описания задачи"""
        
        # Загружаем описание задачи
        task_description = self.load_task_description()
        
        # Создаем промпт
        prompt = self.create_query_prompt(task_description)
        
        try:
            # Получаем ответ от модели с использованием structured output
            response = self.client.beta.chat.completions.parse(
                model=GEMINI_MODEL,
                temperature=ANALYSIS_TEMPERATURE,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format=QueryGeneration
            )
            
            # Получаем структурированный ответ
            query_generation = response.choices[0].message.parsed
            
            # Устанавливаем max_results для каждого запроса
            for query in query_generation.queries:
                query.max_results = max_results_per_query
            
            return query_generation.queries
            
        except Exception as e:
            raise RuntimeError(f"Ошибка генерации запросов: {e}")
    
    def validate_query(self, query: str) -> bool:
        """Валидирует синтаксис arXiv запроса"""
        # Простая валидация основных элементов arXiv синтаксиса
        valid_prefixes = ['ti:', 'abs:', 'au:', 'all:', 'cat:']
        valid_operators = ['AND', 'OR', 'NOT']
        
        # Проверяем наличие базовых элементов
        has_content = len(query.strip()) > 0
        
        # Проверяем отсутствие потенциально проблематичных символов
        forbidden_chars = ['<', '>', '&', ';']
        has_forbidden = any(char in query for char in forbidden_chars)
        
        return has_content and not has_forbidden


async def main():
    """Тестовая функция для проверки генератора запросов"""
    generator = QueryGenerator()
    
    try:
        queries = await generator.generate_queries(max_results_per_query=5)
        
        print("Сгенерированные запросы:")
        for i, query in enumerate(queries, 1):
            print(f"{i}. {query.strategy}: {query.query}")
            
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 