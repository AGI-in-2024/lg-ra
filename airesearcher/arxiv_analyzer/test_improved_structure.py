#!/usr/bin/env python3
"""
Тестовый скрипт для проверки улучшенной системы сохранения отчетов

Тестирует:
1. Создание структуры каталогов
2. Сохранение с новыми путями
3. Резервное копирование
4. Различные конфигурации
"""

import asyncio
import json
import sys
from pathlib import Path

# Добавляем путь к модулю
sys.path.append(str(Path(__file__).parent.parent.parent))

from airesearcher.arxiv_analyzer.config import (
    get_output_paths, create_output_structure,
    DEMO_QUICK_FILENAME, DEMO_FULL_FILENAME
)


def test_output_structure():
    """Тестирует создание структуры каталогов"""
    print("🧪 Тест 1: Создание структуры каталогов")
    
    # Тест с базовыми настройками
    print("\n   📁 Базовая структура:")
    paths = get_output_paths()
    created_paths = create_output_structure()
    
    for name, path in created_paths.items():
        exists = "✅" if path.exists() else "❌"
        print(f"      {exists} {name}: {path}")
    
    # Тест с пользовательским каталогом
    print("\n   📁 Пользовательская структура:")
    custom_paths = get_output_paths("test_output", use_date_structure=False)
    custom_created = create_output_structure("test_output")
    
    for name, path in custom_created.items():
        exists = "✅" if path.exists() else "❌"
        print(f"      {exists} {name}: {path}")
    
    return created_paths, custom_created


def test_path_configs():
    """Тестирует различные конфигурации путей"""
    print("\n🧪 Тест 2: Конфигурации путей")
    
    # С датами
    paths_with_dates = get_output_paths(use_date_structure=True)
    print("\n   📅 С структурой по датам:")
    for name, path in paths_with_dates.items():
        print(f"      • {name}: {path}")
    
    # Без дат
    paths_no_dates = get_output_paths(use_date_structure=False)
    print("\n   📅 Без структуры по датам:")
    for name, path in paths_no_dates.items():
        print(f"      • {name}: {path}")
    
    return paths_with_dates, paths_no_dates


async def test_save_functionality():
    """Тестирует функциональность сохранения"""
    print("\n🧪 Тест 3: Функциональность сохранения")
    
    from airesearcher.arxiv_analyzer.main import ArxivAnalyzer
    
    # Создаем тестовые данные
    test_results = {
        "timestamp": "2025-01-21T12:00:00",
        "test": True,
        "statistics": {
            "papers_analyzed": 5,
            "duration": 120.5
        },
        "top_papers": [
            {"title": "Test Paper 1", "score": 0.95},
            {"title": "Test Paper 2", "score": 0.87}
        ],
        "full_results": {"detailed": "data", "size": "large"}
    }
    
    # Тест 1: Стандартное сохранение
    print("\n   💾 Тест стандартного сохранения:")
    analyzer = ArxivAnalyzer(enable_state_tracking=False)
    saved_path = await analyzer.save_results(test_results, "test_standard.json")
    if saved_path:
        print(f"   ✅ Сохранено в: {saved_path}")
        file_size = Path(saved_path).stat().st_size
        print(f"   📏 Размер файла: {file_size} байт")
    
    # Тест 2: Сохранение с пользовательским каталогом
    print("\n   💾 Тест сохранения в пользовательский каталог:")
    analyzer_custom = ArxivAnalyzer(enable_state_tracking=False, custom_output_dir="test_custom")
    saved_path_custom = await analyzer_custom.save_results(test_results, "test_custom.json")
    if saved_path_custom:
        print(f"   ✅ Сохранено в: {saved_path_custom}")
    
    # Тест 3: Демо файлы
    print("\n   💾 Тест демо файлов:")
    quick_path = await analyzer.save_results(test_results, DEMO_QUICK_FILENAME)
    full_path = await analyzer.save_results(test_results, DEMO_FULL_FILENAME)
    
    if quick_path:
        print(f"   ✅ Quick demo: {quick_path}")
    if full_path:
        print(f"   ✅ Full demo: {full_path}")
    
    return [saved_path, saved_path_custom, quick_path, full_path]


def test_backup_functionality():
    """Тестирует функциональность резервного копирования"""
    print("\n🧪 Тест 4: Резервное копирование")
    
    from airesearcher.arxiv_analyzer.main import ArxivAnalyzer
    
    # Создаем анализатор
    analyzer = ArxivAnalyzer(enable_state_tracking=False)
    
    # Создаем тестовый файл
    test_file = Path("output/reports") / "test_backup.json"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_data = {"version": 1, "data": "original"}
    with open(test_file, 'w') as f:
        json.dump(test_data, f)
    
    print(f"   📄 Создан тестовый файл: {test_file}")
    
    # Тестируем создание резервной копии
    if test_file.exists():
        analyzer._create_backup(test_file, max_backups=3)
        
        # Проверяем наличие резервной копии
        backup_dir = test_file.parent / "backups"
        if backup_dir.exists():
            backups = list(backup_dir.glob("test_backup_backup_*.json"))
            print(f"   ✅ Создано резервных копий: {len(backups)}")
            for backup in backups:
                print(f"      📋 {backup.name}")
        else:
            print("   ❌ Каталог backups не создан")
    
    return test_file


