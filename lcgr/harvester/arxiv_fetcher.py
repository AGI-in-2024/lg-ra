import arxiv
import os
from pathlib import Path
from typing import List, Dict

class ArXivFetcher:
    def __init__(self, download_dir: str = "downloaded_pdfs"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
    
    def fetch(self, queries: List[str], max_per_query: int = 50) -> Dict:
        papers_data = {}
        
        for query in queries:
            try:
                search = arxiv.Search(
                    query=query,
                    max_results=max_per_query,
                    sort_by=arxiv.SortCriterion.SubmittedDate
                )
                
                for result in search.results():
                    try:
                        paper_id = f"arXiv:{result.entry_id.split('/')[-1]}"
                        
                        # Извлекаем аннотацию
                        abstract = result.summary.replace('\n', ' ').strip()
                        
                        papers_data[paper_id] = {
                            "title": result.title,
                            "abstract": abstract,
                            "year": result.published.year,
                            "arxiv_url": result.entry_id,
                            "pdf_url": result.pdf_url,
                            "source": "arxiv"
                        }
                    except:
                        continue
            except:
                continue
        
        return papers_data 