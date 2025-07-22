"""
Модуль для управления состоянием и отслеживания прогресса анализа
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    from .models import ArxivQuery, PaperInfo, PaperAnalysis, RankedPaper
except ImportError:
    from models import ArxivQuery, PaperInfo, PaperAnalysis, RankedPaper


@dataclass
class AnalysisSession:
    """Сессия анализа"""
    session_id: str
    timestamp: str
    task_description_hash: str
    queries: List[Dict]
    total_papers_found: int
    completed: bool = False


@dataclass
class PaperState:
    """Состояние анализа статьи"""
    arxiv_id: str
    title: str
    analysis_timestamp: str
    overall_score: float
    priority_rank: Optional[int] = None
    priority_score: Optional[float] = None
    session_id: str = ""
    # Добавляем полный анализ как словарь
    analysis_data: Optional[Dict] = None


class StateManager:
    """Менеджер состояния для отслеживания прогресса анализа"""
    
    def __init__(self, state_dir: str = "analysis_state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        
        # Файлы состояния
        self.sessions_file = self.state_dir / "sessions.json"
        self.papers_file = self.state_dir / "analyzed_papers.json"
        self.queries_cache_file = self.state_dir / "queries_cache.json"
        self.rankings_file = self.state_dir / "rankings_history.json"
        
        # Загружаем состояние
        self.sessions = self._load_sessions()
        self.analyzed_papers = self._load_analyzed_papers()
        self.queries_cache = self._load_queries_cache()
        self.rankings_history = self._load_rankings_history()
    
    def _load_sessions(self) -> List[AnalysisSession]:
        """Загружает историю сессий"""
        if not self.sessions_file.exists():
            return []
        
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [AnalysisSession(**session) for session in data]
        except Exception as e:
            print(f"Ошибка загрузки сессий: {e}")
            return []
    
    def _load_analyzed_papers(self) -> Dict[str, PaperState]:
        """Загружает информацию о проанализированных статьях"""
        if not self.papers_file.exists():
            return {}
        
        try:
            with open(self.papers_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                papers = {}
                for arxiv_id, paper_data in data.items():
                    # Поддерживаем обратную совместимость - analysis_data может отсутствовать
                    if 'analysis_data' not in paper_data:
                        paper_data['analysis_data'] = None
                    papers[arxiv_id] = PaperState(**paper_data)
                return papers
        except Exception as e:
            print(f"Ошибка загрузки проанализированных статей: {e}")
            return {}
    
    def _load_queries_cache(self) -> Dict[str, List[Dict]]:
        """Загружает кэш запросов"""
        if not self.queries_cache_file.exists():
            return {}
        
        try:
            with open(self.queries_cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки кэша запросов: {e}")
            return {}
    
    def _load_rankings_history(self) -> List[Dict]:
        """Загружает историю ранжирований"""
        if not self.rankings_file.exists():
            return []
        
        try:
            with open(self.rankings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки истории ранжирований: {e}")
            return []
    
    def _save_sessions(self):
        """Сохраняет сессии"""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(session) for session in self.sessions], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения сессий: {e}")
    
    def _save_analyzed_papers(self):
        """Сохраняет проанализированные статьи"""
        try:
            with open(self.papers_file, 'w', encoding='utf-8') as f:
                data = {arxiv_id: asdict(paper) for arxiv_id, paper in self.analyzed_papers.items()}
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения проанализированных статей: {e}")
    
    def _save_queries_cache(self):
        """Сохраняет кэш запросов"""
        try:
            with open(self.queries_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.queries_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения кэша запросов: {e}")
    
    def _save_rankings_history(self):
        """Сохраняет историю ранжирований"""
        try:
            with open(self.rankings_file, 'w', encoding='utf-8') as f:
                json.dump(self.rankings_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения истории ранжирований: {e}")
    
    def get_task_hash(self, task_description: str) -> str:
        """Вычисляет хэш описания задачи"""
        return hashlib.md5(task_description.encode('utf-8')).hexdigest()[:8]
    
    def get_cached_queries(self, task_hash: str) -> Optional[List[ArxivQuery]]:
        """Получает кэшированные запросы для задачи"""
        if task_hash in self.queries_cache:
            cached_data = self.queries_cache[task_hash]
            try:
                from .models import SearchStrategy
                queries = []
                for query_data in cached_data:
                    strategy = SearchStrategy(query_data["strategy"])
                    query = ArxivQuery(
                        strategy=strategy,
                        query=query_data["query"],
                        max_results=query_data.get("max_results", 10)
                    )
                    queries.append(query)
                return queries
            except Exception as e:
                print(f"Ошибка загрузки кэшированных запросов: {e}")
                return None
        return None
    
    def cache_queries(self, task_hash: str, queries: List[ArxivQuery]):
        """Кэширует запросы для задачи"""
        self.queries_cache[task_hash] = [
            {
                "strategy": q.strategy.value,
                "query": q.query,
                "max_results": q.max_results
            }
            for q in queries
        ]
        self._save_queries_cache()
    
    def start_session(self, task_description: str, queries: List[ArxivQuery]) -> str:
        """Начинает новую сессию анализа"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_hash = self.get_task_hash(task_description)
        
        session = AnalysisSession(
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            task_description_hash=task_hash,
            queries=[
                {"strategy": q.strategy.value, "query": q.query}
                for q in queries
            ],
            total_papers_found=0,
            completed=False
        )
        
        self.sessions.append(session)
        self._save_sessions()
        return session_id
    
    def complete_session(self, session_id: str, total_papers: int):
        """Завершает сессию"""
        for session in self.sessions:
            if session.session_id == session_id:
                session.completed = True
                session.total_papers_found = total_papers
                break
        self._save_sessions()
    
    def is_paper_analyzed(self, arxiv_id: str) -> bool:
        """Проверяет, была ли статья уже проанализирована"""
        return arxiv_id in self.analyzed_papers
    
    def get_analyzed_paper(self, arxiv_id: str) -> Optional[PaperState]:
        """Получает информацию о проанализированной статье"""
        return self.analyzed_papers.get(arxiv_id)
    
    def get_full_analysis(self, arxiv_id: str) -> Optional[PaperAnalysis]:
        """Получает полный анализ статьи, восстанавливая объект PaperAnalysis"""
        paper_state = self.analyzed_papers.get(arxiv_id)
        if not paper_state or not paper_state.analysis_data:
            return None
        
        try:
            # Восстанавливаем PaperAnalysis из сохраненных данных
            analysis_data = paper_state.analysis_data
            
            # Импортируем нужные модели
            try:
                from .models import PaperAnalysis
            except ImportError:
                from models import PaperAnalysis
            
            # Создаем объект PaperAnalysis из словаря
            if hasattr(PaperAnalysis, 'model_validate'):
                # Для Pydantic v2
                return PaperAnalysis.model_validate(analysis_data)
            else:
                # Для Pydantic v1 или других случаев
                return PaperAnalysis(**analysis_data)
                
        except Exception as e:
            print(f"Ошибка восстановления анализа для {arxiv_id}: {e}")
            return None
    
    def save_paper_analysis(self, analysis: PaperAnalysis, session_id: str):
        """Сохраняет анализ статьи"""
        # Сериализуем анализ в словарь для JSON совместимости
        analysis_dict = None
        try:
            analysis_dict = analysis.model_dump() if hasattr(analysis, 'model_dump') else asdict(analysis)
        except Exception as e:
            print(f"Предупреждение: не удалось сериализовать анализ: {e}")
        
        paper_state = PaperState(
            arxiv_id=analysis.paper_info.arxiv_id,
            title=analysis.paper_info.title,
            analysis_timestamp=datetime.now().isoformat(),
            overall_score=analysis.overall_score,
            session_id=session_id,
            analysis_data=analysis_dict
        )
        
        self.analyzed_papers[analysis.paper_info.arxiv_id] = paper_state
        self._save_analyzed_papers()
    
    def update_paper_ranking(self, ranked_paper: RankedPaper):
        """Обновляет ранжирование статьи"""
        arxiv_id = ranked_paper.analysis.paper_info.arxiv_id
        if arxiv_id in self.analyzed_papers:
            self.analyzed_papers[arxiv_id].priority_rank = ranked_paper.priority_rank
            self.analyzed_papers[arxiv_id].priority_score = ranked_paper.priority_score
            self._save_analyzed_papers()
    
    def save_ranking_session(self, ranked_papers: List[RankedPaper], session_id: str):
        """Сохраняет результаты ранжирования"""
        ranking_data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "total_papers": len(ranked_papers),
            "top_5": [
                {
                    "rank": paper.priority_rank,
                    "arxiv_id": paper.analysis.paper_info.arxiv_id,
                    "title": paper.analysis.paper_info.title,
                    "score": paper.priority_score
                }
                for paper in ranked_papers[:5]
            ]
        }
        
        self.rankings_history.append(ranking_data)
        self._save_rankings_history()
        
        # Обновляем ранжирования в проанализированных статьях
        for ranked_paper in ranked_papers:
            self.update_paper_ranking(ranked_paper)
    
    def filter_new_papers(self, papers: List[PaperInfo]) -> List[PaperInfo]:
        """Фильтрует новые (не проанализированные) статьи"""
        new_papers = []
        for paper in papers:
            if not self.is_paper_analyzed(paper.arxiv_id):
                new_papers.append(paper)
        return new_papers
    
    def get_progress_summary(self) -> Dict:
        """Возвращает сводку по прогрессу"""
        total_sessions = len(self.sessions)
        completed_sessions = len([s for s in self.sessions if s.completed])
        total_papers = len(self.analyzed_papers)
        
        # Последняя сессия
        last_session = self.sessions[-1] if self.sessions else None
        
        # Топ статьи по всем сессиям
        top_papers = sorted(
            [p for p in self.analyzed_papers.values() if p.priority_rank is not None],
            key=lambda x: x.priority_rank or 999
        )[:5]
        
        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "total_analyzed_papers": total_papers,
            "last_session": {
                "id": last_session.session_id if last_session else None,
                "timestamp": last_session.timestamp if last_session else None,
                "completed": last_session.completed if last_session else None
            } if last_session else None,
            "top_papers": [
                {
                    "rank": p.priority_rank,
                    "arxiv_id": p.arxiv_id,
                    "title": p.title,
                    "overall_score": p.overall_score
                }
                for p in top_papers
            ]
        }
    
    def print_progress_summary(self):
        """Выводит сводку прогресса"""
        summary = self.get_progress_summary()
        
        print("\n" + "="*50)
        print("📈 СВОДКА ПРОГРЕССА")
        print("="*50)
        
        print(f"📊 Сессии: {summary['completed_sessions']}/{summary['total_sessions']} завершено")
        print(f"📚 Всего проанализировано статей: {summary['total_analyzed_papers']}")
        
        if summary['last_session']:
            status = "✅ завершена" if summary['last_session']['completed'] else "⏳ в процессе"
            print(f"🕐 Последняя сессия: {summary['last_session']['id']} ({status})")
        
        if summary['top_papers']:
            print(f"\n🏆 ТОП-{len(summary['top_papers'])} СТАТЕЙ (по всем сессиям):")
            for paper in summary['top_papers']:
                print(f"   {paper['rank']}. {paper['title'][:50]}...")
                print(f"      📈 Оценка: {paper['overall_score']:.3f} | arXiv: {paper['arxiv_id']}")
        
        print("="*50)


def main():
    """Тестовая функция"""
    manager = StateManager()
    manager.print_progress_summary()


if __name__ == "__main__":
    main() 