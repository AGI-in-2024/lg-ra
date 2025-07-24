# -*- coding: utf-8 -*-
"""
Модуль загрузки данных из различных источников
Простые функции для работы с PDF, JSON файлами и другими источниками
"""

import json
from pathlib import Path
from tqdm import tqdm
import concurrent.futures

from .pdf_processing import SimplePDFReader, CacheManager

def process_single_pdf(pdf_file, cache, pdf_reader):
    """Обрабатывает один PDF файл (для параллелизации)"""
    paper_id = f"PDF_{pdf_file.stem}"
    
    # Проверяем кэш
    if cache:
        cached_text = cache.get_pdf_text(str(pdf_file))
        if cached_text:
            print(f"  📁 {paper_id}: из кэша")
            return paper_id, cached_text, 2024
        else:
            print(f"  🔄 {paper_id}: читаем PDF...")
            full_text = pdf_reader.read_pdf(str(pdf_file))
            if full_text:
                cache.save_pdf_text(str(pdf_file), full_text)
            return paper_id, full_text, 2024
    else:
        full_text = pdf_reader.read_pdf(str(pdf_file))
        return paper_id, full_text, 2024

def load_harvester_data(data_path, use_cache=True, max_workers=4):
    """Загружает данные от harvester (новый формат lcgr_ready_*.json)"""
    print(f"📄 Загружаем данные от harvester: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = {}
    cache = CacheManager() if use_cache else None
    pdf_reader = SimplePDFReader()
    
    # Разделяем на PDF и только текст
    pdf_papers = [(paper_id, doc_data) for paper_id, doc_data in data.items() if doc_data.get('has_pdf')]
    text_papers = [(paper_id, doc_data) for paper_id, doc_data in data.items() if not doc_data.get('has_pdf')]
    
    print(f"📊 Найдено: {len(pdf_papers)} PDF + {len(text_papers)} только текст")
    
    # Параллельно обрабатываем PDF файлы
    if pdf_papers:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_paper = {
                executor.submit(process_single_pdf, Path(pdf_path), cache, pdf_reader): (paper_id, doc_data) 
                for paper_id, doc_data in pdf_papers
            }
            
            for future in tqdm(concurrent.futures.as_completed(future_to_paper), 
                             total=len(pdf_papers), desc="Обработка PDF файлов",
                             position=0, leave=True):
                paper_id, doc_data = future_to_paper[future]
                try:
                    _, full_text, _ = future.result()
                    if full_text:
                        documents[paper_id] = {
                            "full_text": full_text,
                            "year": doc_data.get('year', 2024)
                        }
                except Exception as e:
                    print(f"❌ Ошибка обработки PDF {paper_id}: {e}")
                    # Fallback на аннотацию
                    documents[paper_id] = {
                        "full_text": doc_data.get('abstract', ''),
                        "year": doc_data.get('year', 2024)
                    }
    
    # Добавляем документы только с текстом
    for paper_id, doc_data in text_papers:
        documents[paper_id] = {
            "full_text": doc_data.get('full_text', ''),
            "year": doc_data.get('year', 2024)
        }
    
    print(f"✅ Загружено {len(documents)} документов из harvester")
    return documents

def load_pdf_directory(data_path, use_cache=True, max_workers=4):
    """Загружает PDF файлы из папки"""
    print(f"📁 Найдена папка с PDF: {data_path}")
    
    documents = {}
    pdf_files = list(data_path.glob("*.pdf"))
    
    cache = CacheManager() if use_cache else None
    pdf_reader = SimplePDFReader()
    
    print(f"🚀 Запускаем параллельную обработку {len(pdf_files)} PDF файлов (потоков: {max_workers})")
    
    # Параллельная обработка PDF файлов
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_pdf = {
            executor.submit(process_single_pdf, pdf_file, cache, pdf_reader): pdf_file 
            for pdf_file in pdf_files
        }
        
        for future in tqdm(concurrent.futures.as_completed(future_to_pdf), 
                         total=len(pdf_files), desc="Обработка PDF файлов",
                         position=0, leave=True):
            pdf_file = future_to_pdf[future]
            try:
                paper_id, full_text, year = future.result()
                if full_text:
                    documents[paper_id] = {
                        "full_text": full_text,
                        "year": year
                    }
            except Exception as e:
                print(f"❌ Ошибка обработки {pdf_file}: {e}")
    
    print(f"✅ Загружено {len(documents)} PDF файлов")
    return documents

def load_old_json_file(data_path):
    """Загружает старый JSON файл (pubmed_corpus.json)"""
    print(f"📄 Загружаем старый JSON файл: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    converted = {}
    for paper_id, doc_data in data.items():
        converted[paper_id] = {
            "full_text": doc_data.get('abstract', doc_data.get('full_text', '')),
            "year": doc_data.get('year', 2024)
        }
    
    print(f"✅ Загружено {len(converted)} статей из JSON")
    return converted

def create_test_data():
    """Создает тестовые данные если ничего не найдено"""
    print("⚠️ Данные не найдены, используем тестовые данные")
    
    return {
        "TEST:1": {
            "full_text": "Here we test the hypothesis that SIRT1 activation extends lifespan. Using CRISPR-Cas9 as our primary method, we observed a 20% increase in lifespan in C. elegans. We conclude that SIRT1 is a key longevity gene.",
            "year": 2023
        },
        "TEST:2": {
            "full_text": "The role of mTOR in aging is well-established. We hypothesized that inhibiting mTOR with Rapamycin would reduce cellular senescence. Our results, obtained via flow cytometry, showed a significant decrease in senescent cells. This confirms the link between mTOR and senescence.",
            "year": 2022
        },
        "TEST:3": {
            "full_text": "This paper explores if SIRT1 is involved in cellular metabolism. We propose that it is a master regulator. However, our experiments using mass spectrometry did not yield conclusive results connecting it directly to glucose uptake.",
            "year": 2021
        },
        "TEST:4": {
            "full_text": "We investigated the protein landscape of senescent cells using a novel single-cell proteomics method. Our analysis revealed that mTOR signaling is consistently upregulated. We hypothesize this is a core driver of the senescent phenotype.",
            "year": 2024
        }
    }

def load_documents(data_source="downloaded_pdfs", use_cache=True, max_workers=4):
    """Главная функция загрузки документов из разных источников"""
    data_path = Path(data_source)
    
    # 1. Если это JSON файл от harvester (новый формат)
    if data_path.is_file() and data_path.suffix == '.json' and 'lcgr_ready' in data_path.name:
        return load_harvester_data(data_path, use_cache, max_workers)
    
    # 2. Если это папка с PDF файлами
    elif data_path.is_dir():
        return load_pdf_directory(data_path, use_cache, max_workers)
    
    # 3. Если это старый JSON файл (pubmed_corpus.json)
    elif data_path.is_file() and data_path.suffix == '.json':
        return load_old_json_file(data_path)
    
    # 4. Автопоиск данных в разных местах
    else:
        print(f"🔍 Автопоиск данных...")
        
        # Ищем файлы harvester (приоритет)
        harvester_files = list(Path(".").glob("lcgr_ready_*.json"))
        if harvester_files:
            latest_file = max(harvester_files, key=lambda p: p.stat().st_mtime)
            print(f"📄 Найден файл harvester: {latest_file}")
            return load_documents(str(latest_file), use_cache, max_workers)
        
        # Ищем папку с PDF
        possible_paths = [
            Path("downloaded_pdfs"),
            Path(".") / "downloaded_pdfs", 
            Path("..") / "downloaded_pdfs",
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir() and list(path.glob("*.pdf")):
                print(f"📁 Найдена папка с PDF: {path}")
                return load_documents(str(path), use_cache, max_workers)
        
        # Ищем старые JSON файлы
        old_json_files = ["pubmed_corpus.json", "arxiv_corpus.json", "combined_corpus.json"]
        for json_file in old_json_files:
            if Path(json_file).exists():
                print(f"📄 Найден JSON файл: {json_file}")
                return load_documents(json_file, use_cache, max_workers)
        
        # Если ничего не найдено - используем тестовые данные
        return create_test_data() 