"""
Модуль 1: Harvester - Сбор научных данных

Планируется: автоматический сбор данных из PubMed, arXiv, bioRxiv и других источников
"""

__version__ = "1.0.0"

from .query_strategist import QueryStrategist
from .pubmed_fetcher import PubMedFetcher
from .arxiv_fetcher import ArXivFetcher
from .data_processor import DataProcessor
from .harvester_orchestrator import run_harvesting_pipeline

__all__ = [
    'QueryStrategist',
    'PubMedFetcher', 
    'ArXivFetcher',
    'DataProcessor',
    'run_harvesting_pipeline'
] 