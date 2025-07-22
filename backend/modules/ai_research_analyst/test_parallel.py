#!/usr/bin/env python3
"""
Тест параллельной работы AI Research Analyst
"""

import logging
import time
from typing import List

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Импорты модулей системы
import sys
import os

# Добавляем путь к backend для корректного импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, backend_dir)

from modules.ai_research_analyst.arxiv_harvester import ArxivHarvester
from modules.ai_research_analyst.query_strategist import QueryStrategist  
from modules.ai_research_analyst.paper_evaluator import PaperEvaluator
from modules.ai_research_analyst.models import Paper

def test_parallel_search():
    """Тестирует параллельный поиск статей"""
    logger.info("🧪 Тест параллельного поиска статей")
    
    harvester = ArxivHarvester()
    
    # Тестовые запросы
    test_queries = [
        "knowledge distillation",
        "small language models",
        "reasoning abilities",
        "chain of thought"
    ]
    
    logger.info(f"Тестируем на {len(test_queries)} запросах: {test_queries}")
    
    # Последовательный поиск (для сравнения)
    start_time = time.time()
    sequential_results = {}
    for query in test_queries:
        papers = harvester.search_papers(query, max_results=5)
        sequential_results[query] = papers
        logger.info(f"Последовательно: '{query}' -> {len(papers)} статей")
    sequential_time = time.time() - start_time
    
    # Параллельный поиск
    start_time = time.time()
    parallel_results = harvester.search_papers_parallel(test_queries, max_results=5, max_workers=3)
    parallel_time = time.time() - start_time
    
    # Сравнение результатов
    logger.info(f"\n📊 Результаты сравнения:")
    logger.info(f"⏱️ Последовательное время: {sequential_time:.2f}s")
    logger.info(f"⚡ Параллельное время: {parallel_time:.2f}s")
    logger.info(f"🚀 Ускорение: {sequential_time/parallel_time:.2f}x")
    
    # Проверяем что результаты совпадают
    total_sequential = sum(len(papers) for papers in sequential_results.values())
    total_parallel = sum(len(papers) for papers in parallel_results.values())
    
    logger.info(f"📈 Статей найдено последовательно: {total_sequential}")
    logger.info(f"📈 Статей найдено параллельно: {total_parallel}")
    
    if abs(total_sequential - total_parallel) <= 1:  # Небольшая погрешность допустима
        logger.info("✅ Результаты совпадают!")
        return True
    else:
        logger.error("❌ Результаты не совпадают!")
        return False

def test_parallel_evaluation():
    """Тестирует параллельную оценку статей"""
    logger.info("\n🧪 Тест параллельной оценки статей")
    
    evaluator = PaperEvaluator()
    
    # Создаем тестовые статьи
    test_papers = []
    for i in range(25):  # Создаем 25 статей для тестирования батчевой обработки
        paper = Paper(
            id=f"test_paper_{i}",
            published_date="2024-01-01",
            title=f"Test Paper {i}: AI and Machine Learning Research",
            summary=f"This is a test paper about AI research, specifically focusing on topic {i}. It demonstrates various machine learning techniques and methodologies.",
            authors=[f"Author {i}", f"Co-Author {i}"],
            url=f"https://arxiv.org/abs/test{i}"
        )
        test_papers.append(paper)
    
    research_topic = "AI research methodologies and machine learning techniques"
    
    logger.info(f"Тестируем на {len(test_papers)} статьях")
    
    try:
        # Обычная оценка (только 5 статей чтобы быстрее)
        start_time = time.time()
        normal_results = evaluator.evaluate_papers(test_papers[:5], research_topic)
        normal_time = time.time() - start_time
        
        logger.info(f"✅ Обычная оценка прошла успешно: {len(normal_results)} статей за {normal_time:.2f}s")
        
        # Параллельная оценка
        start_time = time.time()
        parallel_results = evaluator.evaluate_papers_parallel(test_papers, research_topic, batch_size=8, max_workers=3)
        parallel_time = time.time() - start_time
        
        logger.info(f"\n📊 Результаты оценки:")
        logger.info(f"⏱️ Обычная оценка (5 статей): {normal_time:.2f}s")
        logger.info(f"⚡ Параллельная оценка (25 статей): {parallel_time:.2f}s")
        logger.info(f"📈 Обработано статей: {len(parallel_results)}")
        
        if len(parallel_results) == len(test_papers):
            logger.info("✅ Все статьи обработаны!")
            return True
        else:
            logger.error(f"❌ Обработано {len(parallel_results)} из {len(test_papers)} статей")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка в тесте оценки: {e}")
        import traceback
        logger.error(f"Подробности: {traceback.format_exc()}")
        return False

def main():
    """Главная функция тестирования"""
    logger.info("🚀 Запуск тестов параллельной работы AI Research Analyst")
    
    success = True
    
    try:
        # Тест 1: Параллельный поиск
        if not test_parallel_search():
            success = False
            
        # Тест 2: Параллельная оценка
        if not test_parallel_evaluation():
            success = False
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в тестах: {e}")
        success = False
    
    if success:
        logger.info("\n🎉 Все тесты пройдены успешно!")
        logger.info("✅ Параллельная система работает корректно")
    else:
        logger.error("\n❌ Некоторые тесты провалились")
        logger.error("🔧 Требуется отладка системы")
    
    return success

if __name__ == "__main__":
    main() 