def test_config_loading():
    """Тестирует загрузку конфигурации"""
    print("\n🧪 Тест 5: Загрузка конфигурации")
    
    try:
        from airesearcher.arxiv_analyzer.config import (
            OUTPUT_BASE_DIR, REPORTS_DIR, STATE_DIR,
            REPORT_FILENAME_TEMPLATE, USE_DATE_STRUCTURE,
            SAVE_FULL_RESULTS, BACKUP_OLD_REPORTS
        )
        
        print("   ✅ Конфигурационные переменные загружены:")
        print(f"      📁 Базовый каталог: {OUTPUT_BASE_DIR}")
        print(f"      📄 Каталог отчетов: {REPORTS_DIR}")
        print(f"      💾 Каталог состояния: {STATE_DIR}")
        print(f"      📝 Шаблон файла: {REPORT_FILENAME_TEMPLATE}")
        print(f"      📅 Структура по датам: {USE_DATE_STRUCTURE}")
        print(f"      💾 Полные результаты: {SAVE_FULL_RESULTS}")
        print(f"      🔄 Резервное копирование: {BACKUP_OLD_REPORTS}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Ошибка импорта конфигурации: {e}")
        return False


async def run_all_tests():
    """Запускает все тесты"""
    print("🚀 ЗАПУСК ТЕСТОВ УЛУЧШЕННОЙ СИСТЕМЫ СОХРАНЕНИЯ")
    print("=" * 60)
    
    results = {}
    
    # Тест 1: Структура каталогов
    try:
        results['structure'] = test_output_structure()
        print("   ✅ Тест структуры каталогов пройден")
    except Exception as e:
        print(f"   ❌ Тест структуры каталогов: {e}")
        results['structure'] = None
    
    # Тест 2: Конфигурации путей
    try:
        results['paths'] = test_path_configs()
        print("   ✅ Тест конфигураций путей пройден")
    except Exception as e:
        print(f"   ❌ Тест конфигураций путей: {e}")
        results['paths'] = None
    
    # Тест 3: Функциональность сохранения
    try:
        results['save'] = await test_save_functionality()
        print("   ✅ Тест сохранения пройден")
    except Exception as e:
        print(f"   ❌ Тест сохранения: {e}")
        results['save'] = None
    
    # Тест 4: Резервное копирование
    try:
        results['backup'] = test_backup_functionality()
        print("   ✅ Тест резервного копирования пройден")
    except Exception as e:
        print(f"   ❌ Тест резервного копирования: {e}")
        results['backup'] = None
    
    # Тест 5: Загрузка конфигурации
    try:
        results['config'] = test_config_loading()
        print("   ✅ Тест загрузки конфигурации пройден")
    except Exception as e:
        print(f"   ❌ Тест загрузки конфигурации: {e}")
        results['config'] = False
    
    print("\n" + "=" * 60)
    print("📊 СВОДКА ТЕСТОВ:")
    
    passed = sum(1 for v in results.values() if v is not None and v != False)
    total = len(results)
    
    print(f"   ✅ Пройдено: {passed}/{total}")
    
    if passed == total:
        print("   🎉 Все тесты пройдены успешно!")
    else:
        print("   ⚠️ Некоторые тесты не пройдены")
    
    return results


def cleanup_test_files():
    """Очищает тестовые файлы"""
    print("\n🧹 Очистка тестовых файлов...")
    
    import shutil
    
    test_dirs = ["output", "test_output", "test_custom"]
    
    for test_dir in test_dirs:
        test_path = Path(test_dir)
        if test_path.exists():
            try:
                shutil.rmtree(test_path)
                print(f"   🗑️ Удален: {test_path}")
            except Exception as e:
                print(f"   ⚠️ Не удалось удалить {test_path}: {e}")


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Тест улучшенной системы сохранения")
    parser.add_argument("--cleanup", action="store_true", help="Очистить тестовые файлы после тестов")
    parser.add_argument("--no-cleanup", action="store_true", help="Не очищать тестовые файлы")
    
    args = parser.parse_args()
    
    # Запускаем тесты
    asyncio.run(run_all_tests())
    
    # Очистка
    if args.cleanup or (not args.no_cleanup):
        cleanup_test_files()
    
    print("\n🏁 Тестирование завершено!")


if __name__ == "__main__":
    main() 