#!/usr/bin/env python3
"""
Быстрый старт модуля анализа arXiv с отслеживанием прогресса

Демонстрирует основные сценарии использования:
1. Первый анализ
2. Инкрементальное обновление  
3. Просмотр прогресса
"""

import asyncio
import os
from pathlib import Path

# Настройка API ключа (замените на ваш)
import dotenv
dotenv.load_dotenv()

from .main import ArxivAnalyzer


async def scenario_1_first_analysis():
    """Сценарий 1: Первый анализ (создание базы знаний)"""
    print("🚀 СЦЕНАРИЙ 1: Первый анализ")
    print("="*50)
    
    analyzer = ArxivAnalyzer(enable_state_tracking=True)
    
    # Показываем текущее состояние (должно быть пустое)
    print("📊 Текущий прогресс:")
    analyzer.print_progress()
    
    # Запускаем первый анализ
    print("\n🔍 Запуск первого анализа...")
    results = await analyzer.run_full_analysis(
        max_papers_per_query=5,  # Небольшой тест
        max_total_papers=15,
        use_llm_ranking=False,   # Быстрее без LLM
        incremental=True
    )
    
    if 'error' not in results:
        print(f"\n✅ Первый анализ завершен!")
        print(f"📈 Проанализировано: {results['statistics']['papers_analyzed']} статей")
        print(f"⏱️ Время: {results['duration_seconds']:.1f} сек")
        
        # Показываем топ-3 статьи
        top_papers = results['top_papers'][:3]
        print(f"\n🏆 ТОП-3 СТАТЬИ:")
        for paper in top_papers:
            print(f"   {paper['rank']}. {paper['title'][:60]}...")
            print(f"      📈 Оценка: {paper['score']:.3f}")
    
    return results


async def scenario_2_incremental_update():
    """Сценарий 2: Инкрементальное обновление"""
    print("\n🔄 СЦЕНАРИЙ 2: Инкрементальное обновление")
    print("="*50)
    
    analyzer = ArxivAnalyzer(enable_state_tracking=True)
    
    # Показываем текущий прогресс
    print("📊 Состояние перед обновлением:")
    progress = analyzer.show_progress()
    if progress.get('total_analyzed_papers', 0) > 0:
        print(f"   📚 Уже проанализировано: {progress['total_analyzed_papers']} статей")
        print(f"   🕐 Последняя сессия: {progress['last_session']['id']}")
    
    # Запускаем инкрементальное обновление
    print("\n🔍 Поиск новых статей...")
    results = await analyzer.run_full_analysis(
        max_papers_per_query=5,
        max_total_papers=20,  # Чуть больше для поиска новых
        use_llm_ranking=False,
        incremental=True  # Ключевой параметр!
    )
    
    if 'message' in results:
        print(f"ℹ️ {results['message']}")
        # Показываем топ статьи за все время
        top_papers = analyzer.get_top_papers_all_time(5)
        if top_papers:
            print("\n🏆 ТОП-5 СТАТЕЙ ЗА ВСЕ ВРЕМЯ:")
            for paper in top_papers:
                print(f"   {paper['rank']}. {paper['title'][:50]}...")
                print(f"      📈 Оценка: {paper['overall_score']:.3f}")
    elif 'error' not in results:
        print(f"\n✅ Обновление завершено!")
        print(f"📈 Новых статей: {results['statistics']['papers_analyzed']}")
        print(f"📊 Всего в ранжировании: {results['statistics']['total_papers_in_ranking']}")
    
    return results


def scenario_3_show_progress():
    """Сценарий 3: Просмотр детального прогресса"""
    print("\n📈 СЦЕНАРИЙ 3: Детальный просмотр прогресса")
    print("="*50)
    
    analyzer = ArxivAnalyzer(enable_state_tracking=True)
    
    # Общий прогресс
    analyzer.print_progress()
    
    # Топ статьи за все время
    top_papers = analyzer.get_top_papers_all_time(7)
    if top_papers:
        print(f"\n🔬 ДЕТАЛЬНЫЙ АНАЛИЗ ТОП-{len(top_papers)} СТАТЕЙ:")
        for i, paper in enumerate(top_papers, 1):
            print(f"\n{i}. {paper['title'][:70]}...")
            print(f"   📈 Общая оценка: {paper['overall_score']:.3f}")
            print(f"   🏅 Приоритет: {paper['priority_score']:.3f}")
            print(f"   📅 Анализ: {paper['analysis_date'][:16]}")
            print(f"   🆔 arXiv: {paper['arxiv_id']}")
            print(f"   🏷️ Сессия: {paper['session_id']}")
    else:
        print("\n📝 Статей пока нет. Запустите анализ!")


async def main():
    """Основная демонстрация"""
    print("🧪 БЫСТРЫЙ СТАРТ: АНАЛИЗ ARXIV С ОТСЛЕЖИВАНИЕМ ПРОГРЕССА")
    print("="*70)
    
    # Проверяем настройки
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here":
        print("❌ Установите API ключ Gemini:")
        print("   export GEMINI_API_KEY='your_actual_key'")
        return
    
    if not Path("./docsforllm/initialtask.md").exists():
        print("❌ Файл ./docsforllm/initialtask.md не найден")
        print("   Запустите из корня проекта")
        return
    
    try:
        # Сценарий 1: Первый анализ
        results1 = await scenario_1_first_analysis()
        
        # Небольшая пауза для наглядности
        await asyncio.sleep(2)
        
        # Сценарий 2: Инкрементальное обновление
        results2 = await scenario_2_incremental_update()
        
        # Сценарий 3: Просмотр прогресса
        scenario_3_show_progress()
        
        print("\n" + "="*70)
        print("✨ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
        print("\n💡 Что дальше:")
        print("   1. Измените ./docsforllm/initialtask.md")
        print("   2. Запустите python demo.py --quick")
        print("   3. Система автоматически сгенерирует новые запросы")
        print("   4. Используйте python demo.py --show-progress для мониторинга")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\nПроверьте:")
        print("   - API ключ Gemini корректный")
        print("   - Файл ./docsforllm/initialtask.md существует")
        print("   - Интернет соединение активно")


if __name__ == "__main__":
    asyncio.run(main()) 