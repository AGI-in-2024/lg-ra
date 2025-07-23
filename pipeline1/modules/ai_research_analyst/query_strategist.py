"""
Query Strategist - генератор поисковых запросов для arXiv
"""

import json
import logging
from typing import List
from openai import OpenAI

from .config import (
    OPENAI_API_KEY, 
    OPENAI_BASE_URL,
    OPENAI_MODEL, 
    OPENAI_TEMPERATURE,
    QUERY_STRATEGIST_PROMPT,
    LLM_REQUEST_TIMEOUT
)


logger = logging.getLogger(__name__)


class QueryStrategist:
    """Класс для генерации стратегических поисковых запросов"""
    
    def __init__(self):
        # Инициализируем клиент с поддержкой Gemini API
        client_kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_BASE_URL:
            client_kwargs["base_url"] = OPENAI_BASE_URL
        
        self.client = OpenAI(**client_kwargs)
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self) -> str:
        """Загружает промпт из файла"""
        try:
            with open(QUERY_STRATEGIST_PROMPT, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Файл промпта не найден: {QUERY_STRATEGIST_PROMPT}")
            return ""
    
    def generate_queries(self, research_topic: str) -> List[str]:
        """
        Генерирует поисковые запросы для заданной темы исследования
        
        Args:
            research_topic: Тема исследования
            
        Returns:
            Список поисковых запросов
        """
        logger.info(f"Генерация запросов для темы: {research_topic}")
        
        try:
            prompt = self.prompt_template.format(research_topic=research_topic)
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=OPENAI_TEMPERATURE,
                timeout=LLM_REQUEST_TIMEOUT
            )
            
            content = response.choices[0].message.content
            
            # Извлекаем JSON из ответа
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            json_str = content[start_idx:end_idx]
            
            queries = json.loads(json_str)
            
            logger.info(f"Сгенерировано {len(queries)} запросов")
            return queries
            
        except Exception as e:
            logger.error(f"Ошибка при генерации запросов: {e}")
            # Возвращаем базовые запросы как fallback
            return self._get_fallback_queries(research_topic)
    
    def _get_fallback_queries(self, research_topic: str) -> List[str]:
        """Возвращает базовые запросы в случае ошибки"""
        logger.warning("Используются fallback запросы")
        return [
            research_topic,
            f"{research_topic} AND machine learning",
            f"{research_topic} AND artificial intelligence",
            f"automated {research_topic}",
            f"{research_topic} AND evaluation",
            f"{research_topic} AND methodology"
        ]
    
    def _extract_queries_from_response(self, content: str) -> List[str]:
        """
        Надежно извлекает список запросов из ответа LLM
        
        Args:
            content: Ответ от LLM
            
        Returns:
            Список поисковых запросов
        """
        try:
            # Попытка 1: Найти JSON блок в markdown
            if '```json' in content:
                start_idx = content.find('```json') + 7
                end_idx = content.find('```', start_idx)
                if end_idx != -1:
                    json_str = content[start_idx:end_idx].strip()
                    parsed_data = json.loads(json_str)
                    # Новый формат: массив объектов с полями strategy и query
                    if isinstance(parsed_data, list) and len(parsed_data) > 0 and isinstance(parsed_data[0], dict):
                        return [item.get('query', '') for item in parsed_data if 'query' in item]
                    # Старый формат: массив строк
                    elif isinstance(parsed_data, list):
                        return parsed_data
            
            # Попытка 2: Найти JSON массив
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                parsed_data = json.loads(json_str)
                # Новый формат: массив объектов с полями strategy и query
                if isinstance(parsed_data, list) and len(parsed_data) > 0 and isinstance(parsed_data[0], dict):
                    return [item.get('query', '') for item in parsed_data if 'query' in item]
                # Старый формат: массив строк
                elif isinstance(parsed_data, list):
                    return parsed_data
            
            # Попытка 3: Парсить весь ответ как JSON
            return json.loads(content.strip())
            
        except json.JSONDecodeError:
            # Попытка 4: Извлечь запросы построчно
            import re
            
            lines = content.split('\n')
            queries = []
            
            for line in lines:
                # Ищем строки с кавычками
                match = re.search(r'"([^"]+)"', line)
                if match:
                    query = match.group(1).strip()
                    if len(query) > 5 and not query.lower().startswith('query'):
                        queries.append(query)
                
                # Ищем строки со списками
                elif line.strip().startswith('-') or line.strip().startswith('*'):
                    query = line.strip().lstrip('-*').strip().strip('"')
                    if len(query) > 5:
                        queries.append(query)
            
            if queries:
                logger.warning(f"Использован fallback парсинг для извлечения {len(queries)} запросов")
                return queries[:12]  # Ограничиваем количество
            
            logger.error("Не удалось извлечь запросы из ответа")
            return []
        
        except Exception as e:
            logger.error(f"Ошибка при извлечении запросов: {e}")
            return [] 