import json
import requests
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm
import time
import hashlib

class PDFDownloader:
    def __init__(self, download_dir: str = "downloaded_pdfs"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
    def _safe_filename(self, paper_id: str) -> str:
        """Создает безопасное имя файла из paper_id"""
        # Убираем опасные символы и ограничиваем длину
        safe_name = "".join(c for c in paper_id if c.isalnum() or c in '-_')
        return safe_name[:50] + ".pdf"
    
    def download_pdf(self, pdf_url: str, paper_id: str) -> str:
        """Скачивает один PDF файл"""
        if not pdf_url:
            return ""
            
        filename = self._safe_filename(paper_id)
        filepath = self.download_dir / filename
        
        # Проверяем, уже скачан ли файл
        if filepath.exists() and filepath.stat().st_size > 1024:  # минимум 1KB
            return str(filepath)
        
        try:
            # Устанавливаем User-Agent для избежания блокировок
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(pdf_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Проверяем что это действительно PDF
            if response.headers.get('content-type', '').startswith('application/pdf'):
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return str(filepath)
            else:
                print(f"⚠️ {paper_id}: не PDF контент")
                return ""
                
        except Exception as e:
            print(f"⚠️ Ошибка скачивания {paper_id}: {e}")
            return ""
    
    def download_from_corpus(self, corpus_file: str, max_downloads: int = None) -> Dict[str, str]:
        """Скачивает PDF файлы из результатов harvester"""
        
        # Загружаем данные из JSON файла harvester
        with open(corpus_file, 'r', encoding='utf-8') as f:
            corpus = json.load(f)
        
        pdf_paths = {}
        download_count = 0
        
        print(f"📥 Начинаем скачивание PDF из {len(corpus)} статей...")
        
        for paper_id, paper_data in tqdm(corpus.items(), desc="Скачивание PDF"):
            # Ограничение количества загрузок
            if max_downloads and download_count >= max_downloads:
                break
                
            pdf_url = paper_data.get('pdf_url')
            if pdf_url:
                filepath = self.download_pdf(pdf_url, paper_id)
                if filepath:
                    pdf_paths[paper_id] = filepath
                    download_count += 1
                    
                # Пауза между запросами
                time.sleep(0.5)
        
        print(f"✅ Скачано {len(pdf_paths)} PDF файлов в {self.download_dir}")
        return pdf_paths
    
    def create_lcgr_format(self, corpus_file: str, pdf_paths: Dict[str, str]) -> Dict[str, Dict]:
        """Создает формат данных для lcgr.py"""
        
        # Загружаем исходные данные
        with open(corpus_file, 'r', encoding='utf-8') as f:
            corpus = json.load(f)
        
        lcgr_documents = {}
        
        for paper_id, paper_data in corpus.items():
            # Если есть PDF файл, используем его для полного текста
            if paper_id in pdf_paths:
                lcgr_documents[paper_id] = {
                    "pdf_path": pdf_paths[paper_id],
                    "year": paper_data.get('year', 2024),
                    "has_pdf": True,
                    "title": paper_data.get('title', ''),
                    "abstract": paper_data.get('abstract', '')
                }
            else:
                # Если нет PDF, используем только аннотацию
                lcgr_documents[paper_id] = {
                    "full_text": paper_data.get('abstract', ''),
                    "year": paper_data.get('year', 2024),
                    "has_pdf": False,
                    "title": paper_data.get('title', ''),
                    "abstract": paper_data.get('abstract', '')
                }
        
        return lcgr_documents

def run_pdf_pipeline(corpus_file: str, max_downloads: int = 50, download_dir: str = "downloaded_pdfs"):
    """Основная функция пайплайна скачивания PDF"""
    
    downloader = PDFDownloader(download_dir)
    
    # Скачиваем PDF файлы
    pdf_paths = downloader.download_from_corpus(corpus_file, max_downloads)
    
    # Создаем формат для lcgr.py
    lcgr_documents = downloader.create_lcgr_format(corpus_file, pdf_paths)
    
    # Сохраняем результат
    output_file = f"lcgr_ready_{Path(corpus_file).stem}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(lcgr_documents, f, ensure_ascii=False, indent=2)
    
    print(f"📄 Данные для lcgr.py сохранены в: {output_file}")
    return output_file, pdf_paths

if __name__ == '__main__':
    # Пример использования
    corpus_file = "combined_corpus.json"  # результат от harvester
    
    output_file, pdf_paths = run_pdf_pipeline(
        corpus_file=corpus_file,
        max_downloads=20,  # ограничиваем для теста
        download_dir="downloaded_pdfs"
    )
    
    print(f"✅ Готово! Скачано {len(pdf_paths)} PDF файлов") 