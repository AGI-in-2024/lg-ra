#!/usr/bin/env python3
"""
Скрипт для показа ВСЕХ проанализированных статей с детальным анализом
"""

import asyncio
import json
import sys
from pathlib import Path

# Добавляем путь к модулю  
sys.path.append(str(Path(__file__).parent.parent.parent))

from airesearcher.arxiv_analyzer.main import ArxivAnalyzer
from airesearcher.arxiv_analyzer.state_manager import StateManager


def show_detailed_analysis(analysis_data):
    """Показывает детальный анализ статьи"""
    print(f"📊 ДЕТАЛЬНЫЙ АНАЛИЗ:")
    
    # Показываем оценки по всем категориям
    if hasattr(analysis_data, 'prioritization'):
        print(f"\n🎯 ПРИОРИТИЗАЦИЯ И ГЕНЕРАЦИЯ ИДЕЙ:")
        p = analysis_data.prioritization
        print(f"   • Алгоритм поиска: {p.algorithm_search.score}/5 - {p.algorithm_search.explanation}")
        print(f"   • Обоснование релевантности: {p.relevance_justification.score}/5 - {p.relevance_justification.explanation}")
        print(f"   • Выявление пробелов: {p.knowledge_gaps.score}/5 - {p.knowledge_gaps.explanation}")
        print(f"   • Баланс популярность/новизна: {p.balance_hotness_novelty.score}/5 - {p.balance_hotness_novelty.explanation}")
    
    if hasattr(analysis_data, 'validation'):
        print(f"\n🔬 ОЦЕНКА И ВАЛИДАЦИЯ:")
        v = analysis_data.validation
        print(f"   • Бенчмарки: {v.benchmarks.score}/5 - {v.benchmarks.explanation}")
        print(f"   • Метрики: {v.metrics.score}/5 - {v.metrics.explanation}")
        print(f"   • Методология оценки: {v.evaluation_methodology.score}/5 - {v.evaluation_methodology.explanation}")
        print(f"   • Экспертная валидация: {v.expert_validation.score}/5 - {v.expert_validation.explanation}")
    
    if hasattr(analysis_data, 'architecture'):
        print(f"\n🏗️ АРХИТЕКТУРА И ВЗАИМОДЕЙСТВИЕ:")
        a = analysis_data.architecture
        print(f"   • Роли и процедуры: {a.roles_and_sops.score}/5 - {a.roles_and_sops.explanation}")
        print(f"   • Коммуникация: {a.communication.score}/5 - {a.communication.explanation}")
        print(f"   • Память и контекст: {a.memory_context.score}/5 - {a.memory_context.explanation}")
        print(f"   • Самокоррекция: {a.self_correction.score}/5 - {a.self_correction.explanation}")
    
    if hasattr(analysis_data, 'knowledge'):
        print(f"\n🧠 РАБОТА СО ЗНАНИЯМИ:")
        k = analysis_data.knowledge
        print(f"   • Извлечение знаний: {k.extraction.score}/5 - {k.extraction.explanation}")
        print(f"   • Представление знаний: {k.representation.score}/5 - {k.representation.explanation}")
        print(f"   • Разрешение конфликтов: {k.conflict_resolution.score}/5 - {k.conflict_resolution.explanation}")
    
    if hasattr(analysis_data, 'implementation'):
        print(f"\n⚙️ ПРАКТИЧЕСКАЯ РЕАЛИЗАЦИЯ:")
        i = analysis_data.implementation
        print(f"   • Инструменты и фреймворки: {i.tools_frameworks.score}/5 - {i.tools_frameworks.explanation}")
        print(f"   • Открытый код: {i.open_source.score}/5 - {i.open_source.explanation}")
        print(f"   • Воспроизводимость: {i.reproducibility.score}/5 - {i.reproducibility.explanation}")
    
    if hasattr(analysis_data, 'key_insights'):
        print(f"\n💡 КЛЮЧЕВЫЕ ИНСАЙТЫ:")
        for insight in analysis_data.key_insights:
            print(f"   • {insight}")
    
    if hasattr(analysis_data, 'relevance_to_task'):
        print(f"\n🔗 РЕЛЕВАНТНОСТЬ К ЗАДАЧЕ:")
        print(f"   {analysis_data.relevance_to_task}")


