#!/usr/bin/env python3
"""
Модуль 2: Extractor - Агент-Извлекатель Знаний
Извлекает структурированные знания из научных документов с помощью LLM
"""

import os
import json
import hashlib
import pathlib
from typing import List, Optional, Dict, Any
import asyncio
from openai import OpenAI
import instructor
from tqdm import tqdm
import jsonlines
from models import ExtractedDocument, InputDocument, RESEARCH_AREAS, ENTITY_TYPES
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.config import ExtractorConfig


class KnowledgeExtractor:
    """
    Основной класс для извлечения знаний из научных документов.
    
    Использует LLM для:
    1. Классификации документов по области и зрелости
    2. Извлечения сущностей и отношений
    """
    
    def __init__(self, config: Optional[ExtractorConfig] = None):
        """
        Инициализация экстрактора.
        
        Args:
            config: Конфигурация экстрактора
        """
        self.config = config or ExtractorConfig()
        
        # Проверяем API ключ
        if not self.config.llm_api_key:
            raise ValueError(
                "API ключ не найден. Установите OPENAI_API_KEY или GEMINI_API_KEY"
            )
        
        # Настраиваем LLM клиент
        if self.config.llm_base_url:
            openai_client = OpenAI(api_key=self.config.llm_api_key, base_url=self.config.llm_base_url)
        else:
            openai_client = OpenAI(api_key=self.config.llm_api_key)
        
        self.llm_client = instructor.from_openai(openai_client)
        
        # Загружаем промпт
        self.master_prompt = self._load_prompt()
        
        # Статистика
        self.stats = {
            "processed": 0,
            "cached": 0,
            "errors": 0,
            "total_entities": 0,
            "total_relationships": 0
        }
    
    def _load_prompt(self) -> str:
        """Загружает мастер-промпт из файла."""
        try:
            with open(self.config.prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback промпт если файл не найден
            return """
            Ты — эксперт-биоинформатик. Проанализируй научный текст и извлеки:
            1. Классификацию (research_area, maturity_level)
            2. Сущности и отношения для графа знаний
            
            Ответь только JSON в указанном формате.
            """
    
    def _generate_cache_key(self, document: InputDocument) -> str:
        """Генерирует ключ кэша для документа."""
        content = f"{document.title}||{document.abstract}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[ExtractedDocument]:
        """Получает результат из кэша."""
        if not self.config.cache_enabled:
            return None
        
        cache_file = self.config.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return ExtractedDocument(**data)
            except Exception as e:
                print(f"Ошибка чтения кэша {cache_key}: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, result: ExtractedDocument):
        """Сохраняет результат в кэш."""
        if not self.config.cache_enabled:
            return
        
        cache_file = self.config.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения в кэш {cache_key}: {e}")
    
    def extract_knowledge(self, document: InputDocument) -> Optional[ExtractedDocument]:
        """
        Извлекает знания из одного документа.
        
        Args:
            document: Входной документ
            
        Returns:
            ExtractedDocument: Результат извлечения или None при ошибке
        """
        # Проверяем кэш
        cache_key = self._generate_cache_key(document)
        cached_result = self._get_cached_result(cache_key)
        
        if cached_result:
            self.stats["cached"] += 1
            return cached_result
        
        # Формируем текст для анализа
        text_to_analyze = f"Title: {document.title}\nAbstract: {document.abstract}"
        if document.content:
            text_to_analyze += f"\nContent: {document.content[:1000]}..."
        
        # Формируем полный промпт
        full_prompt = f"{self.master_prompt}\n\nТекст для анализа:\n{text_to_analyze}"
        
        try:
            # Вызываем LLM с принуждением к структуре
            result = self.llm_client.chat.completions.create(
                model=self.config.llm_model,
                response_model=ExtractedDocument,
                messages=[
                    {
                        "role": "system", 
                        "content": "Ты эксперт по извлечению знаний из научных текстов."
                    },
                    {
                        "role": "user", 
                        "content": full_prompt
                    }
                ],
                temperature=0.1,
                max_retries=2
            )
            
            # Устанавливаем source_id и source_url из исходного документа
            result.source_id = document.source_id
            result.source_url = document.source_url
            
            # Сохраняем в кэш
            self._save_to_cache(cache_key, result)
            
            # Обновляем статистику
            self.stats["processed"] += 1
            self.stats["total_entities"] += len(result.knowledge_graph.entities)
            self.stats["total_relationships"] += len(result.knowledge_graph.relationships)
            
            return result
            
        except Exception as e:
            print(f"Ошибка при обработке документа {document.source_id}: {e}")
            self.stats["errors"] += 1
            return None
    
    async def extract_knowledge_batch(self, documents: List[InputDocument]) -> List[Optional[ExtractedDocument]]:
        """
        Асинхронная пакетная обработка документов.
        
        Args:
            documents: Список документов для обработки
            
        Returns:
            List[Optional[ExtractedDocument]]: Результаты обработки
        """
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        async def process_single(doc: InputDocument) -> Optional[ExtractedDocument]:
            async with semaphore:
                # Выполняем в отдельном потоке чтобы не блокировать event loop
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.extract_knowledge, doc)
        
        # Запускаем обработку всех документов параллельно
        tasks = [process_single(doc) for doc in documents]
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    def process_jsonl_file(self, input_file: str, output_file: str):
        """
        Обрабатывает JSONL файл с документами.
        
        Args:
            input_file: Путь к входному файлу
            output_file: Путь к выходному файлу
        """
        print(f"🔄 Начинаем обработку файла: {input_file}")
        
        # Читаем входные документы
        documents = []
        try:
            with jsonlines.open(input_file, 'r') as reader:
                for line in reader:
                    try:
                        doc = InputDocument(**line)
                        documents.append(doc)
                    except Exception as e:
                        print(f"Ошибка парсинга строки: {e}")
        except FileNotFoundError:
            print(f"❌ Файл не найден: {input_file}")
            return
        
        if not documents:
            print("❌ Нет документов для обработки")
            return
        
        print(f"📚 Загружено документов: {len(documents)}")
        
        # Обрабатываем пакетами
        results = []
        
        with tqdm(total=len(documents), desc="Обработка документов") as pbar:
            for i in range(0, len(documents), self.config.batch_size):
                batch = documents[i:i + self.config.batch_size]
                
                # Асинхронная обработка пакета
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    batch_results = loop.run_until_complete(
                        self.extract_knowledge_batch(batch)
                    )
                    results.extend(batch_results)
                finally:
                    loop.close()
                
                pbar.update(len(batch))
        
        # Фильтруем успешные результаты
        successful_results = [r for r in results if r is not None]
        
        # Сохраняем результаты
        try:
            with jsonlines.open(output_file, 'w') as writer:
                for result in successful_results:
                    writer.write(result.model_dump())
            
            print(f"✅ Результаты сохранены: {output_file}")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
        
        # Выводим статистику
        self._print_stats(len(documents), len(successful_results))
    
    def _print_stats(self, total_input: int, total_output: int):
        """Выводит статистику обработки."""
        print(f"\n📊 Статистика обработки:")
        print(f"  Всего документов: {total_input}")
        print(f"  Успешно обработано: {self.stats['processed']}")
        print(f"  Взято из кэша: {self.stats['cached']}")
        print(f"  Ошибок: {self.stats['errors']}")
        print(f"  Итого на выходе: {total_output}")
        print(f"  Извлечено сущностей: {self.stats['total_entities']}")
        print(f"  Извлечено отношений: {self.stats['total_relationships']}")


def main():
    """Точка входа для CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Knowledge Extractor - Извлечение знаний из научных документов")
    parser.add_argument("--input", "-i", help="Входной JSONL файл", default="harvested_data.jsonl")
    parser.add_argument("--output", "-o", help="Выходной JSONL файл", default="extracted_data.jsonl")
    parser.add_argument("--batch-size", "-b", type=int, help="Размер пакета", default=5)
    parser.add_argument("--no-cache", action="store_true", help="Отключить кэширование")
    
    args = parser.parse_args()
    
    # Настраиваем конфигурацию
    config = ExtractorConfig()
    config.input_filename = args.input
    config.output_filename = args.output
    config.batch_size = args.batch_size
    config.cache_enabled = not args.no_cache
    
    # Создаем экстрактор и запускаем обработку
    try:
        extractor = KnowledgeExtractor(config)
        extractor.process_jsonl_file(args.input, args.output)
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    main() 