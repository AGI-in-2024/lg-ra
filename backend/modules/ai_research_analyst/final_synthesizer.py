"""
Final Synthesizer - создатель итогового аналитического отчета
"""

import json
import logging
from typing import List
from datetime import datetime
from openai import OpenAI

from .models import RankedPaper, ResearchReport
from .config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    FINAL_SYNTHESIZER_PROMPT,
    LLM_REQUEST_TIMEOUT
)


logger = logging.getLogger(__name__)


class FinalSynthesizer:
    """Класс для создания итогового аналитического отчета"""
    
    def __init__(self):
        # Инициализируем клиент с поддержкой Gemini API
        client_kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_BASE_URL:
            client_kwargs["base_url"] = OPENAI_BASE_URL
        
        self.client = OpenAI(**client_kwargs)
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self) -> str:
        """Загружает промпт из файла"""
        try:
            with open(FINAL_SYNTHESIZER_PROMPT, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Файл промпта не найден: {FINAL_SYNTHESIZER_PROMPT}")
            return ""
    
    def create_report(self, research_topic: str, top_papers: List[RankedPaper], total_analyzed: int) -> str:
        """
        Создает итоговый аналитический отчет
        
        Args:
            research_topic: Тема исследования
            top_papers: Список топ статей для анализа
            total_analyzed: Общее количество проанализированных статей
            
        Returns:
            Markdown-форматированный отчет
        """
        logger.info(f"Создание итогового отчета по {len(top_papers)} статьям")
        
        try:
            # Подготавливаем данные о статьях для промпта
            papers_data = []
            for paper in top_papers:
                papers_data.append({
                    "title": paper.title,
                    "authors": paper.authors,
                    "published_date": paper.published_date,
                    "score": paper.score,
                    "justification": paper.justification,
                    "summary": paper.summary[:200] + "..." if len(paper.summary) > 200 else paper.summary
                })
            
            papers_json = json.dumps(papers_data, ensure_ascii=False, indent=2)
            
            # Форматируем промпт
            prompt = self.prompt_template.format(
                research_topic=research_topic,
                top_papers=papers_json
            )
            
            # Вызываем LLM для создания отчета
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=OPENAI_TEMPERATURE,
                timeout=LLM_REQUEST_TIMEOUT
            )
            
            report_content = response.choices[0].message.content
            
            # Добавляем метаинформацию к отчету
            metadata = self._create_metadata(research_topic, len(top_papers), total_analyzed)
            
            final_report = f"{metadata}\n\n{report_content}"
            
            logger.info("Итоговый отчет создан успешно")
            return final_report
            
        except Exception as e:
            logger.error(f"Ошибка при создании отчета: {e}")
            return self._create_fallback_report(research_topic, top_papers, total_analyzed)
    
    def _create_metadata(self, research_topic: str, top_papers_count: int, total_analyzed: int) -> str:
        """Создает метаинформацию для отчета"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        metadata = f"""# AI Research Analyst Report

**Тема исследования:** {research_topic}
**Дата создания:** {timestamp}
**Проанализировано статей:** {total_analyzed}
**Топ статей в отчете:** {top_papers_count}

---"""
        
        return metadata
    
    def _create_fallback_report(self, research_topic: str, top_papers: List[RankedPaper], total_analyzed: int) -> str:
        """Создает базовый отчет в случае ошибки LLM"""
        logger.warning("Создается fallback отчет")
        
        metadata = self._create_metadata(research_topic, len(top_papers), total_analyzed)
        
        papers_list = "\n".join([
            f"**{i+1}. {paper.title}** (Оценка: {paper.score})\n"
            f"   - Авторы: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}\n"
            f"   - Дата: {paper.published_date}\n"
            f"   - Обоснование: {paper.justification}\n"
            for i, paper in enumerate(top_papers[:10])
        ])
        
        fallback_content = f"""
## Топ статей по релевантности

{papers_list}

## Примечание
Данный отчет создан в автоматическом режиме из-за ошибки в системе анализа. 
Рекомендуется ручная проверка результатов.
"""
        
        return f"{metadata}\n{fallback_content}"
    
    def create_research_report_object(self, research_topic: str, top_papers: List[RankedPaper], 
                                    total_analyzed: int, report_content: str) -> ResearchReport:
        """
        Создает объект ResearchReport
        
        Args:
            research_topic: Тема исследования  
            top_papers: Топ статей
            total_analyzed: Общее количество проанализированных статей
            report_content: Содержание отчета
            
        Returns:
            Объект ResearchReport
        """
        return ResearchReport(
            topic=research_topic,
            total_papers_analyzed=total_analyzed,
            top_papers=top_papers,
            clusters=[],  # TODO: Добавить кластеризацию в будущих версиях
            recommendations=report_content,
            generated_at=datetime.now()
        ) 