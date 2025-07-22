#!/usr/bin/env python3
"""
Пример запуска AI Research Analyst

Этот файл демонстрирует, как использовать систему программно.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.ai_research_analyst.orchestrator import ResearchOrchestrator


def main():
    """Пример использования AI Research Analyst"""
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Проверка API ключа
    api_provider = os.getenv('API_PROVIDER', 'gemini').lower()
    
    if api_provider == 'gemini':
        if not os.getenv('GEMINI_API_KEY'):
            print("❌ Ошибка: GEMINI_API_KEY не установлен")
            print("Создайте файл .env и добавьте ваш Gemini API ключ")
            print("💡 Получить ключ: https://makersuite.google.com/app/apikey")
            return
    else:
        if not os.getenv('OPENAI_API_KEY'):
            print("❌ Ошибка: OPENAI_API_KEY не установлен")
            print("Создайте файл .env и добавьте ваш OpenAI API ключ")
            return
    
    # Пример тем для исследования
    research_topics = [
        "создание системы определения релевантного направления ресерча",
        "automated scientific literature review",
        "AI agents for research assistance",
        "machine learning research evaluation methods"
    ]
    
    print("🤖 AI Research Analyst - Пример использования")
    print("=" * 60)
    
    # Выбор темы
    print("\nДоступные темы для исследования:")
    for i, topic in enumerate(research_topics, 1):
        print(f"{i}. {topic}")
    
    try:
        choice = input(f"\nВыберите тему (1-{len(research_topics)}) или введите свою: ")
        
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(research_topics):
                selected_topic = research_topics[idx]
            else:
                print("❌ Неверный выбор")
                return
        else:
            selected_topic = choice.strip()
            if not selected_topic:
                print("❌ Тема не может быть пустой")
                return
        
        print(f"\n📝 Выбранная тема: {selected_topic}")
        
        # Настройка параметров
        target_count = 5  # Для примера используем небольшое количество
        
        print(f"🎯 Целевое количество статей: {target_count}")
        print("\n" + "="*60)
        
        # Создание и запуск оркестратора
        orchestrator = ResearchOrchestrator()
        
        print("🚀 Запуск анализа...")
        report = orchestrator.run_research_pipeline(selected_topic, target_count)
        
        # Вывод результатов
        print("\n" + "="*60)
        print("📊 РЕЗУЛЬТАТЫ АНАЛИЗА")
        print("="*60)
        print(report)
        
        # Сохранение в файл
        output_file = f"research_report_{selected_topic[:30].replace(' ', '_')}.md"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n✅ Отчет сохранен в файл: {output_file}")
        except Exception as e:
            print(f"⚠️ Не удалось сохранить отчет: {e}")
        
        print("\n✨ Анализ завершен!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Анализ прерван пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        logging.exception("Ошибка в примере запуска")


if __name__ == "__main__":
    main() 