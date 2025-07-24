# -*- coding: utf-8 -*-
"""
Простой тест агента-нормализатора сущностей
Демонстрирует как работает нормализация синонимов
"""

from graph.entity_normalizer import EntityNormalizer

def test_entity_normalizer():
    """Простой тест нормализатора"""
    print("🧪 Тестируем агента-нормализатора...")
    
    # Создаем тестовый список сущностей с очевидными синонимами
    test_entities = [
        "GLP-1R",
        "GLP1R", 
        "Glucagon-like peptide-1 receptor",
        "RESVERATROL",
        "RSV",
        "resv",
        "NPY",
        "Neuropeptide Y",
        "SIRT1",
        "Sirtuin 1",
        "mTOR",
        "mechanistic target of rapamycin",
        "AMPK",
        "cfChPs",
        "Telomerase"
    ]
    
    print(f"📋 Исходный список: {len(test_entities)} сущностей")
    for entity in test_entities:
        print(f"   • {entity}")
    
    # Создаем нормализатор
    normalizer = EntityNormalizer()
    
    # Нормализуем
    mapping = normalizer.normalize_entities(test_entities)
    
    print(f"\n🤖 Результат нормализации:")
    for canonical, aliases in mapping.items():
        if len(aliases) > 1:  # Показываем только группы с синонимами
            print(f"   📍 {canonical}: {aliases}")
    
    # Тестируем поиск канонических имен
    print(f"\n🔍 Тестируем поиск канонических имен:")
    test_names = ["GLP1R", "RSV", "Sirtuin 1", "unknown_entity"]
    for name in test_names:
        canonical = normalizer.get_canonical_name(name)
        print(f"   '{name}' -> '{canonical}'")
    
    print("\n✅ Тест завершен!")

if __name__ == "__main__":
    test_entity_normalizer() 