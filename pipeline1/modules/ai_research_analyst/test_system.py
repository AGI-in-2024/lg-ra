"""
Тестовый файл для проверки работы AI Research Analyst
"""

import os
import sys
import logging
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.ai_research_analyst.query_strategist import QueryStrategist
from modules.ai_research_analyst.arxiv_harvester import ArxivHarvester
from modules.ai_research_analyst.paper_evaluator import PaperEvaluator
from modules.ai_research_analyst.final_synthesizer import FinalSynthesizer
from modules.ai_research_analyst.orchestrator import ResearchOrchestrator


def test_query_strategist():
    """Тест генерации запросов"""
    print("🧪 Тестирование Query Strategist...")
    
    api_provider = os.getenv('API_PROVIDER', 'gemini').lower()
    api_key = os.getenv('GEMINI_API_KEY') if api_provider == 'gemini' else os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print(f"⚠️ API ключ для {api_provider} не установлен, пропускаем LLM тесты")
        return
    
    strategist = QueryStrategist()
    test_topic = "machine learning research evaluation"
    
    try:
        queries = strategist.generate_queries(test_topic)
        print(f"✅ Сгенерировано {len(queries)} запросов")
        for i, query in enumerate(queries[:3], 1):
            print(f"  {i}. {query}")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_arxiv_harvester():
    """Тест сбора статей с arXiv"""
    print("\n🧪 Тестирование ArXiv Harvester...")
    
    harvester = ArxivHarvester()
    test_query = "machine learning"
    
    try:
        papers = harvester.search_papers(test_query, max_results=3)
        print(f"✅ Найдено {len(papers)} статей")
        
        if papers:
            paper = papers[0]
            print(f"  Пример: {paper.title[:50]}...")
            print(f"  Авторы: {', '.join(paper.authors[:2])}")
            print(f"  Дата: {paper.published_date}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_paper_evaluator():
    """Тест оценки статей"""
    print("\n🧪 Тестирование Paper Evaluator...")
    
    api_provider = os.getenv('API_PROVIDER', 'gemini').lower()
    api_key = os.getenv('GEMINI_API_KEY') if api_provider == 'gemini' else os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print(f"⚠️ API ключ для {api_provider} не установлен, пропускаем LLM тесты")
        return True
    
    # Создаем тестовую статью
    from modules.ai_research_analyst.models import Paper
    
    test_paper = Paper(
        id="test_id",
        published_date="2024-01-01",
        title="A Survey of Machine Learning Research Evaluation Methods",
        summary="This paper presents a comprehensive survey of methods used to evaluate machine learning research, including quantitative metrics and qualitative assessments.",
        authors=["John Doe", "Jane Smith"]
    )
    
    evaluator = PaperEvaluator()
    test_topic = "machine learning research evaluation"
    
    try:
        ranked_paper = evaluator.evaluate_paper(test_paper, test_topic)
        print(f"✅ Оценка: {ranked_paper.score}")
        print(f"  Обоснование: {ranked_paper.justification[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_full_pipeline():
    """Тест полного пайплайна"""
    print("\n🧪 Тестирование полного пайплайна...")
    
    api_provider = os.getenv('API_PROVIDER', 'gemini').lower()
    api_key = os.getenv('GEMINI_API_KEY') if api_provider == 'gemini' else os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print(f"⚠️ API ключ для {api_provider} не установлен, пропускаем полный тест")
        return True
    
    orchestrator = ResearchOrchestrator()
    test_topic = "automated scientific paper evaluation"
    
    try:
        print("📝 Запуск мини-пайплайна (3 статьи)...")
        report = orchestrator.run_research_pipeline(test_topic, target_count=3)
        
        print("✅ Пайплайн выполнен успешно!")
        print(f"📊 Длина отчета: {len(report)} символов")
        print("📝 Начало отчета:")
        print(report[:300] + "...")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def main():
    """Главная функция тестирования"""
    # Настройка логирования для тестов (включаем DEBUG для диагностики)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Запуск тестов AI Research Analyst")
    print("=" * 50)
    
    tests = [
        test_arxiv_harvester,
        test_query_strategist, 
        test_paper_evaluator,
        test_full_pipeline
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("✅ Все тесты пройдены успешно!")
    else:
        print("⚠️ Некоторые тесты не прошли или были пропущены")
    
    print("\n💡 Совет: Установите GEMINI_API_KEY (рекомендуется) или OPENAI_API_KEY для полного тестирования")
    print("🔗 Получить Gemini API ключ: https://makersuite.google.com/app/apikey")


if __name__ == "__main__":
    main() 