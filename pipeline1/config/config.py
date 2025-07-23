"""
Централизованная конфигурация для всего backend проекта
Автоматически загружает переменные окружения при импорте
"""

import os
from typing import Optional
from pathlib import Path

# Автоматически загружаем .env файл при импорте модуля
try:
    import dotenv
    dotenv.load_dotenv()  # Ищет .env автоматически в текущей и родительских папках
    print("✅ Переменные окружения загружены")
except ImportError:
    print("⚠️  python-dotenv не установлен")


class Config:
    """Базовый класс конфигурации для всего проекта."""
    
    # Общие настройки
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


class ExtractorConfig(Config):
    """Конфигурация экстрактора научной нарративы."""
    
    def __init__(self):
        """Инициализация конфигурации с созданием необходимых директорий."""
        # API ключи
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.llm_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        # Модели и URL
        self.DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.llm_model = os.getenv("LLM_MODEL_NAME", "gpt-4-turbo-preview")
        self.GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
        self.llm_base_url = os.getenv("LLM_BASE_URL")
        
        # Параметры обработки
        self.MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "2000"))
        self.TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
        
        # Настройки кэширования
        self.cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        self.cache_dir = Path(os.getenv("CACHE_DIR", "cache"))
        
        # Настройки батчинга и параллелизма
        self.batch_size = int(os.getenv("BATCH_SIZE", "5"))
        self.max_concurrent = int(os.getenv("MAX_CONCURRENT", "3"))
        
        # Пути файлов
        self.input_filename = os.getenv("INPUT_FILENAME", "harvested_data.jsonl")
        self.output_filename = os.getenv("OUTPUT_FILENAME", "extracted_data.jsonl")
        self.prompt_file = Path(os.getenv("PROMPT_FILE", "prompts/extractor_prompt.txt"))
        self.DEFAULT_INPUT_FILE = os.getenv("DEFAULT_INPUT_FILE", "input_documents.jsonl")
        self.DEFAULT_OUTPUT_FILE = os.getenv("DEFAULT_OUTPUT_FILE", "extracted_narrative.jsonl")
        
        # Создаем директории
        self.cache_dir.mkdir(exist_ok=True)
        self.prompt_file.parent.mkdir(exist_ok=True)

    def get_api_key(self) -> str:
        """Получает API ключ из переменной окружения."""
        api_key = self.GEMINI_API_KEY or self.llm_api_key
        if not api_key:
            raise ValueError(
                "API ключ не найден. "
                "Установите переменную окружения GEMINI_API_KEY или OPENAI_API_KEY. "
                "Получить ключ можно на: https://makersuite.google.com/app/apikey"
            )
        return api_key

    def validate_config(self) -> bool:
        """Проверяет корректность конфигурации."""
        try:
            self.get_api_key()
            return True
        except ValueError:
            return False


class AIAgentConfig(Config):
    """Конфигурация для AI Agent модуля."""
    
    # Здесь будут настройки для AI Agent
    pass


class ArchitectConfig(Config):
    """Конфигурация для Architect модуля."""
    
    # Здесь будут настройки для Architect
    pass


class HarvesterConfig(Config):
    """Конфигурация для Harvester модуля."""
    
    # Здесь будут настройки для Harvester
    pass 