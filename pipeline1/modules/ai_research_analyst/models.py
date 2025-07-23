"""
Модели данных для AI Research Analyst
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Paper(BaseModel):
    """Базовая модель научной статьи"""
    id: str
    published_date: str
    title: str
    summary: str
    authors: List[str]
    url: Optional[str] = None


class RankedPaper(Paper):
    """Модель статьи с оценкой релевантности"""
    rank: Optional[int] = None
    score: float
    justification: str


class SearchQuery(BaseModel):
    """Модель поискового запроса"""
    query: str
    category: Optional[str] = None
    description: Optional[str] = None


class ResearchReport(BaseModel):
    """Модель итогового аналитического отчета"""
    topic: str
    total_papers_analyzed: int
    top_papers: List[RankedPaper]
    clusters: List[dict]
    recommendations: str
    generated_at: datetime 