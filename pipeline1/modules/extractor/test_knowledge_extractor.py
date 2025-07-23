#!/usr/bin/env python3
"""
Тест для Модуля 2: Knowledge Extractor
Демонстрирует извлечение знаний из научных документов
"""

import os
import json
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from models import InputDocument, ExtractedDocument
from extractor import KnowledgeExtractor
from config.config import ExtractorConfig


def test_models():
    """Тест Pydantic моделей."""
    print("🧩 Тестирую Pydantic модели...")
    
    try:
        # Создаем тестовый входной документ
        input_doc = InputDocument(
            source_id="test_001",
            source_url="https://example.com/paper",
            title="SIRT1 activation by resveratrol extends lifespan in mice",
            abstract="We investigated the effects of resveratrol on SIRT1 activity and longevity in mice. Resveratrol treatment increased SIRT1 expression, leading to enhanced autophagy and a 20% increase in median lifespan.",
            content=None
        )
        
        print(f"✅ Входной документ создан: {input_doc.source_id}")
        
        # Тестируем валидацию схемы
        json_data = {
            "source_id": "test_001",
            "source_url": "https://example.com/paper",
            "classification": {
                "research_area": "longevity_interventions",
                "maturity_level": "basic_research"
            },
            "knowledge_graph": {
                "entities": [
                    {"name": "SIRT1", "type": "Gene/Protein"},
                    {"name": "resveratrol", "type": "Chemical/Drug"}
                ],
                "relationships": [
                    {"subject": "resveratrol", "predicate": "активирует", "object": "SIRT1"}
                ]
            }
        }
        
        extracted_doc = ExtractedDocument(**json_data)
        print(f"✅ Извлеченный документ валиден: {len(extracted_doc.knowledge_graph.entities)} сущностей")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в моделях: {e}")
        return False


def test_extractor():
    """Тест экстрактора знаний."""
    print("\n🔬 Тестирую Knowledge Extractor...")
    
    # Проверяем API ключ
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  API ключ не найден - пропускаем тест LLM")
        return True
    
    try:
        # Создаем экстрактор
        extractor = KnowledgeExtractor()
        print("✅ Экстрактор создан")
        
        # Тестовый документ
        test_doc = InputDocument(
            source_id="test_longevity_001",
            source_url=None,
            title="Caloric restriction activates SIRT1 and extends lifespan",
            abstract="Background: Caloric restriction (CR) is known to extend lifespan. We hypothesized that CR works through SIRT1 activation. Methods: We used C57BL/6 mice on 70% caloric intake. Results: CR mice showed 25% increased lifespan and elevated SIRT1 activity. Conclusions: CR extends lifespan via SIRT1 pathway.",
            content=None
        )
        
        print("📄 Обрабатываю тестовый документ...")
        
        # Извлекаем знания
        result = extractor.extract_knowledge(test_doc)
        
        if result:
            print(f"✅ Обработка успешна!")
            print(f"  📊 Область исследования: {result.classification.research_area}")
            print(f"  🎯 Уровень зрелости: {result.classification.maturity_level}")
            print(f"  🔗 Сущностей: {len(result.knowledge_graph.entities)}")
            print(f"  ↔️  Отношений: {len(result.knowledge_graph.relationships)}")
            
            # Показываем примеры
            if result.knowledge_graph.entities:
                print("  🧬 Примеры сущностей:")
                for entity in result.knowledge_graph.entities[:3]:
                    print(f"    • {entity.name} ({entity.type})")
            
            if result.knowledge_graph.relationships:
                print("  🔄 Примеры отношений:")
                for rel in result.knowledge_graph.relationships[:3]:
                    print(f"    • {rel.subject} → {rel.predicate} → {rel.object}")
            
            return True
        else:
            print("❌ Результат обработки пуст")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка в экстракторе: {e}")
        return False


def test_cache():
    """Тест системы кэширования."""
    print("\n💾 Тестирую кэширование...")
    
    try:
        config = ExtractorConfig()
        print(f"📁 Папка кэша: {config.cache_dir}")
        print(f"🔧 Кэширование: {'включено' if config.cache_enabled else 'отключено'}")
        
        if config.cache_dir.exists():
            cache_files = list(config.cache_dir.glob("*.json"))
            print(f"📄 Файлов в кэше: {len(cache_files)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка кэша: {e}")
        return False


def test_prompt_loading():
    """Тест загрузки промпта."""
    print("\n📋 Тестирую загрузку промпта...")
    
    try:
        config = ExtractorConfig()
        
        if config.prompt_file.exists():
            with open(config.prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read()
            print(f"✅ Промпт загружен: {len(prompt)} символов")
            
            # Проверяем основные секции промпта
            sections = ["ЗАДАЧА:", "КОНТЕКСТ:", "ФОРМАТ ВЫВОДА:"]
            found_sections = []
            for section in sections:
                if section in prompt:
                    found_sections.append(section)
            
            print(f"📋 Найденные секции: {', '.join(found_sections)}")
            return True
        else:
            print(f"⚠️  Файл промпта не найден: {config.prompt_file}")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка загрузки промпта: {e}")
        return False


def run_all_tests():
    """Запуск всех тестов."""
    print("🧪 Запускаю все тесты Knowledge Extractor...")
    print("=" * 60)
    
    tests = [
        ("Модели", test_models),
        ("Кэширование", test_cache),
        ("Промпт", test_prompt_loading),
        ("Экстрактор", test_extractor),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n🔍 Тест: {name}")
        print("-" * 40)
        result = test_func()
        results.append((name, result))
        print(f"{'✅ ПРОЙДЕН' if result else '❌ ПРОВАЛЕН'}")
    
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"  {name}: {status}")
    
    print(f"\n🎯 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты успешно пройдены!")
    else:
        print("⚠️  Некоторые тесты провалены. Проверьте конфигурацию.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1) 