"""
Модуль 2 - Extractor v2.0
Агент деконструкции научного знания

Этот модуль извлекает структурированную научную нарративу из исследовательских документов,
используя Gemini модели через OpenAI compatibility API.
"""

import os
import json
import jsonlines
from typing import List, Optional
from openai import OpenAI
from tqdm import tqdm
from models import DocumentInput, ProcessedDocument, ExtractedNarrative

class ScientificNarrativeExtractor:
    """
    Экстрактор научной нарративы из исследовательских документов.
    
    Использует Gemini модели через OpenAI compatibility API для извлечения
    структурированных компонентов научного процесса: гипотез, методов,
    результатов и выводов.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        """
        Инициализация экстрактора.
        
        Args:
            api_key: API ключ для Gemini. Если не указан, берется из переменной окружения.
            model: Название модели Gemini для использования.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("API ключ не найден. Установите переменную окружения GEMINI_API_KEY или передайте api_key")
        
        self.model = model
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        
        # Мастер-промпт для извлечения научной нарративы
        self.system_prompt = """
Роль: Ты — эксперт в методологии науки и анализе научных текстов. Твоя задача — анализировать научные статьи и деконструировать их на фундаментальные логические компоненты научного процесса.

Задача: Внимательно прочитай предоставленный научный текст (название и аннотацию). Разбей содержание на отдельные научные утверждения и классифицируй каждое по типу:

1. **Hypothesis** - Утверждения, которые авторы ставят под вопрос или собираются проверить (например, "Мы предположили, что...", "Гипотеза состоит в том, что...")

2. **Method** - Описание использованных техник, технологий, оборудования или протоколов (например, "РНК-секвенирование было проведено на...", "Мыши были разделены на группы...")

3. **Result** - Прямое, объективное изложение полученных данных, часто с количественными показателями (например, "Наблюдалось увеличение продолжительности жизни на 15%", "Экспрессия гена X снизилась в 2 раза")

4. **Conclusion** - Интерпретация результатов авторами, их главные выводы (например, "Таким образом, наши данные свидетельствуют...", "Это подтверждает роль...")

5. **Dataset** - Явное упоминание использованного набора данных или источника данных (например, "Данные взяты из UK Biobank")

6. **Comment** - Важные фоновые утверждения или наблюдения, контекст (например, "Старение является основным фактором риска...")

Для каждого утверждения также извлеки все структурированные факты в виде троек "субъект-предикат-объект".

Важно: Будь точным и извлекай только то, что явно указано в тексте. Не добавляй интерпретации.
"""

    def extract_narrative(self, document: DocumentInput) -> ProcessedDocument:
        """
        Извлекает научную нарративу из одного документа.
        
        Args:
            document: Входной документ для обработки
            
        Returns:
            ProcessedDocument: Документ с извлеченной научной нарративой
        """
        # Формируем текст для анализа
        text_to_analyze = f"Название: {document.title}\n\nАннотация: {document.abstract}"
        if document.content:
            text_to_analyze += f"\n\nПолный текст: {document.content[:2000]}..."  # Ограничиваем длину
        
        user_prompt = f"""
Анализируй следующий научный документ и извлеки структурированную научную нарративу:

{text_to_analyze}

Извлеки все научные утверждения, классифицируй их по типам и выдели knowledge triples для каждого утверждения.
"""

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=ExtractedNarrative,
                temperature=0.1  # Низкая температура для более детерминированных результатов
            )
            
            extracted = completion.choices[0].message.parsed
            
            return ProcessedDocument(
                source_id=document.source_id,
                source_url=document.source_url,
                scientific_narrative=extracted.scientific_narrative
            )
            
        except Exception as e:
            print(f"Ошибка при обработке документа {document.source_id}: {e}")
            # Возвращаем пустой результат в случае ошибки
            return ProcessedDocument(
                source_id=document.source_id,
                source_url=document.source_url,
                scientific_narrative=[]
            )

    def process_jsonl_file(self, input_file: str, output_file: str) -> None:
        """
        Обрабатывает файл .jsonl с документами и сохраняет результаты.
        
        Args:
            input_file: Путь к входному .jsonl файлу
            output_file: Путь к выходному .jsonl файлу
        """
        processed_count = 0
        error_count = 0
        
        print(f"Начинаю обработку файла: {input_file}")
        
        with jsonlines.open(input_file, 'r') as reader, \
             jsonlines.open(output_file, 'w') as writer:
            
            # Считаем общее количество строк для прогресс-бара
            total_lines = sum(1 for _ in jsonlines.open(input_file))
            
            with tqdm(total=total_lines, desc="Обработка документов") as pbar:
                for line in jsonlines.open(input_file):
                    try:
                        # Создаем объект DocumentInput из строки JSON
                        document = DocumentInput(**line)
                        
                        # Извлекаем нарративу
                        processed_doc = self.extract_narrative(document)
                        
                        # Сохраняем результат
                        writer.write(processed_doc.model_dump())
                        processed_count += 1
                        
                    except Exception as e:
                        print(f"\nОшибка при обработке строки: {e}")
                        error_count += 1
                    
                    pbar.update(1)
        
        print(f"\nОбработка завершена:")
        print(f"Успешно обработано: {processed_count} документов")
        print(f"Ошибок: {error_count}")
        print(f"Результаты сохранены в: {output_file}")

    def process_single_document(self, title: str, abstract: str, 
                               source_id: str = "manual", 
                               source_url: Optional[str] = None) -> ProcessedDocument:
        """
        Обрабатывает отдельный документ.
        
        Args:
            title: Название документа
            abstract: Аннотация документа
            source_id: Идентификатор документа
            source_url: URL документа
            
        Returns:
            ProcessedDocument: Обработанный документ
        """
        document = DocumentInput(
            source_id=source_id,
            source_url=source_url,
            title=title,
            abstract=abstract
        )
        
        return self.extract_narrative(document)


def main():
    """Пример использования экстрактора."""
    import argparse
    from dotenv import load_dotenv
    
    # Загружаем переменные окружения
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Extractor v2.0 - Извлечение научной нарративы")
    parser.add_argument("--input", "-i", required=True, help="Путь к входному .jsonl файлу")
    parser.add_argument("--output", "-o", required=True, help="Путь к выходному .jsonl файлу")
    parser.add_argument("--model", "-m", default="gemini-2.0-flash", help="Модель Gemini для использования")
    
    args = parser.parse_args()
    
    # Создаем экстрактор
    extractor = ScientificNarrativeExtractor(model=args.model)
    
    # Обрабатываем файл
    extractor.process_jsonl_file(args.input, args.output)


if __name__ == "__main__":
    main() 