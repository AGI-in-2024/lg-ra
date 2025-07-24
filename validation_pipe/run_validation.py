#!/usr/bin/env python3
"""
Удобный запуск модуля валидации исследовательских отчетов
"""

import os
import sys
import pathlib

def main():
    """Главная функция запуска"""
    print("🧬 Валидатор исследовательских отчетов")
    print("=" * 50)
    
    # Проверяем API ключ
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ Ошибка: GOOGLE_API_KEY не установлен")
        print("\n📝 Инструкция по настройке:")
        print("1. Получите API ключ: https://makersuite.google.com/app/apikey")
        print("2. Установите переменную окружения:")
        print("   export GOOGLE_API_KEY=your_gemini_api_key_here")
        print("\n💡 Или создайте файл .env с содержимым:")
        print("   GOOGLE_API_KEY=your_gemini_api_key_here")
        return
    
    # Проверяем зависимости
    try:
        from validation import ReportValidator
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("\n📦 Установите зависимости:")
        print("   pip install -r requirements.txt")
        return
    
    # Проверяем структуру данных
    data_dir = pathlib.Path("data/dataset2")
    input_dir = data_dir / "input"
    topredict_dir = data_dir / "topredict"
    
    if not input_dir.exists():
        print(f"❌ Папка не найдена: {input_dir}")
        print("📁 Создайте структуру папок согласно README.md")
        return
    
    if not topredict_dir.exists():
        print(f"❌ Папка не найдена: {topredict_dir}")
        print("📁 Создайте структуру папок согласно README.md")
        return
    
    # Проверяем файлы
    report_file = input_dir / "hierarchical_research_report.json"
    if not report_file.exists():
        print(f"❌ Файл не найден: {report_file}")
        print("📄 Поместите hierarchical_research_report.json в папку input/")
        return
    
    pdf_files = list(topredict_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ PDF файлы не найдены в: {topredict_dir}")
        print("📄 Поместите PDF файлы для валидации в папку topredict/")
        return
    
    print(f"✅ Все проверки пройдены!")
    print(f"📊 Найден отчет: {report_file}")
    print(f"📄 Найдено PDF файлов: {len(pdf_files)}")
    
    # Запускаем валидацию
    try:
        validator = ReportValidator()
        validator.run_validation()
        
        print("\n🎉 Валидация завершена успешно!")
        print("📁 Результаты сохранены в папке 'results/'")
        
    except Exception as e:
        print(f"\n❌ Ошибка валидации: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 