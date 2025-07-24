"""
Конфигурация для модуля анализа arXiv статей
"""

import os
from typing import List

# Gemini API конфигурация (через OpenAI compatibility)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GEMINI_MODEL = "gemini-2.0-flash"

# ArXiv API конфигурация
ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
DEFAULT_MAX_RESULTS = 10

# Параметры анализа
ANALYSIS_TEMPERATURE = 0.1  # Низкая температура для более консистентных результатов
ANALYSIS_MAX_TOKENS = 4000

# Промпты для системы
TASK_DESCRIPTION_PATH = "docsforllm/initialtask.md"

# Категории для анализа статей (из чеклиста)
ANALYSIS_CATEGORIES = {
    "prioritization": {
        "name": "Приоритизация и Генерация Идей",
        "criteria": [
            "algorithm_search",
            "relevance_justification", 
            "knowledge_gaps",
            "balance_hotness_novelty"
        ]
    },
    "validation": {
        "name": "Оценка и Валидация",
        "criteria": [
            "benchmarks",
            "metrics",
            "evaluation_methodology",
            "expert_validation"
        ]
    },
    "architecture": {
        "name": "Архитектура и Взаимодействие Агентов",
        "criteria": [
            "roles_and_sops",
            "communication",
            "memory_context",
            "self_correction"
        ]
    },
    "knowledge": {
        "name": "Работа со Знаниями",
        "criteria": [
            "extraction",
            "representation",
            "conflict_resolution"
        ]
    },
    "implementation": {
        "name": "Практическая Реализация",
        "criteria": [
            "tools_frameworks",
            "open_source",
            "reproducibility"
        ]
    }
}

# Веса для категорий при финальном ранжировании
CATEGORY_WEIGHTS = {
    "prioritization": 0.25,
    "validation": 0.2,
    "architecture": 0.25,
    "knowledge": 0.15,
    "implementation": 0.15
}

# Параметры поиска по умолчанию
DEFAULT_SEARCH_STRATEGIES = [
    "Broad Overview",
    "Focused Search", 
    "Architecture/Methodology Search",
    "Benchmark/Dataset Search"
]

# === НОВЫЕ НАСТРОЙКИ ДЛЯ УЛУЧШЕННОЙ СИСТЕМЫ СОХРАНЕНИЯ ===

# Структура директорий для сохранения результатов
OUTPUT_BASE_DIR = "output"  # Базовая директория для всех выходных файлов
REPORTS_DIR = "reports"     # Директория для финальных отчетов
STATE_DIR = "state"         # Директория для состояния системы
LOGS_DIR = "logs"           # Директория для логов (на будущее)

# Настройки именования файлов
REPORT_FILENAME_TEMPLATE = "arxiv_analysis_{timestamp}.json"
DEMO_QUICK_FILENAME = "demo_quick_analysis.json"
DEMO_FULL_FILENAME = "demo_full_analysis.json"

# Настройки структуры по датам
USE_DATE_STRUCTURE = True   # Создавать подпапки по датам (YYYY-MM-DD)
DATE_FORMAT = "%Y-%m-%d"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# Настройки сохранения отчетов
SAVE_FULL_RESULTS = False   # Включать ли полные результаты в JSON (может быть очень большим)
COMPRESS_REPORTS = False    # Сжимать ли отчеты (на будущее)
MAX_REPORT_SIZE_MB = 50     # Максимальный размер отчета в MB

# Настройки резервного копирования
BACKUP_OLD_REPORTS = True   # Создавать резервные копии при перезаписи
MAX_BACKUPS = 5            # Максимальное количество резервных копий

# Функция для получения полных путей
def get_output_paths(base_dir: str = OUTPUT_BASE_DIR, use_date_structure: bool = USE_DATE_STRUCTURE):
    """Возвращает словарь с полными путями для сохранения файлов"""
    from pathlib import Path
    from datetime import datetime
    
    base_path = Path(base_dir)
    
    if use_date_structure:
        date_str = datetime.now().strftime(DATE_FORMAT)
        reports_path = base_path / REPORTS_DIR / date_str
        state_path = base_path / STATE_DIR
        logs_path = base_path / LOGS_DIR / date_str
    else:
        reports_path = base_path / REPORTS_DIR
        state_path = base_path / STATE_DIR
        logs_path = base_path / LOGS_DIR
    
    return {
        "base": base_path,
        "reports": reports_path,
        "state": state_path,
        "logs": logs_path
    }

def create_output_structure(base_dir: str = OUTPUT_BASE_DIR):
    """Создает структуру директорий для выходных файлов"""
    from pathlib import Path
    
    paths = get_output_paths(base_dir)
    
    for path_name, path in paths.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Создана директория: {path}")
    
    return paths 