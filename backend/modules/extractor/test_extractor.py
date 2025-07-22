#!/usr/bin/env python3
"""
Тест модуля Extractor v2.0
Демонстрирует работу извлечения научной нарративы
"""

import os
import json
from extractor import ScientificNarrativeExtractor
from models import DocumentInput
import dotenv
dotenv.load_dotenv()

def test_extractor():
    """Тестирует базовую функциональность экстрактора."""
    
    # Проверяем наличие API ключа
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Ошибка: API ключ GEMINI_API_KEY не установлен")
        print("Получите ключ на: https://makersuite.google.com/app/apikey")
        print("Затем установите: export GEMINI_API_KEY=your_key_here")
        return False
    
    print(f"✅ API ключ найден: {api_key[:10]}...")
    
    try:
        # Создаем экстрактор
        print("🔧 Создаем экстрактор...")
        extractor = ScientificNarrativeExtractor()
        print("✅ Экстрактор создан успешно")
        
        # Тестовая научная статья
        print("\n📄 Тестируем извлечение научной нарративы...")
        
        title = "Caloric restriction extends lifespan through autophagy activation"
        abstract = """
        Background: Caloric restriction (CR) is known to extend lifespan in various species.
        Hypothesis: We hypothesized that CR extends lifespan through activation of autophagy pathways.
        Methods: We used C57BL/6 mice divided into control and CR groups (70% caloric intake). 
        Autophagy was measured using LC3 immunostaining and Western blot analysis.
        Results: CR mice showed 25% increase in lifespan (p<0.001). LC3-II levels increased 3-fold.
        Conclusions: Our data demonstrate that caloric restriction extends lifespan through enhanced autophagy.
        """
        
        # Обрабатываем документ
        result = extractor.process_single_document(
            title=title,
            abstract=abstract,
            source_id="test_001"
        )
        
        print(f"✅ Обработка завершена")
        print(f"📊 Извлечено утверждений: {len(result.scientific_narrative)}")
        
        # Показываем результаты
        if result.scientific_narrative:
            print("\n🔬 Извлеченная научная нарратива:")
            for i, statement in enumerate(result.scientific_narrative, 1):
                print(f"\n{i}. Тип: {statement.statement_type}")
                print(f"   Содержание: {statement.statement_content}")
                
                if statement.knowledge_triples:
                    print("   📝 Knowledge Triples:")
                    for triple in statement.knowledge_triples:
                        print(f"     • {triple.subject} → {triple.predicate} → {triple.object}")
        else:
            print("⚠️  Нарратива не извлечена - возможно модель вернула пустой результат")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

def test_models():
    """Тестирует Pydantic модели."""
    print("\n🧩 Тестируем Pydantic модели...")
    
    try:
        from models import KnowledgeTriple, ScientificStatement, ExtractedNarrative
        
        # Создаем тестовые объекты
        triple = KnowledgeTriple(
            subject="caloric restriction",
            predicate="extends",
            object="lifespan"
        )
        
        statement = ScientificStatement(
            statement_type="Result",
            statement_content="CR mice showed 25% increase in lifespan",
            knowledge_triples=[triple]
        )
        
        narrative = ExtractedNarrative(
            scientific_narrative=[statement]
        )
        
        print(f"✅ Модели работают корректно")
        print(f"📄 Пример тройки: {triple.subject} → {triple.predicate} → {triple.object}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в моделях: {e}")
        return False

def main():
    """Запускает все тесты."""
    print("🚀 Тестирование Модуля 2 - Extractor v2.0")
    print("=" * 50)
    
    # Тест моделей
    models_ok = test_models()
    
    if models_ok:
        # Тест экстрактора
        extractor_ok = test_extractor()
        
        if extractor_ok:
            print("\n🎉 Все тесты прошли успешно!")
            print("Модуль Extractor v2.0 готов к использованию")
        else:
            print("\n💥 Тесты экстрактора провалены")
    else:
        print("\n💥 Тесты моделей провалены")

if __name__ == "__main__":
    main() 