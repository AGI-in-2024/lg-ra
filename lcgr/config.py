# -*- coding: utf-8 -*-
"""
Конфигурация и настройка клиентов для системы анализа графа знаний
Простая настройка без сложных конструкций
"""

import os
import instructor
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Проверяем наличие Google API ключа
def check_api_key():
    """Проверяет наличие Google API ключа"""
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ Ошибка: GOOGLE_API_KEY не найден!")
        print("🔧 Получите ключ: https://makersuite.google.com/app/apikey")
        print("🔧 Установите: export GOOGLE_API_KEY=your_api_key_here")
        exit(1)
    
    os.environ["GOOGLE_API_KEY"] = os.getenv('GOOGLE_API_KEY')
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def init_gemini_clients():
    """Инициализирует клиентов Gemini"""
    print("🚀 Инициализация Gemini клиентов...")
    
    try:
        # Клиент для извлечения (быстрый, дешевый)
        extractor_client = instructor.from_provider(
            "google/gemini-2.0-flash",
            mode=instructor.Mode.GENAI_TOOLS
        )
        
        # Клиент для анализа и критики (мощный)
        critic_client = instructor.from_provider(
            "google/gemini-2.5-flash", 
            # "google/gemini-2.0-flash",
            mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS
        )
        
        print("✅ Gemini клиенты успешно инициализированы!")
        return extractor_client, critic_client
        
    except Exception as e:
        print(f"❌ Ошибка инициализации Gemini: {e}")
        print("🔧 Проверьте ваш GOOGLE_API_KEY")
        exit(1)

# Инициализация при импорте модуля
check_api_key()
llm_extractor_client, llm_critic_client = init_gemini_clients() 