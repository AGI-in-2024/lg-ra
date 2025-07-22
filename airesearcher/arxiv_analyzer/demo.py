#!/usr/bin/env python3
"""
Демонстрационный скрипт для модуля анализа arXiv статей с отслеживанием прогресса

Запуск:
python demo.py [--quick] [--no-incremental] [--show-progress] [--clear-state] [--api-key YOUR_KEY]
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Добавляем путь к модулю
sys.path.append(str(Path(__file__).parent.parent.parent))

from airesearcher.arxiv_analyzer.main import ArxivAnalyzer


async def run_quick_demo(incremental: bool = True, custom_output_dir: str = None):
    """Быстрая демонстрация с ограниченными параметрами"""
    print("🚀 Запуск быстрой демонстрации...")
    print("   Параметры: 3 статьи на запрос, максимум 10 статей, без LLM ранжирования")
    if custom_output_dir:
        print(f"   📂 Выходной каталог: {custom_output_dir}")
    
    analyzer = ArxivAnalyzer(enable_state_tracking=True, custom_output_dir=custom_output_dir)
    
    try:
        results = await analyzer.run_full_analysis(
            max_papers_per_query=3,
            max_total_papers=10,
            use_llm_ranking=False,
            incremental=incremental
        )
        
        analyzer.print_summary(results)
        
        if 'error' not in results and 'message' not in results:
            # Используем новую систему путей с настраиваемым именем файла
            try:
                from airesearcher.arxiv_analyzer.config import DEMO_QUICK_FILENAME
            except ImportError:
                from config import DEMO_QUICK_FILENAME
                
            filename = await analyzer.save_results(results, DEMO_QUICK_FILENAME)
            print(f"\n✅ Результаты быстрой демо сохранены в {filename}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def run_full_demo(incremental: bool = True, custom_output_dir: str = None):
    """Полная демонстрация с LLM ранжированием"""
    print("🚀 Запуск полной демонстрации...")
    print("   Параметры: 8 статей на запрос, максимум 30 статей, с LLM ранжированием")
    if custom_output_dir:
        print(f"   📂 Выходной каталог: {custom_output_dir}")
    
    analyzer = ArxivAnalyzer(enable_state_tracking=True, custom_output_dir=custom_output_dir)
    
    try:
        results = await analyzer.run_full_analysis(
            max_papers_per_query=8,
            max_total_papers=30,
            use_llm_ranking=True,
            incremental=incremental
        )
        
        analyzer.print_summary(results)
        
        if 'error' not in results and 'message' not in results:
            # Используем новую систему путей с настраиваемым именем файла
            try:
                from airesearcher.arxiv_analyzer.config import DEMO_FULL_FILENAME
            except ImportError:
                from config import DEMO_FULL_FILENAME
                
            filename = await analyzer.save_results(results, DEMO_FULL_FILENAME)
            print(f"\n✅ Результаты полной демо сохранены в {filename}")
            
            # Дополнительная статистика
            print("\n📈 ДОПОЛНИТЕЛЬНАЯ СТАТИСТИКА:")
            ranking_summary = results.get('ranking_summary', {})
            if ranking_summary:
                print(f"   • Общее количество статей: {ranking_summary.get('total', 0)}")
                print(f"   • Средняя оценка топ-5: {ranking_summary.get('top_5_avg_score', 0):.3f}")
                
                categories = ranking_summary.get('categories_analysis', {})
                print("   • Средние оценки по категориям:")
                for category, score in categories.items():
                    print(f"     - {category}: {score:.2f}")
            
            # Показываем топ статьи за все время
            top_papers = analyzer.get_top_papers_all_time(5)
            if top_papers:
                print("\n🏆 ТОП-5 СТАТЕЙ ЗА ВСЕ ВРЕМЯ:")
                for paper in top_papers:
                    print(f"   {paper['rank']}. {paper['title'][:50]}...")
                    print(f"      📈 Оценка: {paper['overall_score']:.3f} | arXiv: {paper['arxiv_id']}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def show_progress(custom_output_dir: str = None):
    """Показывает текущий прогресс"""
    analyzer = ArxivAnalyzer(enable_state_tracking=True, custom_output_dir=custom_output_dir)
    analyzer.print_progress()
    
    # Показываем структуру сохраненных файлов
    show_output_structure(custom_output_dir)
    
    # Показываем топ статьи
    top_papers = analyzer.get_top_papers_all_time(10)
    if top_papers:
        print(f"\n🏆 ТОП-{len(top_papers)} СТАТЕЙ ЗА ВСЕ ВРЕМЯ:")
        for paper in top_papers:
            print(f"\n{paper['rank']}. {paper['title'][:60]}...")
            print(f"   📈 Общая оценка: {paper['overall_score']:.3f}")
            print(f"   🏅 Приоритет: {paper['priority_score']:.3f}")
            print(f"   📅 Дата анализа: {paper['analysis_date'][:10]}")
            print(f"   🏷️  Сессия: {paper['session_id']}")
            print(f"   🔗 arXiv: {paper['arxiv_id']}")
    else:
        print("\n📝 Пока нет проанализированных статей")


def show_output_structure(custom_output_dir: str = None):
    """Показывает структуру выходных файлов"""
    try:
        from airesearcher.arxiv_analyzer.config import get_output_paths
    except ImportError:
        from config import get_output_paths
    
    if custom_output_dir:
        paths = get_output_paths(custom_output_dir)
    else:
        paths = get_output_paths()
    
    print("\n📂 СТРУКТУРА ВЫХОДНЫХ ФАЙЛОВ:")
    for path_name, path in paths.items():
        if path.exists():
            try:
                # Подсчитываем файлы в каталоге
                files = list(path.glob("**/*"))
                file_count = len([f for f in files if f.is_file()])
                dir_count = len([f for f in files if f.is_dir()])
                
                print(f"   📁 {path_name}: {path}")
                print(f"      📄 Файлов: {file_count}, 📂 Подкаталогов: {dir_count}")
                
                # Показываем последние файлы
                recent_files = sorted([f for f in files if f.is_file()], 
                                    key=lambda x: x.stat().st_mtime, reverse=True)[:3]
                
                for file in recent_files:
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"         • {file.name} ({size_mb:.2f} MB)")
                        
            except Exception as e:
                print(f"   📁 {path_name}: {path} (ошибка: {e})")
        else:
            print(f"   📁 {path_name}: {path} (не существует)")

def clear_state(custom_output_dir: str = None):
    """Очищает состояние"""
    print("🗑️ Очистка состояния...")
    
    analyzer = ArxivAnalyzer(enable_state_tracking=True, custom_output_dir=custom_output_dir)
    
    # Показываем текущее состояние
    progress = analyzer.show_progress()
    if progress.get('total_analyzed_papers', 0) > 0:
        print(f"⚠️ Будет удалено {progress['total_analyzed_papers']} проанализированных статей")
        print(f"⚠️ Будет удалено {progress['total_sessions']} сессий")
        
        confirm = input("Вы уверены? (yes/no): ")
        if confirm.lower() in ['yes', 'y', 'да']:
            analyzer.clear_state(confirm=True)
        else:
            print("❌ Отменено")
    else:
        print("ℹ️ Состояние уже пустое")


def check_requirements():
    """Проверяет наличие необходимых зависимостей и настроек"""
    print("🔍 Проверка требований...")
    
    # Проверка API ключа
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Не найден GEMINI_API_KEY в переменных окружения")
        print("   Установите ключ: export GEMINI_API_KEY='your_key'")
        return False
    else:
        print(f"✅ API ключ найден: {api_key[:10]}...{api_key[-5:]}")
    
    # Проверка файла с задачей
    task_file = Path("../../docsforllm/initialtask.md")
    if not task_file.exists():
        print(f"❌ Не найден файл с описанием задачи: {task_file}")
        return False
    else:
        print(f"✅ Файл с задачей найден: {task_file}")
    
    # Проверка зависимостей
    try:
        import openai
        import aiohttp
        import pydantic
        print("✅ Все зависимости установлены")
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("   Установите: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Демонстрация модуля анализа arXiv статей с отслеживанием состояния")
    parser.add_argument("--quick", action="store_true", help="Быстрая демонстрация (меньше API вызовов)")
    parser.add_argument("--no-incremental", action="store_true", help="Отключить инкрементальный режим")
    parser.add_argument("--show-progress", action="store_true", help="Показать текущий прогресс и выйти")
    parser.add_argument("--clear-state", action="store_true", help="Очистить сохраненное состояние")
    parser.add_argument("--show-structure", action="store_true", help="Показать структуру выходных файлов")
    parser.add_argument("--output-dir", help="Пользовательский каталог для сохранения результатов")
    parser.add_argument("--api-key", help="Gemini API ключ (если не в переменной окружения)")
    
    args = parser.parse_args()
    
    # Установка API ключа если передан
    if args.api_key:
        os.environ["GEMINI_API_KEY"] = args.api_key
    
    print("=" * 70)
    print("🧪 ДЕМОНСТРАЦИЯ МОДУЛЯ АНАЛИЗА ARXIV СТАТЕЙ С ОТСЛЕЖИВАНИЕМ СОСТОЯНИЯ")
    print("=" * 70)
    
    # Специальные команды
    if args.show_progress:
        show_progress(args.output_dir)
        return
    
    if args.show_structure:
        show_output_structure(args.output_dir)
        return
    
    if args.clear_state:
        clear_state(args.output_dir)
        return
    
    # Проверка требований
    if not check_requirements():
        print("\n❌ Проверка требований не пройдена. Завершение.")
        return
    
    print("\n✅ Все требования выполнены. Запуск демонстрации...\n")
    
    incremental = not args.no_incremental
    if incremental:
        print("♻️  Инкрементальный режим: включен (пропуск уже проанализированных статей)")
    else:
        print("🔄 Инкрементальный режим: отключен (повторный анализ всех статей)")
    
    # Запуск соответствующей демонстрации
    if args.quick:
        asyncio.run(run_quick_demo(incremental, args.output_dir))
    else:
        asyncio.run(run_full_demo(incremental, args.output_dir))
    
    print("\n" + "=" * 70)
    print("✨ Демонстрация завершена!")
    print("\n💡 Полезные команды:")
    print("   python demo.py --show-progress     # Показать прогресс")
    print("   python demo.py --show-structure    # Показать структуру файлов")
    print("   python demo.py --clear-state       # Очистить состояние")
    print("   python demo.py --no-incremental    # Отключить инкрементальный режим")
    print("   python demo.py --output-dir custom # Использовать пользовательский каталог")
    print("=" * 70)


if __name__ == "__main__":
    main() 