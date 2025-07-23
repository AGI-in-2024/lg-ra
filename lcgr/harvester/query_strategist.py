import os
from typing import List
import instructor
from pydantic import BaseModel, Field

class QueryList(BaseModel):
    queries: List[str] = Field(..., description="Список поисковых запросов")

class QueryStrategist:
    def __init__(self):
        self.client = instructor.from_provider(
            "google/gemini-2.0-flash",
            mode=instructor.Mode.GENAI_TOOLS
        )
    
    def generate(self, topic: str) -> List[str]:
        prompt = f"""
        Создай 5-7 конкретных поисковых запросов для научной литературы по теме: {topic}
        
        Требования:
        - Используй ключевые слова и термины
        - Запросы должны покрывать разные аспекты темы
        - Подходят для поиска в PubMed и arXiv
        - Простые и понятные
        
        Тема: {topic}
        """
        
        try:
            result = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                response_model=QueryList
            )
            return result.queries
        except Exception as e:
            print(f"Ошибка генерации запросов: {e}")
            return [topic] 