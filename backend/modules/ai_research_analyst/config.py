"""
Настройки для AI Research Analyst
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Основные настройки  
TARGET_PAPER_COUNT = int(os.getenv("TARGET_PAPER_COUNT", 10))
MIN_SCORE_THRESHOLD = float(os.getenv("MIN_SCORE_THRESHOLD", 7.0))
MAX_PAPERS_PER_QUERY = int(os.getenv("MAX_PAPERS_PER_QUERY", 20))
ARXIV_BASE_URL = "http://export.arxiv.org/api/query"

# API настройки
# Поддерживаем как OpenAI, так и Gemini API
API_PROVIDER = os.getenv("API_PROVIDER", "gemini")  # gemini или openai

if API_PROVIDER.lower() == "gemini":
    # Gemini API через OpenAI compatibility
    OPENAI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-2.5-flash")
else:
    # Стандартный OpenAI API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = None
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.3))

# Пути к промптам
PROMPTS_DIR = Path(__file__).parent / "prompts"
QUERY_STRATEGIST_PROMPT = PROMPTS_DIR / "query_strategist.txt"
PAPER_EVALUATOR_PROMPT = PROMPTS_DIR / "paper_evaluator.txt"
FINAL_SYNTHESIZER_PROMPT = PROMPTS_DIR / "final_synthesizer.txt"

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Тайм-ауты и лимиты
ARXIV_REQUEST_TIMEOUT = int(os.getenv("ARXIV_REQUEST_TIMEOUT", 30))
ARXIV_RATE_LIMIT_DELAY = float(os.getenv("ARXIV_RATE_LIMIT_DELAY", 1.0))  # секунд между запросами
LLM_REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", 60))

# Диагностическое логирование (после определения всех переменных)
import logging
config_logger = logging.getLogger(__name__ + ".config")
config_logger.info(f"🔧 Конфигурация API:")
config_logger.info(f"  API_PROVIDER: {API_PROVIDER}")
config_logger.info(f"  OPENAI_MODEL: {OPENAI_MODEL}")
config_logger.info(f"  OPENAI_BASE_URL: {OPENAI_BASE_URL}")
config_logger.info(f"  API ключ установлен: {'✅' if OPENAI_API_KEY else '❌'}")
if OPENAI_API_KEY:
    config_logger.info(f"  API ключ (первые 10 символов): {OPENAI_API_KEY[:10]}...")
config_logger.info(f"  TARGET_PAPER_COUNT: {TARGET_PAPER_COUNT}")
config_logger.info(f"  MIN_SCORE_THRESHOLD: {MIN_SCORE_THRESHOLD}") 