import json
import os
from pathlib import Path
from typing import Dict

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

class SimplePDFReader:
    def __init__(self):
        if GENAI_AVAILABLE:
            self.client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
        else:
            self.client = None
    
    def read_pdf(self, pdf_path: str) -> str:
        if not self.client:
            return ""
        
        try:
            pdf_path = Path(pdf_path)
            pdf_data = pdf_path.read_bytes()
            
            prompt = "Извлеки полный текст из научной статьи. Включи все разделы: введение, методы, результаты, обсуждение, заключение."
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                    prompt
                ]
            )
            return response.text
        except:
            return ""

class CacheManager:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.pdf_cache_file = self.cache_dir / "pdf_texts.json"
        self.pdf_cache = self._load_cache()
    
    def _load_cache(self):
        try:
            if self.pdf_cache_file.exists():
                with open(self.pdf_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def _save_cache(self):
        with open(self.pdf_cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.pdf_cache, f, ensure_ascii=False, indent=2)
    
    def get_pdf_text(self, pdf_path: str) -> str:
        file_key = f"{Path(pdf_path).name}_{os.path.getmtime(pdf_path)}"
        return self.pdf_cache.get(file_key, "")
    
    def save_pdf_text(self, pdf_path: str, text: str):
        file_key = f"{Path(pdf_path).name}_{os.path.getmtime(pdf_path)}"
        self.pdf_cache[file_key] = text
        self._save_cache()

class DataProcessor:
    def __init__(self):
        self.pdf_reader = SimplePDFReader()
        self.cache = CacheManager()
    
    def process(self, pubmed_data: Dict, arxiv_data: Dict = None) -> Dict:
        unified_corpus = {}
        
        # Обрабатываем данные PubMed
        for paper_id, data in pubmed_data.items():
            unified_corpus[paper_id] = {
                "title": data["title"],
                "year": data["year"],
                "abstract": data["abstract"],
                "full_text": "",
                "source": "pubmed"
            }
        
        # Обрабатываем данные arXiv
        if arxiv_data:
            for paper_id, data in arxiv_data.items():
                pdf_path = data["pdf_path"]
                
                # Проверяем кэш
                cached_text = self.cache.get_pdf_text(pdf_path)
                if cached_text:
                    full_text = cached_text
                else:
                    full_text = self.pdf_reader.read_pdf(pdf_path)
                    if full_text:
                        self.cache.save_pdf_text(pdf_path, full_text)
                
                unified_corpus[paper_id] = {
                    "title": data["title"],
                    "year": data["year"],
                    "abstract": "",
                    "full_text": full_text,
                    "source": "arxiv"
                }
        
        return unified_corpus 