import json
import os
from dotenv import load_dotenv

from .query_strategist import QueryStrategist
from .pubmed_fetcher import collect_pubmed_corpus
from .arxiv_fetcher import ArXivFetcher
from .data_processor import DataProcessor

load_dotenv()

def run_harvesting_pipeline(topic: str, start_date: str, end_date: str, 
                          sources: list = ["pubmed", "arxiv"], 
                          output_file: str = "final_corpus.json",
                          max_results: int = 250):
    """
    Запускает пайплайн сбора данных
    
    Args:
        topic: Тема для поиска
        start_date: Начальная дата в формате "YYYY/MM/DD"
        end_date: Конечная дата в формате "YYYY/MM/DD"
        sources: Список источников ["pubmed", "arxiv"]
        output_file: Файл для сохранения результата
        max_results: Максимальное количество статей для извлечения
    """
    
    print(f"Начинаем сбор данных по теме: {topic}")
    print(f"Источники: {', '.join(sources)}")
    
    # 1. Генерируем запросы
    strategist = QueryStrategist()
    queries = strategist.generate(topic)
    print(f"Сгенерировано {len(queries)} запросов")
    
    pubmed_data = {}
    arxiv_data = {}
    
    # 2. Собираем данные из PubMed
    if "pubmed" in sources:
        pubmed_data = collect_pubmed_corpus(queries, start_date, end_date, max_results_per_query=max_results)
        print(f"Найдено {len(pubmed_data)} статей в PubMed")
    
    # 3. Собираем данные из arXiv
    if "arxiv" in sources:
        arxiv_fetcher = ArXivFetcher()
        arxiv_data = arxiv_fetcher.fetch(queries, max_per_query=max_results)
        print(f"Найдено {len(arxiv_data)} статей в arXiv")
    
    # 4. Обрабатываем и унифицируем данные
    processor = DataProcessor()
    unified_corpus = processor.process(pubmed_data, arxiv_data if arxiv_data else None)
    print(f"Создан унифицированный корпус из {len(unified_corpus)} статей")
    
    # 5. Сохраняем результат
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(unified_corpus, f, ensure_ascii=False, indent=2)
    print(f"Корпус сохранен в {output_file}")
    
    return unified_corpus

if __name__ == '__main__':
    # Примеры использования
    
    # Только PubMed
    corpus1 = run_harvesting_pipeline(
        topic="longevity and aging mechanisms",
        start_date="2020/01/01",
        end_date="2024/12/31",
        sources=["pubmed"],
        output_file="pubmed_only_corpus.json",
        max_results=100
    )
    
    # Только arXiv
    corpus2 = run_harvesting_pipeline(
        topic="machine learning in biology",
        start_date="2020/01/01", 
        end_date="2024/12/31",
        sources=["arxiv"],
        output_file="arxiv_only_corpus.json",
        max_results=50
    )
    
    # Оба источника
    corpus3 = run_harvesting_pipeline(
        topic="longevity and aging mechanisms",
        start_date="2020/01/01",
        end_date="2024/12/31", 
        sources=["pubmed", "arxiv"],
        output_file="combined_corpus.json",
        max_results=150
    ) 