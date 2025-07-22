"""
Главная точка входа для AI Research Analyst
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Добавляем путь к модулям в PYTHONPATH  
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.ai_research_analyst.orchestrator import ResearchOrchestrator
from modules.ai_research_analyst.config import LOG_LEVEL, TARGET_PAPER_COUNT


def setup_logging():
    """Настраивает логирование"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('research_analyst.log')
        ]
    )


def validate_environment():
    """Проверяет наличие необходимых переменных окружения"""
    api_provider = os.getenv('API_PROVIDER', 'gemini').lower()
    
    if api_provider == 'gemini':
        if not os.getenv('GEMINI_API_KEY'):
            print("❌ Ошибка: Переменная окружения GEMINI_API_KEY не установлена")
            print("Создайте файл .env с вашим Gemini API ключом:")
            print("API_PROVIDER=gemini")
            print("GEMINI_API_KEY=your_gemini_api_key_here")
            print("\n💡 Получить ключ: https://makersuite.google.com/app/apikey")
            sys.exit(1)
    else:
        if not os.getenv('OPENAI_API_KEY'):
            print("❌ Ошибка: Переменная окружения OPENAI_API_KEY не установлена")
            print("Создайте файл .env с вашим OpenAI API ключом:")
            print("API_PROVIDER=openai")
            print("OPENAI_API_KEY=your_openai_api_key_here")
            sys.exit(1)


def parse_arguments():
    """Парсит аргументы командной строки"""
    parser = argparse.ArgumentParser(
        description="AI Research Analyst - автономный анализ научных статей",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Базовый запуск с дефолтными настройками
  python main.py "создание системы определения релевантного направления ресерча"

  # Запуск с указанием количества статей
  python main.py "machine learning evaluation" --target-count 15

  # Интерактивный режим
  python main.py --interactive

  # Сохранение отчета в файл
  python main.py "AI agents research" --output report.md
        """
    )
    
    parser.add_argument(
        'topic',
        nargs='?',
        help='Тема исследования (если не указана, будет запрошена интерактивно)'
    )
    
    parser.add_argument(
        '--target-count',
        type=int,
        default=TARGET_PAPER_COUNT,
        help=f'Целевое количество валидированных статей (по умолчанию: {TARGET_PAPER_COUNT})'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Путь к файлу для сохранения отчета (по умолчанию: вывод в консоль)'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Интерактивный режим ввода параметров'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Подробный вывод (уровень DEBUG)'
    )
    
    return parser.parse_args()


def interactive_mode():
    """Интерактивный режим ввода параметров"""
    print("\n🤖 AI Research Analyst - Интерактивный режим")
    print("=" * 50)
    
    # Ввод темы исследования
    while True:
        topic = input("\n📝 Введите тему исследования: ").strip()
        if topic:
            break
        print("❌ Тема не может быть пустой")
    
    # Ввод количества статей
    while True:
        try:
            count_input = input(f"\n🎯 Целевое количество статей (по умолчанию {TARGET_PAPER_COUNT}): ").strip()
            target_count = int(count_input) if count_input else TARGET_PAPER_COUNT
            if target_count > 0:
                break
            print("❌ Количество должно быть положительным числом")
        except ValueError:
            print("❌ Введите корректное число")
    
    # Ввод пути для сохранения (опционально)
    output_path = input("\n💾 Путь для сохранения отчета (Enter для вывода в консоль): ").strip()
    output_path = output_path if output_path else None
    
    return topic, target_count, output_path


def save_report(report_content: str, output_path: str):
    """Сохраняет отчет в файл"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"✅ Отчет сохранен в файл: {output_path}")
    except Exception as e:
        print(f"❌ Ошибка при сохранении отчета: {e}")


def main():
    """Главная функция"""
    # Парсинг аргументов
    args = parse_arguments()
    
    # Настройка логирования
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    setup_logging()
    
    # Проверка окружения
    validate_environment()
    
    # Получение параметров
    if args.interactive:
        topic, target_count, output_path = interactive_mode()
    else:
        if not args.topic:
            print("❌ Ошибка: Укажите тему исследования или используйте --interactive")
            sys.exit(1)
        
        topic = args.topic
        target_count = args.target_count
        output_path = args.output
    
    # Вывод параметров запуска
    print(f"\n🚀 Запуск AI Research Analyst")
    print(f"📝 Тема: {topic}")
    print(f"🎯 Целевое количество: {target_count}")
    print(f"💾 Сохранение: {'В файл ' + output_path if output_path else 'В консоль'}")
    print("\n" + "="*60)
    
    try:
        # Создание и запуск оркестратора
        orchestrator = ResearchOrchestrator()
        report = orchestrator.run_research_pipeline(topic, target_count)
        
        # Сохранение или вывод отчета
        if output_path:
            save_report(report, output_path)
        else:
            print("\n" + "="*60)
            print("📊 ИТОГОВЫЙ ОТЧЕТ")
            print("="*60)
            print(report)
        
        print(f"\n✨ Анализ завершен успешно!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Анализ прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        logging.exception("Критическая ошибка в main()")
        sys.exit(1)


if __name__ == "__main__":
    main() 