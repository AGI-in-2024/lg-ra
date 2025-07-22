"""
ArXiv Harvester - сборщик статей с arXiv API
"""

import requests
import xml.etree.ElementTree as ET
import time
import logging
from typing import List, Optional, Dict, Tuple
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from .models import Paper
from .config import (
    ARXIV_BASE_URL,
    MAX_PAPERS_PER_QUERY,
    ARXIV_REQUEST_TIMEOUT,
    ARXIV_RATE_LIMIT_DELAY
)


logger = logging.getLogger(__name__)


class ArxivHarvester:
    """Класс для сбора статей с arXiv"""
    
    def __init__(self):
        self.base_url = ARXIV_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-Research-Analyst/1.0 (your-email@example.com)'
        })
    
    def search_papers(self, query: str, max_results: int = MAX_PAPERS_PER_QUERY) -> List[Paper]:
        """
        Ищет статьи по запросу в arXiv
        
        Args:
            query: Поисковый запрос
            max_results: Максимальное количество результатов
            
        Returns:
            Список объектов Paper
        """
        logger.info(f"Поиск статей по запросу: {query}")
        
        try:
            # Подготавливаем URL для запроса
            encoded_query = quote(query)
            url = f"{self.base_url}?search_query=all:{encoded_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
            
            # Делаем запрос к arXiv API
            response = self.session.get(url, timeout=ARXIV_REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Парсим XML ответ
            papers = self._parse_arxiv_response(response.text)
            
            logger.info(f"Найдено {len(papers)} статей")
            
            # Добавляем небольшую задержку для соблюдения rate limit
            time.sleep(ARXIV_RATE_LIMIT_DELAY)
            
            return papers
            
        except Exception as e:
            logger.error(f"Ошибка при поиске статей: {e}")
            return []
    
    def search_papers_parallel(self, queries: List[str], max_results: int = MAX_PAPERS_PER_QUERY, max_workers: int = 5) -> Dict[str, List[Paper]]:
        """
        Параллельный поиск статей по нескольким запросам
        
        Args:
            queries: Список поисковых запросов
            max_results: Максимальное количество результатов на запрос
            max_workers: Максимальное количество параллельных потоков
            
        Returns:
            Словарь {запрос: список_статей}
        """
        logger.info(f"🚀 Параллельный поиск по {len(queries)} запросам с {max_workers} потоками")
        
        results = {}
        rate_limit_lock = Lock()  # Для соблюдения rate limit
        
        def search_single_query(query: str) -> Tuple[str, List[Paper]]:
            """Поиск по одному запросу с rate limiting"""
            try:
                # Соблюдаем rate limit
                with rate_limit_lock:
                    time.sleep(ARXIV_RATE_LIMIT_DELAY)
                
                logger.info(f"🔍 Поиск по запросу: {query[:50]}...")
                
                # Подготавливаем URL для запроса
                encoded_query = quote(query)
                url = f"{self.base_url}?search_query=all:{encoded_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
                
                # Делаем запрос к arXiv API
                response = self.session.get(url, timeout=ARXIV_REQUEST_TIMEOUT)
                response.raise_for_status()
                
                # Парсим XML ответ
                papers = self._parse_arxiv_response(response.text)
                
                logger.info(f"✅ Найдено {len(papers)} статей для запроса: {query[:50]}...")
                return query, papers
                
            except Exception as e:
                logger.error(f"❌ Ошибка при поиске по запросу '{query[:50]}...': {e}")
                return query, []
        
        # Параллельное выполнение запросов
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Отправляем все задачи
            future_to_query = {
                executor.submit(search_single_query, query): query 
                for query in queries
            }
            
            # Собираем результаты по мере выполнения
            for future in as_completed(future_to_query):
                query, papers = future.result()
                results[query] = papers
        
        total_papers = sum(len(papers) for papers in results.values())
        logger.info(f"🎯 Параллельный поиск завершен! Всего найдено {total_papers} статей")
        
        return results
    
    def _parse_arxiv_response(self, xml_content: str) -> List[Paper]:
        """
        Парсит XML ответ от arXiv API
        
        Args:
            xml_content: XML контент от arXiv
            
        Returns:
            Список объектов Paper
        """
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Определяем namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            # Находим все элементы entry (статьи)
            entries = root.findall('atom:entry', ns)
            
            for entry in entries:
                paper = self._parse_entry(entry, ns)
                if paper:
                    papers.append(paper)
                    
        except ET.ParseError as e:
            logger.error(f"Ошибка парсинга XML: {e}")
        except Exception as e:
            logger.error(f"Ошибка обработки ответа arXiv: {e}")
            
        return papers
    
    def _parse_entry(self, entry: ET.Element, ns: dict) -> Optional[Paper]:
        """
        Парсит отдельную запись статьи
        
        Args:
            entry: XML элемент entry
            ns: Namespace для XML
            
        Returns:
            Объект Paper или None в случае ошибки
        """
        try:
            # Извлекаем ID статьи
            id_elem = entry.find('atom:id', ns)
            paper_id = id_elem.text.split('/')[-1] if id_elem is not None else ""
            
            # Извлекаем дату публикации
            published_elem = entry.find('atom:published', ns)
            published_date = published_elem.text[:10] if published_elem is not None else ""
            
            # Извлекаем заголовок
            title_elem = entry.find('atom:title', ns)
            title = title_elem.text.strip() if title_elem is not None else ""
            
            # Извлекаем аннотацию
            summary_elem = entry.find('atom:summary', ns)
            summary = summary_elem.text.strip() if summary_elem is not None else ""
            
            # Извлекаем авторов
            authors = []
            author_elems = entry.findall('atom:author', ns)
            for author_elem in author_elems:
                name_elem = author_elem.find('atom:name', ns)
                if name_elem is not None:
                    authors.append(name_elem.text)
            
            # Извлекаем URL
            link_elems = entry.findall('atom:link', ns)
            url = ""
            for link in link_elems:
                if link.get('title') == 'pdf':
                    url = link.get('href', '')
                    break
            
            if not url:  # Если PDF ссылка не найдена, используем основную ссылку
                for link in link_elems:
                    if link.get('rel') == 'alternate':
                        url = link.get('href', '')
                        break
            
            # Создаем объект Paper
            paper = Paper(
                id=paper_id,
                published_date=published_date,
                title=title,
                summary=summary,
                authors=authors,
                url=url
            )
            
            return paper
            
        except Exception as e:
            logger.error(f"Ошибка парсинга статьи: {e}")
            return None
    
    def harvest_multiple_queries(self, queries: List[str]) -> List[Paper]:
        """
        Собирает статьи по множественным запросам
        
        Args:
            queries: Список поисковых запросов
            
        Returns:
            Список уникальных статей
        """
        all_papers = []
        seen_ids = set()
        
        for query in queries:
            papers = self.search_papers(query)
            
            # Добавляем только уникальные статьи
            for paper in papers:
                if paper.id not in seen_ids:
                    all_papers.append(paper)
                    seen_ids.add(paper.id)
        
        logger.info(f"Собрано {len(all_papers)} уникальных статей")
        return all_papers 