async def show_all_papers(limit: int = None):
    """Показывает все проанализированные статьи с детальным анализом"""
    
    print("📚 ПОКАЗ ВСЕХ ПРОАНАЛИЗИРОВАННЫХ СТАТЕЙ С ДЕТАЛЬНЫМ АНАЛИЗОМ")
    print("=" * 80)
    
    analyzer = ArxivAnalyzer(enable_state_tracking=True)
    state_manager = analyzer.state_manager
    
    # Получаем все проанализированные статьи
    all_papers = list(state_manager.analyzed_papers.values())
    
    if not all_papers:
        print("❌ Нет проанализированных статей. Запустите сначала анализ.")
        return
    
    print(f"📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"   • Всего статей: {len(all_papers)}")
    print(f"   • Диапазон оценок: {min(p.overall_score for p in all_papers):.3f} - {max(p.overall_score for p in all_papers):.3f}")
    print(f"   • Средняя оценка: {sum(p.overall_score for p in all_papers) / len(all_papers):.3f}")
    
    # Сортируем по приоритету
    sorted_papers = sorted(all_papers, key=lambda x: x.priority_score or x.overall_score, reverse=True)
    
    # Ограничиваем количество статей если задан лимит
    if limit:
        sorted_papers = sorted_papers[:limit]
        print(f"   • Показываем топ-{limit} статей")
    
    print("\n" + "=" * 80)
    
    for i, paper in enumerate(sorted_papers, 1):
        print(f"\n📄 СТАТЬЯ {i}/{len(sorted_papers)}")
        print("=" * 80)
        
        # Основная информация
        print(f"🏷️  Название: {paper.title}")
        print(f"🆔 arXiv ID: {paper.arxiv_id}")
        print(f"📈 Общая оценка: {paper.overall_score:.3f}")
        print(f"🏅 Приоритет: {paper.priority_score or 'N/A'}")
        print(f"📅 Дата анализа: {paper.analysis_timestamp}")
        print(f"🏷️  Сессия: {paper.session_id}")
        
        # Получаем полный анализ из state manager
        try:
            full_analysis = state_manager.get_full_analysis(paper.arxiv_id)
            if full_analysis:
                show_detailed_analysis(full_analysis)
            else:
                print("⚠️  Детальный анализ не найден или не сохранен в старом формате")
        except Exception as e:
            print(f"❌ Ошибка получения анализа: {e}")
        
        print("\n" + "-" * 80)
        
        # Пауза для чтения только если показываем все статьи
        if not limit and i < len(sorted_papers):
            try:
                input("\n📖 Нажмите Enter для следующей статьи (Ctrl+C для выхода)...")
            except KeyboardInterrupt:
                print("\n\n👋 Просмотр прерван пользователем")
                break
    
    print(f"\n✅ Показано {i} из {len(all_papers)} статей")


def show_summary_only():
    """Показывает только краткую сводку всех статей"""
    print("📚 КРАТКАЯ СВОДКА ВСЕХ СТАТЕЙ")
    print("=" * 80)
    
    analyzer = ArxivAnalyzer(enable_state_tracking=True)
    all_papers = list(analyzer.state_manager.analyzed_papers.values())
    
    if not all_papers:
        print("❌ Нет проанализированных статей")
        return
    
    # Сортируем по приоритету
    sorted_papers = sorted(all_papers, key=lambda x: x.priority_score or x.overall_score, reverse=True)
    
    print(f"📊 Всего статей: {len(sorted_papers)}\n")
    
    for i, paper in enumerate(sorted_papers, 1):
        priority = paper.priority_score or paper.overall_score
        print(f"{i:2d}. 📈{paper.overall_score:.3f} 🏅{priority:.3f} | {paper.title[:70]}...")
        print(f"     🆔 {paper.arxiv_id} | 📅 {paper.analysis_timestamp[:10]} | 🏷️ {paper.session_id}")
        print()


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Показ всех проанализированных статей")
    parser.add_argument("--summary", action="store_true", help="Показать только краткую сводку")
    parser.add_argument("--top", type=int, help="Показать детальный анализ только топ-N статей")
    
    args = parser.parse_args()
    
    if args.summary:
        show_summary_only()
    else:
        asyncio.run(show_all_papers(limit=args.top))


if __name__ == "__main__":
    main() 