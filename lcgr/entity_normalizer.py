# -*- coding: utf-8 -*-
"""
Агент-нормализатор сущностей для системы анализа графа знаний
Группирует синонимы и создает каноническое представление биологических сущностей
"""

import json
from typing import Dict, List, Set
from google import genai

class EntityNormalizer:
    """
    Агент-нормализатор для группировки синонимов биологических сущностей
    Простой класс без сложных конструкций
    """
    
    def __init__(self):
        """Инициализация нормализатора"""
        self.normalization_map = {}
        self.reverse_map = {}  # Для быстрого поиска канонического имени
        self._google_client = None  # Ленивая инициализация
    
    @property
    def google_client(self):
        """Ленивая инициализация Google клиента"""
        if self._google_client is None:
            self._google_client = genai.Client()
        return self._google_client
    
    def collect_all_entities(self, documents_knowledge: List) -> List[str]:
        """
        Собирает все уникальные имена сущностей из всех документов
        
        Args:
            documents_knowledge: Список ExtractedKnowledge объектов
            
        Returns:
            Список уникальных имен сущностей
        """
        print("📋 Собираю все уникальные сущности из документов...")
        
        all_entity_names = set()
        
        # Проходим по всем документам
        for doc_knowledge in documents_knowledge:
            # Проходим по всем концептам в документе
            for concept in doc_knowledge.concepts:
                # Проходим по всем сущностям в концепте
                for entity in concept.mentioned_entities:
                    all_entity_names.add(entity.name)
        
        unique_entities = list(all_entity_names)
        print(f"   ✅ Найдено {len(unique_entities)} уникальных сущностей")
        
        return unique_entities
    
    def normalize_entities(self, entity_names: List[str]) -> Dict[str, List[str]]:
        """
        Нормализует список сущностей с помощью LLM
        
        Args:
            entity_names: Список имен сущностей для нормализации
            
        Returns:
            Словарь канонических имен и их синонимов
        """
        print("🤖 Запускаю агента-нормализатора...")
        
        # Prompt for entity normalizer agent
        prompt = """# ROLE
You are a world-class bioinformatics expert specializing in biological entity normalization and ontologies. Your task is to analyze a list of terms extracted from a corpus of longevity research papers and group them by canonical (commonly accepted) names.

# TASK
Analyze the following JSON array of entity names. Some of them are synonyms, abbreviations, or simply variations of the same thing. Group them together. If you are not sure, leave the entity in its own group.

# INPUT DATA (ENTITY LIST)
{entity_list}

# OUTPUT INSTRUCTIONS
Your response MUST be a JSON array of objects with canonical names and their aliases.

# EXAMPLE OUTPUT
[
  {{"canonical_name": "GLP-1R", "aliases": ["GLP-1R", "GLP1R", "Glucagon-like peptide-1 receptor"]}},
  {{"canonical_name": "Resveratrol", "aliases": ["RESVERATROL", "RSV", "resv"]}},
  {{"canonical_name": "NPY", "aliases": ["NPY", "Neuropeptide Y"]}},
  {{"canonical_name": "cfChPs", "aliases": ["cfChPs"]}}
]

# IMPORTANT RULES:
1. Use the most common/official name as canonical
2. Group only if you are 90%+ confident
3. Include the canonical name in the aliases list
4. Do not invent new groups - work only with the given entities"""

        try:
            # Подготавливаем данные для LLM
            entity_list_json = json.dumps(entity_names, ensure_ascii=False, indent=2)
            
            # Вызываем LLM с структурированным выводом (нативный Google API)
            response = self.google_client.models.generate_content(
                # model="gemini-2.5-flash"
                model="gemini-2.5-flash",
                contents=prompt.format(entity_list=entity_list_json),
                config={
                    "response_mime_type": "application/json",
                    "response_schema": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "canonical_name": {"type": "string"},
                                "aliases": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["canonical_name", "aliases"]
                        }
                    }
                }
            )
            
            # Парсим JSON ответ и конвертируем в словарь
            entities_array = json.loads(response.text)
            normalization_map = {}
            for item in entities_array:
                canonical = item["canonical_name"]
                aliases = item["aliases"]
                normalization_map[canonical] = aliases
            
            print(f"   ✅ Агент создал {len(normalization_map)} канонических групп")
            
            # Создаем обратный словарь для быстрого поиска
            reverse_map = {}
            for canonical_name, aliases in normalization_map.items():
                for alias in aliases:
                    reverse_map[alias] = canonical_name
            
            self.normalization_map = normalization_map
            self.reverse_map = reverse_map
            
            return normalization_map
            
        except Exception as e:
            print(f"   ❌ Ошибка при нормализации: {e}")
            print("   ⚠️ Использую исходные имена без нормализации")
            
            # Fallback: каждая сущность сама себе канонический вариант
            fallback_map = {name: [name] for name in entity_names}
            self.normalization_map = fallback_map
            self.reverse_map = {name: name for name in entity_names}
            
            return fallback_map
    
    def get_canonical_name(self, entity_name: str) -> str:
        """
        Получает каноническое имя для данной сущности
        
        Args:
            entity_name: Имя сущности
            
        Returns:
            Каноническое имя сущности
        """
        return self.reverse_map.get(entity_name, entity_name)
    
    def save_mapping(self, file_path: str) -> bool:
        """
        Сохраняет мапинг в JSON файл
        
        Args:
            file_path: Путь к файлу для сохранения
            
        Returns:
            True если сохранение успешно
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.normalization_map, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения мапинга: {e}")
            return False
    
    def load_mapping(self, file_path: str) -> bool:
        """
        Загружает мапинг из JSON файла
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            True если загрузка успешна
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.normalization_map = json.load(f)
            
            # Пересоздаем обратный словарь
            self.reverse_map = {}
            for canonical_name, aliases in self.normalization_map.items():
                for alias in aliases:
                    self.reverse_map[alias] = canonical_name
            
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки мапинга: {e}")
            return False
    
    def print_statistics(self):
        """Выводит статистику нормализации"""
        if not self.normalization_map:
            print("   ⚠️ Мапинг не создан")
            return
        
        total_entities = sum(len(aliases) for aliases in self.normalization_map.values())
        canonical_count = len(self.normalization_map)
        
        print(f"   📊 Статистика нормализации:")
        print(f"      • Всего сущностей: {total_entities}")
        print(f"      • Канонических групп: {canonical_count}")
        print(f"      • Степень сжатия: {total_entities/canonical_count:.1f}x")
        
        # Показываем несколько примеров групп
        print(f"   🔍 Примеры групп:")
        count = 0
        for canonical, aliases in self.normalization_map.items():
            if len(aliases) > 1 and count < 3:  # Показываем только группы с синонимами
                print(f"      • {canonical}: {aliases}")
                count += 1 


def normalize_entities_simple(documents_knowledge: List, save_file: str = "entity_normalization_map.json") -> EntityNormalizer:
    """
    Простая функция для быстрой нормализации сущностей
    Для использования в других модулях
    
    Args:
        documents_knowledge: Список ExtractedKnowledge объектов
        save_file: Файл для сохранения мапинга
        
    Returns:
        Настроенный EntityNormalizer
    """
    normalizer = EntityNormalizer()
    
    # Собираем сущности
    unique_entities = normalizer.collect_all_entities(documents_knowledge)
    
    if unique_entities:
        # Нормализуем
        normalizer.normalize_entities(unique_entities)
        
        # Сохраняем
        if save_file:
            normalizer.save_mapping(save_file)
            print(f"💾 Мапинг сохранен: {save_file}")
        
        # Показываем статистику
        normalizer.print_statistics()
    
    return normalizer 