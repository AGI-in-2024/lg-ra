# -*- coding: utf-8 -*-
"""
Модуль для работы с PDF файлами и кэширования
Простые классы для чтения PDF и управления кэшем
"""

import os
import json
import threading
from pathlib import Path

# Проверяем доступность PDF модуля
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    print("⚠️ google-genai не установлен для чтения PDF")
    GENAI_AVAILABLE = False

class SimplePDFReader:
    """Простой класс для чтения PDF с помощью Gemini"""
    
    def __init__(self):
        if GENAI_AVAILABLE:
            self.client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
        else:
            self.client = None
    
    def read_pdf(self, pdf_path: str) -> str:
        """Читает текст из PDF файла (устаревший метод)"""
        if not self.client:
            return "PDF reader недоступен - установите google-genai"
        
        try:
            pdf_path = Path(pdf_path)
            pdf_data = pdf_path.read_bytes()
            
            prompt = """Extract ALL text from the scientific PDF. 
            Include: introduction, methods, results, discussion, conclusion.
            DO NOT summarize - full text is needed!
            CRITICAL: All extracted text MUST be in English only."""
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                    prompt
                ]
            )
            return response.text
        except Exception as e:
            print(f"⚠️ Ошибка чтения PDF {pdf_path}: {e}")
            return ""

    def extract_concepts_from_pdf(self, pdf_path: str, paper_id: str):
        """Сразу извлекает концепты и сущности из PDF без промежуточного текста"""
        if not self.client:
            return None
        
        try:
            pdf_path = Path(pdf_path)
            pdf_data = pdf_path.read_bytes()
            
            prompt = f"""
            You are an expert in scientific research methodology and bioinformatics.
            
            TASK: Analyze the entire scientific PDF and extract its core components.
            
            IMPORTANT DISTINCTIONS:
            - Hypothesis: A testable prediction or proposed explanation (often starts with "we hypothesize", "we propose", "we test the hypothesis")
            - Method: The experimental technique or approach used (e.g., "using CRISPR", "via flow cytometry", "mass spectrometry")  
            - Result: The actual findings or observations from experiments (e.g., "we observed", "showed", "revealed")
            - Conclusion: Final interpretations or implications drawn from results (e.g., "we conclude", "this confirms")
            
            For each component, identify all mentioned biological entities:
            - Gene: SIRT1, p53, BRCA1
            - Protein: mTOR, insulin, collagen  
            - Disease: cancer, diabetes, aging
            - Compound: Rapamycin, metformin, resveratrol
            - Process: senescence, apoptosis, autophagy
            
            CRITICAL: Your response MUST be a structured JSON that follows the ExtractedKnowledge schema.
            CRITICAL: All text fields (statements, entity names) MUST be in English only.
            
            Paper ID: {paper_id}
            """
            
            # Импортируем здесь чтобы избежать циклического импорта
            from core.models import ExtractedKnowledge
            from config import llm_extractor_client
            
            # Используем прямой API Gemini для мультимодальности
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                    prompt
                ]
            )
            
            # Парсим ответ через instructor
            parsed_response = llm_extractor_client.chat.completions.create(
                messages=[{"role": "user", "content": f"Analyze this text and return structured data. CRITICAL: All text fields must be in English only:\n\n{response.text}"}],
                response_model=ExtractedKnowledge
            )
            parsed_response.paper_id = paper_id
            return parsed_response
            
        except Exception as e:
            print(f"⚠️ Ошибка извлечения концептов из PDF {pdf_path}: {e}")
            return None

class CacheManager:
    """Простой менеджер кэша для PDF текстов"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.pdf_cache_file = self.cache_dir / "pdf_texts.json"
        self.pdf_cache = self._load_cache()
        # Блокировка для потокобезопасности
        self._lock = threading.Lock()
    
    def _load_cache(self):
        """Загружает кэш из файла"""
        try:
            if self.pdf_cache_file.exists():
                with open(self.pdf_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def _save_cache(self):
        """Сохраняет кэш в файл"""
        with self._lock:
            with open(self.pdf_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.pdf_cache, f, ensure_ascii=False, indent=2)
    
    def get_pdf_text(self, pdf_path: str) -> str:
        """Получает текст PDF из кэша"""
        file_key = f"{Path(pdf_path).name}_{os.path.getmtime(pdf_path)}"
        with self._lock:
            return self.pdf_cache.get(file_key, "")
    
    def save_pdf_text(self, pdf_path: str, text: str):
        """Сохраняет текст PDF в кэш"""
        file_key = f"{Path(pdf_path).name}_{os.path.getmtime(pdf_path)}"
        with self._lock:
            self.pdf_cache[file_key] = text
        self._save_cache() 