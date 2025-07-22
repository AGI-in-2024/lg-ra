"""
Модуль чтения PDF документов для Extractor v2.0
Использует Gemini API для анализа PDF файлов с поддержкой vision capabilities
"""

import os
import io
import pathlib
from typing import Optional, Union, List
try:
    from google import genai
    from google.genai import types
except ImportError:
    # Fallback если google-genai не установлен
    print("Warning: google-genai не установлен. Установите: pip install google-genai")
    genai = None
    types = None

import httpx
from models import DocumentInput, ProcessedDocument, ExtractedNarrative
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.config import ExtractorConfig


class PDFReader:
    """
    Читатель PDF документов с использованием Gemini API.
    
    Поддерживает анализ PDF файлов включая текст, изображения, диаграммы,
    графики и таблицы до 1000 страниц.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        """
        Инициализация PDF читателя.
        
        Args:
            api_key: API ключ для Gemini. Если не указан, берется из переменной окружения.
            model: Название модели Gemini для использования.
        """
        if genai is None:
            raise ImportError("google-genai пакет не установлен. Установите: pip install google-genai")
            
        self.api_key = api_key or ExtractorConfig().get_api_key()
        self.model = model
        self.client = genai.Client(api_key=self.api_key)
        
    def read_pdf_from_url(self, pdf_url: str, use_file_api: bool = True) -> str:
        """
        Читает PDF из URL и извлекает текстовое содержимое.
        
        Args:
            pdf_url: URL PDF файла
            use_file_api: Использовать File API для больших файлов (рекомендуется)
            
        Returns:
            str: Извлеченное текстовое содержимое
        """
        try:
            # Скачиваем PDF
            response = httpx.get(pdf_url, timeout=60.0)
            response.raise_for_status()
            pdf_data = response.content
            
            # Проверяем размер файла
            file_size_mb = len(pdf_data) / (1024 * 1024)
            
            if file_size_mb > 20 or use_file_api:
                return self._process_large_pdf(pdf_data, source_type="url", source=pdf_url)
            else:
                return self._process_small_pdf(pdf_data)
                
        except Exception as e:
            raise Exception(f"Ошибка при чтении PDF из URL {pdf_url}: {e}")
    
    def read_pdf_from_file(self, file_path: Union[str, pathlib.Path], use_file_api: bool = True) -> str:
        """
        Читает PDF из локального файла и извлекает текстовое содержимое.
        
        Args:
            file_path: Путь к PDF файлу
            use_file_api: Использовать File API для больших файлов (рекомендуется)
            
        Returns:
            str: Извлеченное текстовое содержимое
        """
        try:
            file_path = pathlib.Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"Файл не найден: {file_path}")
            
            # Проверяем размер файла
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            if file_size_mb > 20 or use_file_api:
                return self._process_large_pdf_from_file(file_path)
            else:
                pdf_data = file_path.read_bytes()
                return self._process_small_pdf(pdf_data)
                
        except Exception as e:
            raise Exception(f"Ошибка при чтении PDF файла {file_path}: {e}")
    
    def _process_small_pdf(self, pdf_data: bytes) -> str:
        """Обрабатывает маленькие PDF файлы (< 20MB) инлайн."""
        prompt = """
        Извлеки весь текстовый контент из этого PDF документа.
        Сохрани структуру документа, включая заголовки, абзацы и разделы.
        Если есть таблицы, представь их в текстовом формате.
        Если есть изображения с текстом, извлеки текст из них.
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(
                    data=pdf_data,
                    mime_type='application/pdf',
                ),
                prompt
            ]
        )
        
        return response.text
    
    def _process_large_pdf(self, pdf_data: bytes, source_type: str, source: str) -> str:
        """Обрабатывает большие PDF файлы через File API."""
        # Загружаем PDF через File API
        doc_io = io.BytesIO(pdf_data)
        
        uploaded_file = self.client.files.upload(
            file=doc_io,
            config=dict(mime_type='application/pdf')
        )
        
        prompt = """
        Извлеки весь текстовый контент из этого PDF документа.
        Сохрани структуру документа, включая заголовки, абзацы и разделы.
        Если есть таблицы, представь их в текстовом формате.
        Если есть изображения с текстом, извлеки текст из них.
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=[uploaded_file, prompt]
        )
        
        return response.text
    
    def _process_large_pdf_from_file(self, file_path: pathlib.Path) -> str:
        """Обрабатывает большие PDF файлы из локального хранилища через File API."""
        uploaded_file = self.client.files.upload(file=file_path)
        
        prompt = """
        Извлеки весь текстовый контент из этого PDF документа.
        Сохрани структуру документа, включая заголовки, абзацы и разделы.
        Если есть таблицы, представь их в текстовом формате.
        Если есть изображения с текстом, извлеки текст из них.
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=[uploaded_file, prompt]
        )
        
        return response.text
    
    def extract_scientific_narrative_from_pdf_url(self, pdf_url: str, source_id: Optional[str] = None) -> ProcessedDocument:
        """
        Извлекает научную нарративу из PDF по URL.
        
        Args:
            pdf_url: URL PDF файла
            source_id: Идентификатор документа (если не указан, генерируется из URL)
            
        Returns:
            ProcessedDocument: Документ с извлеченной научной нарративой
        """
        if not source_id:
            source_id = f"pdf_url_{hash(pdf_url)}"
        
        # Читаем PDF и извлекаем содержимое
        content = self.read_pdf_from_url(pdf_url)
        
        # Используем специальный промпт для извлечения научной структуры
        extracted_narrative = self._extract_narrative_from_content(content)
        
        return ProcessedDocument(
            source_id=source_id,
            source_url=pdf_url,
            scientific_narrative=extracted_narrative.scientific_narrative
        )
    
    def extract_scientific_narrative_from_pdf_file(self, file_path: Union[str, pathlib.Path], 
                                                  source_id: Optional[str] = None) -> ProcessedDocument:
        """
        Извлекает научную нарративу из локального PDF файла.
        
        Args:
            file_path: Путь к PDF файлу
            source_id: Идентификатор документа (если не указан, генерируется из имени файла)
            
        Returns:
            ProcessedDocument: Документ с извлеченной научной нарративой
        """
        file_path = pathlib.Path(file_path)
        
        if not source_id:
            source_id = f"pdf_file_{file_path.stem}"
        
        # Читаем PDF и извлекаем содержимое
        content = self.read_pdf_from_file(file_path)
        
        # Используем специальный промпт для извлечения научной структуры
        extracted_narrative = self._extract_narrative_from_content(content)
        
        return ProcessedDocument(
            source_id=source_id,
            source_url=f"file://{file_path.absolute()}",
            scientific_narrative=extracted_narrative.scientific_narrative
        )
    
    def _extract_narrative_from_content(self, content: str) -> ExtractedNarrative:
        """
        Извлекает научную нарративу из текстового содержимого.
        
        Args:
            content: Текстовое содержимое документа
            
        Returns:
            ExtractedNarrative: Извлеченная научная нарратива
        """
        system_prompt = """
        Роль: Ты — эксперт в методологии науки и анализе научных текстов. 
        Твоя задача — анализировать научные документы и деконструировать их на 
        фундаментальные логические компоненты научного процесса.
        
        Задача: Внимательно прочитай предоставленный научный текст. 
        Разбей содержание на отдельные научные утверждения и классифицируй каждое по типу:
        
        1. **Hypothesis** - Утверждения, которые авторы ставят под вопрос или собираются проверить
        2. **Method** - Описание использованных техник, технологий, оборудования или протоколов
        3. **Result** - Прямое, объективное изложение полученных данных, часто с количественными показателями
        4. **Conclusion** - Интерпретация результатов авторами, их главные выводы
        5. **Dataset** - Явное упоминание использованного набора данных или источника данных
        6. **Comment** - Важные фоновые утверждения или наблюдения, контекст
        
        Для каждого утверждения также извлеки все структурированные факты в виде троек "субъект-предикат-объект".
        
        Важно: Будь точным и извлекай только то, что явно указано в тексте. Не добавляй интерпретации.
        """
        
        user_prompt = f"""
        Анализируй следующий научный документ и извлеки структурированную научную нарративу:
        
        {content}
        
        Извлеки все научные утверждения, классифицируй их по типам и выдели knowledge triples для каждого утверждения.
        """
        
        # Используем OpenAI compatibility API для structured output
        from openai import OpenAI
        
        openai_client = OpenAI(
            api_key=self.api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        
        completion = openai_client.beta.chat.completions.parse(
            model="gemini-2.0-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=ExtractedNarrative,
            temperature=0.1
        )
        
        result = completion.choices[0].message.parsed
        if result is None:
            # Возвращаем пустую нарративу если парсинг не удался
            return ExtractedNarrative(scientific_narrative=[])
        
        return result
    
    def summarize_pdf(self, pdf_source: Union[str, pathlib.Path], is_url: bool = False) -> str:
        """
        Создает краткое резюме PDF документа.
        
        Args:
            pdf_source: URL или путь к PDF файлу
            is_url: True если pdf_source это URL, False если локальный файл
            
        Returns:
            str: Краткое резюме документа
        """
        if is_url:
            content = self.read_pdf_from_url(str(pdf_source))
        else:
            content = self.read_pdf_from_file(pdf_source)
        
        summary_prompt = """
        Создай краткое резюме этого научного документа на русском языке.
        Включи:
        1. Основную тему исследования
        2. Ключевые методы
        3. Главные результаты
        4. Основные выводы
        
        Резюме должно быть не более 200 слов.
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=[summary_prompt + "\n\n" + content]
        )
        
        return response.text
    
    def compare_multiple_pdfs(self, pdf_sources: List[Union[str, pathlib.Path]], 
                            is_urls: List[bool], comparison_prompt: str) -> str:
        """
        Сравнивает несколько PDF документов.
        
        Args:
            pdf_sources: Список URL или путей к PDF файлам
            is_urls: Список булевых значений, указывающих какие источники являются URL
            comparison_prompt: Промпт для сравнения
            
        Returns:
            str: Результат сравнения
        """
        if len(pdf_sources) != len(is_urls):
            raise ValueError("Количество источников должно совпадать с количеством флагов is_url")
        
        # Загружаем все PDF файлы
        uploaded_files = []
        
        for pdf_source, is_url in zip(pdf_sources, is_urls):
            if is_url:
                response = httpx.get(str(pdf_source))
                pdf_data = io.BytesIO(response.content)
                uploaded_file = self.client.files.upload(
                    file=pdf_data,
                    config=dict(mime_type='application/pdf')
                )
            else:
                uploaded_file = self.client.files.upload(file=pathlib.Path(pdf_source))
            
            uploaded_files.append(uploaded_file)
        
        # Создаем контент для сравнения
        contents = uploaded_files + [comparison_prompt]
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents
        )
        
        return response.text


def main():
    """Пример использования PDF читателя."""
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF Reader - Чтение и анализ PDF документов")
    parser.add_argument("--pdf", "-p", required=True, help="Путь к PDF файлу или URL")
    parser.add_argument("--url", action="store_true", help="Указывает что pdf является URL")
    parser.add_argument("--action", "-a", choices=["read", "summarize", "extract"], 
                       default="read", help="Действие: read, summarize или extract")
    parser.add_argument("--output", "-o", help="Файл для сохранения результата")
    
    args = parser.parse_args()
    
    # Создаем PDF читатель
    reader = PDFReader()
    
    try:
        if args.action == "read":
            if args.url:
                content = reader.read_pdf_from_url(args.pdf)
            else:
                content = reader.read_pdf_from_file(args.pdf)
            
            print("=== Содержимое PDF ===")
            print(content)
            
        elif args.action == "summarize":
            summary = reader.summarize_pdf(args.pdf, is_url=args.url)
            
            print("=== Резюме PDF ===")
            print(summary)
            
        elif args.action == "extract":
            if args.url:
                result = reader.extract_scientific_narrative_from_pdf_url(args.pdf)
            else:
                result = reader.extract_scientific_narrative_from_pdf_file(args.pdf)
            
            print("=== Извлеченная научная нарратива ===")
            print(f"Документ ID: {result.source_id}")
            print(f"Утверждений: {len(result.scientific_narrative)}")
            
            for i, statement in enumerate(result.scientific_narrative, 1):
                print(f"\n{i}. Тип: {statement.statement_type}")
                print(f"   Содержание: {statement.statement_content}")
                if statement.knowledge_triples:
                    print("   Knowledge Triples:")
                    for triple in statement.knowledge_triples:
                        print(f"     - {triple.subject} -> {triple.predicate} -> {triple.object}")
        
        # Сохраняем результат если указан выходной файл
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                if args.action == "extract":
                    import json
                    f.write(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
                else:
                    f.write(content if args.action == "read" else summary)
            
            print(f"\nРезультат сохранен в: {args.output}")
        
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main() 