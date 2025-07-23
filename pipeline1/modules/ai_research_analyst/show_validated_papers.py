"""
Скрипт для отображения валидированных статей
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator import ResearchOrchestrator

def show_validated_papers():
    """Показывает детальную информацию о валидированных статьях"""
    
    print("🔍 Запуск анализа для получения валидированных статей...")
    
    # Создаем оркестратор и запускаем анализ
    orchestrator = ResearchOrchestrator()
    
    # Запускаем быстрый анализ с целью найти 3 статьи
    topic = "automated scientific paper evaluation"
    target_count = 3
    
    report = orchestrator.run_research_pipeline(topic, target_count)
    
    # Получаем валидированные статьи
    validated_papers, all_papers = orchestrator.get_results()
    
    print(f"\n{'='*80}")
    print(f"📊 ВАЛИДИРОВАННЫЕ СТАТЬИ")
    print(f"{'='*80}")
    print(f"Всего найдено: {len(validated_papers)} из {len(all_papers)} проанализированных")
    print(f"Порог оценки: 7.0")
    
    if not validated_papers:
        print("❌ Валидированных статей не найдено")
        return
    
    for i, paper in enumerate(validated_papers, 1):
        print(f"\n{'-'*80}")
        print(f"📄 СТАТЬЯ #{i}")
        print(f"{'-'*80}")
        print(f"🏷️  Название: {paper.title}")
        print(f"👥 Авторы: {', '.join(paper.authors)}")
        print(f"📅 Дата публикации: {paper.published_date}")
        print(f"🔗 URL: {paper.pdf_url}")
        print(f"📊 Оценка: {paper.score:.1f}/10")
        print(f"🏆 Ранг: {paper.rank if hasattr(paper, 'rank') else 'N/A'}")
        print(f"\n📝 Обоснование оценки:")
        print(f"   {paper.justification}")
        print(f"\n📄 Аннотация:")
        print(f"   {paper.summary[:200]}..." if len(paper.summary) > 200 else f"   {paper.summary}")
    
    print(f"\n{'-'*80}")
    print(f"📈 СТАТИСТИКА:")
    print(f"   Средняя оценка: {sum(p.score for p in validated_papers) / len(validated_papers):.2f}")
    print(f"   Топ оценка: {max(p.score for p in validated_papers):.1f}")
    print(f"   Минимальная оценка: {min(p.score for p in validated_papers):.1f}")
    print(f"{'='*80}")

if __name__ == "__main__":
    show_validated_papers() 