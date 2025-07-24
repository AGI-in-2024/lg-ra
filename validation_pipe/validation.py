#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Валидация исследовательских отчетов через анализ PDF статей
Простой код для junior разработчиков
"""

import os
import json
import pathlib
from datetime import datetime
from typing import Dict, List, Optional

# Импорт для работы с Gemini API
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    print("❌ google-genai не установлен. Установите: pip install google-genai")
    GENAI_AVAILABLE = False

# Загрузка переменных окружения
from dotenv import load_dotenv
load_dotenv()


class ValidationResult:
    """Простой класс для результата валидации"""
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.validation_status = "unknown"
        self.confidence_score = 0.0
        self.matches_found = []
        self.discrepancies = []
        self.summary = ""
        self.recommendations = []


class ReportValidator:
    """Основной класс для валидации отчетов"""
    
    def __init__(self):
        """Инициализация валидатора"""
        # Проверяем API ключ
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "❌ GOOGLE_API_KEY не найден! "
                "Получите ключ: https://makersuite.google.com/app/apikey"
            )
        
        # Инициализируем клиент Gemini
        if GENAI_AVAILABLE:
            self.client = genai.Client(api_key=self.api_key)
        else:
            raise ImportError("google-genai пакет не установлен")
        
        # Пути к папкам
        self.data_dir = pathlib.Path("data/dataset2")
        self.input_dir = self.data_dir / "input"
        self.topredict_dir = self.data_dir / "topredict"
        self.results_dir = pathlib.Path("results")
        
        # Создаем папки если их нет
        self.results_dir.mkdir(exist_ok=True)
        
        print("✅ Валидатор успешно инициализирован")
    
    def load_research_report(self) -> Optional[Dict]:
        """Загружает hierarchical_research_report.json из папки input"""
        report_path = self.input_dir / "hierarchical_research_report.json"
        
        if not report_path.exists():
            print(f"❌ Файл отчета не найден: {report_path}")
            
            # Проверяем есть ли PDF файлы в input для создания отчета
            pdf_files = list(self.input_dir.glob("*.pdf"))
            if pdf_files:
                print(f"💡 Найдено {len(pdf_files)} PDF файлов в input")
                print("🔄 Попробуйте сначала запустить: python downlaod_init_data.py")
                print("   для создания отчета на основе PDF файлов")
            
            return None
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            print(f"✅ Загружен отчет с {report.get('total_programs', 0)} программами")
            return report
        except Exception as e:
            print(f"❌ Ошибка загрузки отчета: {e}")
            return None
    
    def convert_predictions_to_md(self, report: Dict) -> str:
        """Конвертирует JSON предсказаний в удобный MD формат"""
        md_content = "# Предсказанные исследовательские направления\n\n"
        
        # Проверяем структуру - hierarchical или research_report
        if 'programs' in report:
            # Структура hierarchical_research_report.json
            for program in report.get('programs', []):
                md_content += f"## {program.get('program_title', 'Без названия')}\n\n"
                md_content += f"**Описание программы:** {program.get('program_summary', '')}\n\n"
                
                for subgroup in program.get('subgroups', []):
                    md_content += f"### {subgroup.get('subgroup_type', 'Подгруппа')}\n\n"
                    md_content += f"{subgroup.get('subgroup_description', '')}\n\n"
                    
                    for direction in subgroup.get('directions', []):
                        rank = direction.get('rank', 0)
                        title = direction.get('title', 'Без названия')
                        description = direction.get('description', '')
                        
                        md_content += f"#### Направление {rank}: {title}\n\n"
                        md_content += f"{description}\n\n"
                        
                        # Добавляем критику если есть
                        critique = direction.get('critique', {})
                        if critique:
                            md_content += "**Оценка:**\n"
                            md_content += f"- Новизна: {critique.get('novelty_score', 0)}\n"
                            md_content += f"- Влияние: {critique.get('impact_score', 0)}\n"
                            md_content += f"- Осуществимость: {critique.get('feasibility_score', 0)}\n"
                            md_content += f"- Итоговая оценка: {critique.get('final_score', 0)}\n\n"
                        
                        md_content += "---\n\n"
        
        elif 'directions' in report:
            # Структура research_report.json
            md_content += f"**Общее количество направлений:** {report.get('total_directions', 0)}\n\n"
            
            for direction in report.get('directions', [])[:10]:  # Берем топ-10
                rank = direction.get('rank', 0)
                title = direction.get('title', 'Без названия')
                description = direction.get('description', '')
                
                md_content += f"## Направление {rank}: {title}\n\n"
                md_content += f"{description}\n\n"
                
                # Добавляем поддерживающие статьи
                papers = direction.get('supporting_papers', [])
                if papers:
                    md_content += f"**Поддерживающие статьи:** {', '.join(papers)}\n\n"
                
                # Добавляем критику если есть
                critique = direction.get('critique', {})
                if critique:
                    md_content += "**Оценка:**\n"
                    md_content += f"- Новизна: {critique.get('novelty_score', 0)}\n"
                    md_content += f"- Влияние: {critique.get('impact_score', 0)}\n"
                    md_content += f"- Осуществимость: {critique.get('feasibility_score', 0)}\n"
                    md_content += f"- Итоговая оценка: {critique.get('final_score', 0)}\n"
                    md_content += f"- Рекомендация: {critique.get('recommendation', 'Нет')}\n\n"
                
                md_content += "---\n\n"
        
        return md_content
    
    def find_pdf_files(self) -> List[pathlib.Path]:
        """Находит все PDF файлы в папке topredict"""
        pdf_files = list(self.topredict_dir.glob("*.pdf"))
        print(f"📄 Найдено {len(pdf_files)} PDF файлов")
        return pdf_files
    
    def extract_key_info_from_pdf(self, pdf_path: pathlib.Path) -> str:
        """Извлекает IRP (Идеализированную Исследовательскую Программу) из PDF статьи"""
        try:
            # Читаем PDF файл
            pdf_data = pdf_path.read_bytes()
            print(f"📊 Размер PDF файла: {len(pdf_data)} байт")
            
            # Детальный промпт для извлечения IRP согласно бенчмарку
            prompt = """
            Извлеки из научной статьи полную Идеализированную Исследовательскую Программу (IRP).
            Это то, как бы выглядел грант или план исследования, который привел к этой статье.
            
            ОБЯЗАТЕЛЬНО извлеки следующие компоненты:
            
            1. ПРОБЛЕМА И КОНТЕКСТ (Problem & Context):
               - Научный пробел (Knowledge Gap): Какое противоречие или недостаток знаний существовал до этой статьи?
               - Ключевая парадигма (Overarching Theme): В какой большой научной теме лежит работа?
            
            2. ЦЕНТРАЛЬНАЯ ГИПОТЕЗА (Core Hypothesis):
               - Главное проверяемое утверждение статьи
               - Конкретная формулировка того, что хотели доказать
            
            3. КЛЮЧЕВЫЕ КОМПОНЕНТЫ ИССЛЕДОВАНИЯ (Key Research Components):
               - Объекты (Entities): Основные молекулы/гены/белки, которые нужно было изучить
               - Механизмы (Mechanisms): Биологические процессы, которые нужно было исследовать  
               - Системы (Systems): Основные модели для исследования (клеточные линии, животные модели, ткани)
            
            4. КЛЮЧЕВЫЕ МЕТОДЫ (Essential Methods):
               - Список методов, без которых открытие было бы невозможно
               - Критически важные экспериментальные подходы
            
            5. ГЛАВНЫЙ ВЫВОД И ВКЛАД (Main Finding & Impact):
               - Краткая формулировка главного результата
               - Значимость для науки и медицины
               - Как это изменяет понимание в данной области
            
            Отвечай СТРУКТУРИРОВАННО на русском языке, четко разделяя каждый раздел.
            Будь максимально точным и детальным - эта информация будет использоваться для валидации предсказаний.
            """
            
            print(f"📝 Размер промпта: {len(prompt)} символов")
            print(f"🚀 Отправляю запрос к Gemini 2.0 Flash...")
            
            # Отправляем запрос к Gemini 2.0 Flash
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                    prompt
                ]
            )
            
            print(f"📥 Получен ответ от API")
            print(f"📊 Размер ответа: {len(response.text)} символов")
            print(f"📋 Первые 500 символов ответа:")
            print(f"'{response.text[:500]}...'")
            
            print(f"✅ Извлечена IRP из {pdf_path.name}")
            return response.text
            
        except Exception as e:
            print(f"❌ ОШИБКА извлечения IRP из PDF {pdf_path.name}:")
            print(f"   Тип ошибки: {type(e).__name__}")
            print(f"   Текст ошибки: {str(e)}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return ""
    
    def validate_predictions_vs_paper(self, predictions_md: str, paper_info: str) -> ValidationResult:
        """Валидирует предсказанные программы против IRP из статьи по критериям бенчмарка"""
        result = ValidationResult()
        
        print(f"📊 Размер PRP (предсказания): {len(predictions_md)} символов")
        print(f"📊 Размер IRP (из статьи): {len(paper_info)} символов")
        
        try:
            validation_prompt = f"""
            Выполни детальную валидацию предсказанных исследовательских программ (PRP) против 
            идеализированной исследовательской программы (IRP) из реальной статьи.
            
            ПРЕДСКАЗАННЫЕ ПРОГРАММЫ (PRP):
            {predictions_md[:5000]}
            
            ИДЕАЛИЗИРОВАННАЯ ПРОГРАММА ИЗ СТАТЬИ (IRP):
            {paper_info[:4000]}
            
            КРИТЕРИИ ОЦЕНКИ (согласно Research Program Prediction Benchmark):
            
            1. СООТВЕТСТВИЕ ГИПОТЕЗЫ (Hypothesis Match) - оценка 0-5:
               0 = Нет связи
               1 = Очень слабая связь
               2 = Слабая связь 
               3 = Концептуальное совпадение
               4 = Близкое совпадение
               5 = Прямое совпадение главной гипотезы
            
            2. ПОЛНОТА КОМПОНЕНТОВ (Component Recall) - проценты:
               - Объекты: % ключевых объектов (гены/белки/молекулы) из IRP, упомянутых в PRP
               - Механизмы: % ключевых механизмов из IRP, упомянутых в PRP  
               - Методы: % ключевых методов из IRP, упомянутых в PRP
            
            3. КАЧЕСТВО ПЛАНА (Plan Quality) - оценка 0-5:
               Насколько логичен и реалистичен предложенный план исследования?
               Соответствуют ли методы поставленным задачам?
            
            4. ТОЧНОСТЬ КОНТЕКСТА (Context Accuracy) - оценка 0-5:
               Насколько точно PRP описывает научный пробел и потенциальный вклад,
               как они определены в IRP?
            
            5. РАНЖИРОВАНИЕ (Ranking):
               Какое направление из PRP лучше всего соответствует IRP?
               Указать его ранг/позицию в списке предсказаний.
            
            ОБЯЗАТЕЛЬНЫЙ ФОРМАТ ОТВЕТА:
            СТАТУС: [ТОЧНОЕ_СОВПАДЕНИЕ/ХОРОШЕЕ_СОВПАДЕНИЕ/ЧАСТИЧНОЕ_СОВПАДЕНИЕ/СЛАБОЕ_СОВПАДЕНИЕ/НЕТ_СОВПАДЕНИЯ]
            
            СООТВЕТСТВИЕ_ГИПОТЕЗЫ: [0-5]
            ОБЪЕКТЫ_RECALL: [0-100%]
            МЕХАНИЗМЫ_RECALL: [0-100%]
            МЕТОДЫ_RECALL: [0-100%]
            КАЧЕСТВО_ПЛАНА: [0-5]
            ТОЧНОСТЬ_КОНТЕКСТА: [0-5]
            ЛУЧШИЙ_РАНГ: [номер лучше всего соответствующего направления]
            
            НАЙДЕННЫЕ_СОВПАДЕНИЯ:
            [детальный список совпадений]
            
            КРИТИЧЕСКИЕ_РАСХОЖДЕНИЯ:
            [список важных несоответствий]
            
            ИТОГОВАЯ_ОЦЕНКА:
            [детальное резюме качества предсказания на русском языке]
            """
            
            print(f"📝 Размер validation промпта: {len(validation_prompt)} символов")
            print(f"🚀 Отправляю validation запрос к Gemini 2.0 Flash...")
            
            # Отправляем запрос к Gemini 2.0 Flash
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[validation_prompt]
            )
            
            print(f"📥 Получен validation ответ от API")
            print(f"📊 Размер validation ответа: {len(response.text)} символов")
            print(f"📋 Первые 1000 символов validation ответа:")
            print(f"'{response.text[:1000]}...'")
            
            # Парсим детальный ответ
            response_text = response.text
            result.summary = response_text
            
            # Извлекаем статус с учетом новых категорий
            print(f"🔍 Парсинг статуса из ответа...")
            if "ТОЧНОЕ_СОВПАДЕНИЕ" in response_text:
                result.validation_status = "exact_match"
                result.confidence_score = 0.95
                print(f"✅ Найден статус: ТОЧНОЕ_СОВПАДЕНИЕ")
            elif "ХОРОШЕЕ_СОВПАДЕНИЕ" in response_text:
                result.validation_status = "good_match"
                result.confidence_score = 0.85
                print(f"✅ Найден статус: ХОРОШЕЕ_СОВПАДЕНИЕ")
            elif "ЧАСТИЧНОЕ_СОВПАДЕНИЕ" in response_text:
                result.validation_status = "partial_match"
                result.confidence_score = 0.65
                print(f"✅ Найден статус: ЧАСТИЧНОЕ_СОВПАДЕНИЕ")
            elif "СЛАБОЕ_СОВПАДЕНИЕ" in response_text:
                result.validation_status = "weak_match"
                result.confidence_score = 0.45
                print(f"✅ Найден статус: СЛАБОЕ_СОВПАДЕНИЕ")
            elif "НЕТ_СОВПАДЕНИЯ" in response_text:
                result.validation_status = "no_match"
                result.confidence_score = 0.9
                print(f"✅ Найден статус: НЕТ_СОВПАДЕНИЯ")
            else:
                result.validation_status = "unclear"
                result.confidence_score = 0.5
                print(f"⚠️  Статус не распознан, установлен: unclear")
                print(f"🔍 Ищем в тексте: {[s for s in ['ТОЧНОЕ_СОВПАДЕНИЕ', 'ХОРОШЕЕ_СОВПАДЕНИЕ', 'ЧАСТИЧНОЕ_СОВПАДЕНИЕ', 'СЛАБОЕ_СОВПАДЕНИЕ', 'НЕТ_СОВПАДЕНИЯ'] if s in response_text]}")
            
            print(f"✅ Детальная валидация завершена: {result.validation_status}")
            return result
            
        except Exception as e:
            print(f"❌ ОШИБКА валидации:")
            print(f"   Тип ошибки: {type(e).__name__}")
            print(f"   Текст ошибки: {str(e)}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            result.validation_status = "error"
            result.summary = f"Ошибка валидации: {str(e)}"
            return result
    
    def save_validation_result(self, result: ValidationResult, pdf_name: str):
        """Сохраняет результат валидации в папку results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"validation_{pdf_name}_{timestamp}.json"
        result_path = self.results_dir / result_filename
        
        # Конвертируем результат в словарь
        result_dict = {
            "timestamp": result.timestamp,
            "pdf_file": pdf_name,
            "validation_status": result.validation_status,
            "confidence_score": result.confidence_score,
            "matches_found": result.matches_found,
            "discrepancies": result.discrepancies,
            "summary": result.summary,
            "recommendations": result.recommendations
        }
        
        try:
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)
            print(f"💾 Результат сохранен: {result_path}")
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
    
    def run_validation(self):
        """Запускает полный процесс валидации по Research Program Prediction Benchmark"""
        print("🚀 Запуск валидации по RPPB (Research Program Prediction Benchmark)...")
        
        # 1. Загружаем отчет с предсказанными программами (PRP)
        report = self.load_research_report()
        if not report:
            print("❌ Не удалось загрузить отчет с предсказаниями")
            return
        
        # 2. Конвертируем предсказанные программы в удобный MD формат
        print("📝 Конвертирую предсказанные программы (PRP) в MD...")
        predictions_md = self.convert_predictions_to_md(report)
        
        # 3. Находим PDF файлы со статьями для валидации
        pdf_files = self.find_pdf_files()
        if not pdf_files:
            print("❌ PDF файлы со статьями не найдены")
            return
        
        # 4. Обрабатываем каждую статью
        for pdf_path in pdf_files:
            print(f"\n📄 Валидация против: {pdf_path.name}")
            
            # Извлекаем Идеализированную Исследовательскую Программу (IRP) из статьи
            print("🔍 Извлекаю IRP (Идеализированную Исследовательскую Программу) из статьи...")
            paper_irp = self.extract_key_info_from_pdf(pdf_path)
            if not paper_irp:
                print("❌ Не удалось извлечь IRP из статьи")
                continue
            
            # Сравниваем предсказанные программы (PRP) с идеализированной программой (IRP)
            print("⚖️ Сравниваю PRP vs IRP по критериям бенчмарка...")
            result = self.validate_predictions_vs_paper(predictions_md, paper_irp)
            
            # Сохраняем детальный результат валидации
            self.save_validation_result(result, pdf_path.stem)
        
        print("\n✅ Валидация по RPPB завершена!")
        print("📊 Результаты содержат детальные метрики соответствия")
        print("🎯 Проверьте папку 'results/' для анализа качества предсказаний")


def main():
    """Главная функция"""
    try:
        validator = ReportValidator()
        validator.run_validation()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    main()