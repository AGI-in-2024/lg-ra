"""
Клиент для работы с arXiv API
"""

import xml.etree.ElementTree as ET
import aiohttp
import asyncio
from typing import List, Optional
from urllib.parse import quote_plus
from datetime import datetime

try:
    from .models import ArxivQuery, PaperInfo
    from .config import ARXIV_BASE_URL
except ImportError:
    from models import ArxivQuery, PaperInfo
    from config import ARXIV_BASE_URL


class ArxivClient:
    """Клиент для работы с arXiv API"""
    
    def __init__(self):
        self.base_url = ARXIV_BASE_URL
        self.session = None
    
    async def __aenter__(self):
        """Асинхронный контекст менеджер для создания сессии"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
    
    def _build_search_url(self, query: ArxivQuery) -> str:
        """Строит URL для поиска в arXiv"""
        encoded_query = quote_plus(query.query)
        url = f"{self.base_url}?search_query={encoded_query}&max_results={query.max_results}&sortBy=submittedDate&sortOrder=descending"
        return url
    
    def _parse_arxiv_response(self, xml_content: str) -> List[PaperInfo]:
        """Парсит XML ответ от arXiv API"""
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Namespaces для arXiv API
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            # Находим все entry элементы (статьи)
            entries = root.findall('atom:entry', namespaces)
            
            for entry in entries:
                try:
                    # Извлекаем основную информацию
                    title = entry.find('atom:title', namespaces)
                    title_text = title.text.strip().replace('\n', ' ') if title is not None else "Без названия"
                    
                    # Авторы
                    authors = []
                    author_elements = entry.findall('atom:author', namespaces)
                    for author in author_elements:
                        name = author.find('atom:name', namespaces)
                        if name is not None:
                            authors.append(name.text.strip())
                    
                    # Аннотация
                    summary = entry.find('atom:summary', namespaces)
                    abstract = summary.text.strip().replace('\n', ' ') if summary is not None else ""
                    
                    # arXiv ID
                    id_element = entry.find('atom:id', namespaces)
                    arxiv_id = ""
                    if id_element is not None:
                        arxiv_id = id_element.text.split('/')[-1]  # Извлекаем ID из URL
                    
                    # PDF URL
                    pdf_url = ""
                    links = entry.findall('atom:link', namespaces)
                    for link in links:
                        if link.get('type') == 'application/pdf':
                            pdf_url = link.get('href', '')
                            break
                    
                    # Дата публикации
                    published = entry.find('atom:published', namespaces)
                    published_date = published.text if published is not None else ""
                    
                    # Категории
                    categories = []
                    category_elements = entry.findall('atom:category', namespaces)
                    for cat in category_elements:
                        term = cat.get('term')
                        if term:
                            categories.append(term)
                    
                    paper = PaperInfo(
                        title=title_text,
                        authors=authors,
                        abstract=abstract,
                        arxiv_id=arxiv_id,
                        pdf_url=pdf_url,
                        published=published_date,
                        categories=categories
                    )
                    
                    papers.append(paper)
                    
                except Exception as e:
                    print(f"Ошибка парсинга статьи: {e}")
                    continue
            
        except ET.ParseError as e:
            raise ValueError(f"Ошибка парсинга XML: {e}")
        
        return papers
    
    async def search_papers(self, query: ArxivQuery) -> List[PaperInfo]:
        """Выполняет поиск статей по запросу"""
        if not self.session:
            raise RuntimeError("Сессия не инициализирована. Используйте async with.")
        
        url = self._build_search_url(query)
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    xml_content = await response.text()
                    papers = self._parse_arxiv_response(xml_content)
                    return papers
                else:
                    raise aiohttp.ClientError(f"HTTP {response.status}: {await response.text()}")
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Ошибка запроса к arXiv: {e}")
    
    async def search_multiple_queries(self, queries: List[ArxivQuery]) -> dict:
        """Выполняет поиск по нескольким запросам параллельно"""
        results = {}
        
        # Создаем задачи для параллельного выполнения
        tasks = []
        for query in queries:
            task = asyncio.create_task(self.search_papers(query))
            tasks.append((query, task))
        
        # Ждем выполнения всех задач
        for query, task in tasks:
            try:
                papers = await task
                results[query.strategy.value] = {
                    'query': query.query,
                    'papers': papers,
                    'count': len(papers)
                }
            except Exception as e:
                print(f"Ошибка поиска для стратегии {query.strategy}: {e}")
                results[query.strategy.value] = {
                    'query': query.query,
                    'papers': [],
                    'count': 0,
                    'error': str(e)
                }
        
        return results
    
    def filter_duplicates(self, all_papers: List[PaperInfo]) -> List[PaperInfo]:
        """Убирает дубликаты статей по arXiv ID"""
        seen_ids = set()
        unique_papers = []
        
        for paper in all_papers:
            if paper.arxiv_id not in seen_ids:
                seen_ids.add(paper.arxiv_id)
                unique_papers.append(paper)
        
        return unique_papers


async def main():
    """Тестовая функция для проверки клиента"""
    from .query_generator import QueryGenerator
    
    # Создаем тестовый запрос
    test_query = ArxivQuery(
        strategy="Broad Overview",
        query='ti:"multi-agent" AND abs:"language model"',
        max_results=5
    )
    
    async with ArxivClient() as client:
        try:
            papers = await client.search_papers(test_query)
            print(f"Найдено {len(papers)} статей:")
            
            for i, paper in enumerate(papers, 1):
                print(f"\n{i}. {paper.title}")
                print(f"   Авторы: {', '.join(paper.authors[:3])}...")
                print(f"   arXiv ID: {paper.arxiv_id}")
                print(f"   Категории: {', '.join(paper.categories[:3])}")
                
        except Exception as e:
            print(f"Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 