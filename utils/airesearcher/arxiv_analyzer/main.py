"""
Основной модуль для анализа arXiv статей по чеклисту из initialtask.md
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

try:
    from .query_generator import QueryGenerator
    from .arxiv_client import ArxivClient
    from .paper_analyzer import PaperAnalyzer
    from .priority_ranker import PriorityRanker
    from .state_manager import StateManager
    from .models import ArxivQuery, PaperInfo, PaperAnalysis, RankedPaper
    from .config import DEFAULT_MAX_RESULTS
except ImportError:
    # Fallback для прямого запуска
    from query_generator import QueryGenerator
    from arxiv_client import ArxivClient
    from paper_analyzer import PaperAnalyzer
    from priority_ranker import PriorityRanker
    from state_manager import StateManager
    from models import ArxivQuery, PaperInfo, PaperAnalysis, RankedPaper
    from config import DEFAULT_MAX_RESULTS

# Импорт data_loader для работы с PDF файлами
try:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent / "lcgr"))
    from data_loader import load_documents
except ImportError:
    print("⚠️ Модуль data_loader не найден. Анализ PDF файлов будет недоступен.")
    load_documents = None


class ArxivAnalyzer:
    """Основной класс для анализа статей arXiv с поддержкой отслеживания прогресса"""
    
    def __init__(self, enable_state_tracking: bool = True, custom_output_dir: Optional[str] = None, pdf_directory: Optional[str] = None):
        self.query_generator = QueryGenerator()
        self.paper_analyzer = PaperAnalyzer()
        self.priority_ranker = PriorityRanker()
        
        # Папка с PDF файлами для анализа
        self.pdf_directory = pdf_directory or "lcgr/downloaded_pdfs/references_dlya_statiy_2025"
        
        # Менеджер состояния с улучшенной структурой путей
        self.enable_state_tracking = enable_state_tracking
        self.custom_output_dir = custom_output_dir
        
        if enable_state_tracking:
            # Используем новую структуру путей для состояния
            try:
                from .config import get_output_paths, create_output_structure
            except ImportError:
                from config import get_output_paths, create_output_structure
            
            if custom_output_dir:
                paths = get_output_paths(custom_output_dir)
            else:
                paths = get_output_paths()
            
            # Создаем структуру каталогов
            create_output_structure(paths["base"])
            
            # Инициализируем StateManager с новым путем состояния
            self.state_manager = StateManager(str(paths["state"]))
            print(f"🏗️ Инициализирована система отслеживания состояния: {paths['state']}")
        else:
            self.state_manager = None
    
    async def run_full_analysis(
        self, 
        max_papers_per_query: int = DEFAULT_MAX_RESULTS,
        max_total_papers: int = 50,
        use_llm_ranking: bool = True,
        incremental: bool = True
    ) -> Dict:
        """Запускает полный анализ: генерация запросов → поиск → анализ → ранжирование
        
        Args:
            max_papers_per_query: Максимум статей на запрос
            max_total_papers: Максимум статей всего  
            use_llm_ranking: Использовать LLM для ранжирования
            incremental: Использовать инкрементальный режим (пропускать уже проанализированные)
        """
        
        start_time = time.time()
        print("🚀 Запуск полного анализа arXiv статей...")
        
        # Показываем текущий прогресс если включено отслеживание состояния
        if self.enable_state_tracking and self.state_manager:
            self.state_manager.print_progress_summary()
        
        # Этап 0: Загрузка описания задачи для кэширования запросов  
        task_description = self.query_generator.load_task_description()
        task_hash = None
        if self.enable_state_tracking and self.state_manager:
            task_hash = self.state_manager.get_task_hash(task_description)
        
        # Этап 1: Генерация или загрузка поисковых запросов
        print("\n📝 Этап 1: Генерация поисковых запросов...")
        try:
            # Пытаемся загрузить кэшированные запросы
            queries = None
            if self.enable_state_tracking and self.state_manager and task_hash:
                queries = self.state_manager.get_cached_queries(task_hash)
                if queries:
                    print(f"♻️  Загружено {len(queries)} кэшированных запросов")
            
            # Если кэша нет, генерируем новые запросы
            if not queries:
                queries = await self.query_generator.generate_queries(max_papers_per_query)
                print(f"✅ Сгенерировано {len(queries)} новых запросов")
                
                # Кэшируем запросы
                if self.enable_state_tracking and self.state_manager and task_hash:
                    self.state_manager.cache_queries(task_hash, queries)
                    print("💾 Запросы сохранены в кэш")
            
            for i, query in enumerate(queries, 1):
                print(f"   {i}. {query.strategy.value}: {query.query}")
                
        except Exception as e:
            print(f"❌ Ошибка генерации запросов: {e}")
            return {"error": f"Ошибка генерации запросов: {e}"}
        
        # Начинаем новую сессию если включено отслеживание состояния
        session_id = None
        if self.enable_state_tracking and self.state_manager:
            session_id = self.state_manager.start_session(task_description, queries)
            print(f"📋 Начата сессия: {session_id}")
        
        # Этап 2: Поиск статей в arXiv
        print("\n🔍 Этап 2: Поиск статей в arXiv...")
        try:
            async with ArxivClient() as client:
                search_results = await client.search_multiple_queries(queries)
                
                # Собираем все статьи и убираем дубликаты
                all_papers = []
                for strategy, result in search_results.items():
                    if 'papers' in result:
                        all_papers.extend(result['papers'])
                        print(f"   {strategy}: найдено {result['count']} статей")
                
                unique_papers = client.filter_duplicates(all_papers)
                
                # Фильтруем уже проанализированные статьи если включен инкрементальный режим
                if incremental and self.enable_state_tracking and self.state_manager:
                    new_papers = self.state_manager.filter_new_papers(unique_papers)
                    already_analyzed = len(unique_papers) - len(new_papers)
                    if already_analyzed > 0:
                        print(f"♻️  Пропущено {already_analyzed} уже проанализированных статей")
                        unique_papers = new_papers
                
                # Ограничиваем количество статей
                if len(unique_papers) > max_total_papers:
                    unique_papers = unique_papers[:max_total_papers]
                    print(f"   ⚠️  Ограничено до {max_total_papers} статей")
                
                print(f"✅ К анализу: {len(unique_papers)} статей")
                
        except Exception as e:
            print(f"❌ Ошибка поиска статей: {e}")
            return {"error": f"Ошибка поиска статей: {e}"}
        
        if not unique_papers:
            if incremental and self.enable_state_tracking:
                print("ℹ️  Все найденные статьи уже проанализированы")
                # Загружаем существующие результаты
                summary = self.state_manager.get_progress_summary()
                return {"message": "Все статьи уже проанализированы", "progress_summary": summary}
            else:
                print("❌ Не найдено статей для анализа")
                return {"error": "Не найдено статей для анализа"}
        
        # Этап 3: Анализ статей по чеклисту
        print(f"\n🧠 Этап 3: Анализ {len(unique_papers)} статей по чеклисту...")
        try:
            analyses = await self.paper_analyzer.analyze_papers_batch(
                unique_papers, 
                max_concurrent=3
            )
            print(f"✅ Проанализировано {len(analyses)} статей")
            
            # Сохраняем анализы в состояние
            if self.enable_state_tracking and self.state_manager and session_id:
                for analysis in analyses:
                    self.state_manager.save_paper_analysis(analysis, session_id)
                print("💾 Анализы сохранены в состояние")
            
            # Показываем краткую статистику
            valid_analyses = [a for a in analyses if a.overall_score > 0.1]
            avg_score = sum(a.overall_score for a in valid_analyses) / len(valid_analyses) if valid_analyses else 0
            print(f"   📊 Средняя оценка релевантности: {avg_score:.2f}")
            
        except Exception as e:
            print(f"❌ Ошибка анализа статей: {e}")
            return {"error": f"Ошибка анализа статей: {e}"}
        
        # Этап 4: Ранжирование по приоритетности
        print("\n📊 Этап 4: Ранжирование статей по приоритетности...")
        
        # Если включен инкрементальный режим, комбинируем с существующими анализами
        all_analyses = analyses
        if incremental and self.enable_state_tracking and self.state_manager:
            # Получаем все существующие анализы и комбинируем с новыми
            # (для глобального ранжирования)
            print("🔄 Подготовка глобального ранжирования...")
            
            # Импорты для создания упрощенных анализов
            try:
                from .models import PaperInfo, AnalysisScore, PaperAnalysis
                from .models import PrioritizationAnalysis, ValidationAnalysis, ArchitectureAnalysis
                from .models import KnowledgeAnalysis, ImplementationAnalysis
            except ImportError:
                from models import PaperInfo, AnalysisScore, PaperAnalysis
                from models import PrioritizationAnalysis, ValidationAnalysis, ArchitectureAnalysis
                from models import KnowledgeAnalysis, ImplementationAnalysis
            
            all_analyzed_papers = []
            for arxiv_id, paper_state in self.state_manager.analyzed_papers.items():
                
                # Простой анализ на основе сохраненного состояния
                dummy_score = AnalysisScore(score=3, explanation="Из сохраненного состояния")
                dummy_analysis = PaperAnalysis(
                    paper_info=PaperInfo(
                        title=paper_state.title,
                        authors=[],
                        abstract="",
                        arxiv_id=paper_state.arxiv_id,
                        pdf_url="",
                        published="",
                        categories=[]
                    ),
                    prioritization=PrioritizationAnalysis(
                        algorithm_search=dummy_score,
                        relevance_justification=dummy_score,
                        knowledge_gaps=dummy_score,
                        balance_hotness_novelty=dummy_score
                    ),
                    validation=ValidationAnalysis(
                        benchmarks=dummy_score,
                        metrics=dummy_score,
                        evaluation_methodology=dummy_score,
                        expert_validation=dummy_score
                    ),
                    architecture=ArchitectureAnalysis(
                        roles_and_sops=dummy_score,
                        communication=dummy_score,
                        memory_context=dummy_score,
                        self_correction=dummy_score
                    ),
                    knowledge=KnowledgeAnalysis(
                        extraction=dummy_score,
                        representation=dummy_score,
                        conflict_resolution=dummy_score
                    ),
                    implementation=ImplementationAnalysis(
                        tools_frameworks=dummy_score,
                        open_source=dummy_score,
                        reproducibility=dummy_score
                    ),
                    overall_score=paper_state.overall_score,
                    key_insights=["Из сохраненного состояния"],
                    relevance_to_task="Ранее проанализированная статья"
                )
                all_analyzed_papers.append(dummy_analysis)
            
            # Комбинируем существующие и новые анализы
            all_analyses = all_analyzed_papers + analyses
            print(f"📊 Глобальное ранжирование: {len(all_analyses)} статей")
        
        try:
            if use_llm_ranking:
                ranked_papers = await self.priority_ranker.rank_papers_with_llm(all_analyses)
                print("✅ Ранжирование с LLM анализом завершено")
            else:
                ranked_papers = self.priority_ranker.rank_papers_simple(all_analyses)
                print("✅ Простое ранжирование завершено")
            
            # Сохраняем результаты ранжирования
            if self.enable_state_tracking and self.state_manager and session_id:
                self.state_manager.save_ranking_session(ranked_papers, session_id)
                print("💾 Ранжирование сохранено в состояние")
            
            # Статистика ранжирования
            summary = self.priority_ranker.get_ranking_summary(ranked_papers)
            print(f"   🏆 Топ статья: {summary['top_paper']['title'][:50]}..." if summary['top_paper'] else "")
            print(f"   📈 Средняя оценка топ-5: {summary['top_5_avg_score']:.2f}")
            
        except Exception as e:
            print(f"❌ Ошибка ранжирования: {e}")
            return {"error": f"Ошибка ранжирования: {e}"}
        
        # Завершение сессии
        if self.enable_state_tracking and self.state_manager and session_id:
            self.state_manager.complete_session(session_id, len(unique_papers))
            print(f"✅ Сессия {session_id} завершена")
        
        # Завершение
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n🎉 Анализ завершен за {duration:.1f} секунд")
        
        # Формируем результат
        result = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "duration_seconds": duration,
            "incremental_mode": incremental,
            "statistics": {
                "queries_generated": len(queries),
                "papers_found": len(unique_papers),
                "papers_analyzed": len(analyses),
                "total_papers_in_ranking": len(all_analyses),
                "valid_analyses": len([a for a in analyses if a.overall_score > 0.1])
            },
            "queries": [{"strategy": q.strategy.value, "query": q.query} for q in queries],
            "ranking_summary": summary,
            "top_papers": self._format_top_papers(ranked_papers[:10]),
            "full_results": ranked_papers  # Полные результаты для дальнейшего использования
        }
        
        return result
    
    async def run_pdf_analysis(
        self,
        max_papers: int = 50,
        use_llm_ranking: bool = True,
        use_cache: bool = True,
        max_workers: int = 4
    ) -> Dict:
        """Анализирует PDF файлы из указанной папки
        
        Args:
            max_papers: Максимум статей для анализа
            use_llm_ranking: Использовать LLM для ранжирования  
            use_cache: Использовать кэш для PDF файлов
            max_workers: Количество потоков для обработки PDF
        """
        
        if load_documents is None:
            return {"error": "Модуль data_loader не доступен"}
        
        start_time = time.time()
        print(f"🚀 Запуск анализа PDF файлов из папки: {self.pdf_directory}")
        
        # Показываем текущий прогресс если включено отслеживание состояния
        if self.enable_state_tracking and self.state_manager:
            self.state_manager.print_progress_summary()
        
        # Этап 1: Загрузка PDF файлов
        print(f"\n📁 Этап 1: Загрузка PDF файлов из {self.pdf_directory}...")
        try:
            documents = load_documents(
                data_source=self.pdf_directory,
                use_cache=use_cache,
                max_workers=max_workers
            )
            
            if not documents:
                return {"error": f"Не найдено PDF файлов в папке {self.pdf_directory}"}
            
            # Ограничиваем количество документов
            if len(documents) > max_papers:
                documents = dict(list(documents.items())[:max_papers])
                print(f"   ⚠️  Ограничено до {max_papers} файлов")
            
            print(f"✅ Загружено {len(documents)} PDF файлов")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки PDF файлов: {e}")
            return {"error": f"Ошибка загрузки PDF файлов: {e}"}
        
        # Преобразуем документы в формат PaperInfo для анализа
        papers = []
        for paper_id, doc_data in documents.items():
            # Создаем минимальную информацию о статье из PDF
            paper_info = PaperInfo(
                title=f"PDF Document: {paper_id}",
                authors=[],
                abstract=doc_data["full_text"][:1000],  # Первые 1000 символов как аннотация
                arxiv_id=paper_id,
                pdf_url="",
                published=str(doc_data.get("year", 2024)),
                categories=[]
            )
            papers.append(paper_info)
        
        # Начинаем новую сессию
        session_id = None
        if self.enable_state_tracking and self.state_manager:
            session_id = self.state_manager.start_session(f"PDF Analysis: {self.pdf_directory}", [])
            print(f"📋 Начата сессия: {session_id}")
        
        # Этап 2: Анализ документов по чеклисту
        print(f"\n🧠 Этап 2: Анализ {len(papers)} документов по чеклисту...")
        try:
            # Заменяем содержимое статей полным текстом из PDF
            for i, paper in enumerate(papers):
                paper_id = paper.arxiv_id
                if paper_id in documents:
                    # Заменяем аннотацию полным текстом
                    paper.abstract = documents[paper_id]["full_text"]
            
            analyses = await self.paper_analyzer.analyze_papers_batch(
                papers, 
                max_concurrent=3
            )
            print(f"✅ Проанализировано {len(analyses)} документов")
            
            # Сохраняем анализы в состояние
            if self.enable_state_tracking and self.state_manager and session_id:
                for analysis in analyses:
                    self.state_manager.save_paper_analysis(analysis, session_id)
                print("💾 Анализы сохранены в состояние")
            
            # Показываем краткую статистику
            valid_analyses = [a for a in analyses if a.overall_score > 0.1]
            avg_score = sum(a.overall_score for a in valid_analyses) / len(valid_analyses) if valid_analyses else 0
            print(f"   📊 Средняя оценка релевантности: {avg_score:.2f}")
            
        except Exception as e:
            print(f"❌ Ошибка анализа документов: {e}")
            return {"error": f"Ошибка анализа документов: {e}"}
        
        # Этап 3: Ранжирование по приоритетности
        print("\n📊 Этап 3: Ранжирование документов по приоритетности...")
        try:
            if use_llm_ranking:
                ranked_papers = await self.priority_ranker.rank_papers_with_llm(analyses)
                print("✅ Ранжирование с LLM анализом завершено")
            else:
                ranked_papers = self.priority_ranker.rank_papers_simple(analyses)
                print("✅ Простое ранжирование завершено")
            
            # Сохраняем результаты ранжирования
            if self.enable_state_tracking and self.state_manager and session_id:
                self.state_manager.save_ranking_session(ranked_papers, session_id)
                print("💾 Ранжирование сохранено в состояние")
            
            # Статистика ранжирования
            summary = self.priority_ranker.get_ranking_summary(ranked_papers)
            print(f"   🏆 Топ документ: {summary['top_paper']['title'][:50]}..." if summary['top_paper'] else "")
            print(f"   📈 Средняя оценка топ-5: {summary['top_5_avg_score']:.2f}")
            
        except Exception as e:
            print(f"❌ Ошибка ранжирования: {e}")
            return {"error": f"Ошибка ранжирования: {e}"}
        
        # Завершение сессии
        if self.enable_state_tracking and self.state_manager and session_id:
            self.state_manager.complete_session(session_id, len(papers))
            print(f"✅ Сессия {session_id} завершена")
        
        # Завершение
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n🎉 Анализ PDF файлов завершен за {duration:.1f} секунд")
        
        # Формируем результат
        result = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "duration_seconds": duration,
            "analysis_type": "pdf_analysis",
            "pdf_directory": self.pdf_directory,
            "statistics": {
                "pdf_files_loaded": len(documents),
                "papers_analyzed": len(analyses),
                "valid_analyses": len([a for a in analyses if a.overall_score > 0.1])
            },
            "ranking_summary": summary,
            "top_papers": self._format_top_papers(ranked_papers[:10]),
            "full_results": ranked_papers
        }
        
        return result
    
    def show_progress(self) -> Dict:
        """Показывает текущий прогресс анализа"""
        if not self.enable_state_tracking or not self.state_manager:
            return {"error": "Отслеживание состояния отключено"}
        
        return self.state_manager.get_progress_summary()
    
    def print_progress(self):
        """Выводит текущий прогресс анализа"""
        if not self.enable_state_tracking or not self.state_manager:
            print("⚠️ Отслеживание состояния отключено")
            return
        
        self.state_manager.print_progress_summary()
    
    def get_top_papers_all_time(self, limit: int = 10) -> List[Dict]:
        """Получает топ статьи за все время"""
        if not self.enable_state_tracking or not self.state_manager:
            return []
        
        # Получаем все статьи с рангами
        top_papers = sorted(
            [p for p in self.state_manager.analyzed_papers.values() if p.priority_rank is not None],
            key=lambda x: x.priority_rank or 999
        )[:limit]
        
        return [
            {
                "rank": p.priority_rank,
                "arxiv_id": p.arxiv_id,
                "title": p.title,
                "overall_score": p.overall_score,
                "priority_score": p.priority_score,
                "analysis_date": p.analysis_timestamp,
                "session_id": p.session_id
            }
            for p in top_papers
        ]
    
    def clear_state(self, confirm: bool = False):
        """Очищает сохраненное состояние (ОСТОРОЖНО!)"""
        if not confirm:
            print("⚠️ Для очистки состояния передайте confirm=True")
            return
        
        if not self.enable_state_tracking or not self.state_manager:
            print("⚠️ Отслеживание состояния отключено")
            return
        
        import shutil
        state_path = Path(self.state_manager.state_dir)
        if state_path.exists():
            shutil.rmtree(state_path)
            print(f"🗑️ Состояние очищено: {state_path}")
            
            # Пересоздаем state manager с той же структурой
            try:
                from .config import get_output_paths, create_output_structure
            except ImportError:
                from config import get_output_paths, create_output_structure
            
            if self.custom_output_dir:
                paths = get_output_paths(self.custom_output_dir)
            else:
                paths = get_output_paths()
            
            create_output_structure(paths["base"])
            self.state_manager = StateManager(str(paths["state"]))
        else:
            print("ℹ️ Состояние уже пустое")
    
    def _format_top_papers(self, top_papers: List[RankedPaper]) -> List[Dict]:
        """Форматирует топ статьи для отображения"""
        formatted = []
        
        for paper in top_papers:
            formatted.append({
                "rank": paper.priority_rank,
                "score": round(paper.priority_score, 3),
                "title": paper.analysis.paper_info.title,
                "authors": paper.analysis.paper_info.authors[:3],  # Первые 3 автора
                "arxiv_id": paper.analysis.paper_info.arxiv_id,
                "categories": paper.analysis.paper_info.categories,
                "overall_score": paper.analysis.overall_score,
                "key_insights": paper.analysis.key_insights[:3],  # Первые 3 инсайта
                "relevance": paper.analysis.relevance_to_task[:200] + "..." if len(paper.analysis.relevance_to_task) > 200 else paper.analysis.relevance_to_task,
                "justification": paper.priority_justification[:300] + "..." if len(paper.priority_justification) > 300 else paper.priority_justification,
                "pdf_url": paper.analysis.paper_info.pdf_url
            })
        
        return formatted
    
    async def save_results(self, results: Dict, filename: Optional[str] = None, custom_dir: Optional[str] = None) -> str:
        """Сохраняет результаты анализа в JSON файл с улучшенной структурой каталогов"""
        try:
            from .config import (
                get_output_paths, create_output_structure, 
                REPORT_FILENAME_TEMPLATE, TIMESTAMP_FORMAT,
                SAVE_FULL_RESULTS, BACKUP_OLD_REPORTS, MAX_BACKUPS
            )
        except ImportError:
            from config import (
                get_output_paths, create_output_structure,
                REPORT_FILENAME_TEMPLATE, TIMESTAMP_FORMAT, 
                SAVE_FULL_RESULTS, BACKUP_OLD_REPORTS, MAX_BACKUPS
            )
        
        # Создаем структуру каталогов
        if custom_dir:
            paths = get_output_paths(custom_dir)
        else:
            paths = get_output_paths()
        
        create_output_structure(paths["base"])
        
        # Определяем имя файла
        if filename is None:
            timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
            filename = REPORT_FILENAME_TEMPLATE.format(timestamp=timestamp)
        
        # Полный путь к файлу
        full_path = paths["reports"] / filename
        
        # Подготавливаем данные для сохранения
        save_data = results.copy()
        
        # Добавляем метаинформацию о сохранении
        save_data["save_metadata"] = {
            "saved_at": datetime.now().isoformat(),
            "save_path": str(full_path),
            "save_config": {
                "full_results_included": SAVE_FULL_RESULTS,
                "date_structure_used": paths["reports"].parent.name != "reports"
            }
        }
        
        # Убираем full_results если настройка отключена
        if not SAVE_FULL_RESULTS and 'full_results' in save_data:
            del save_data['full_results']
            save_data["save_metadata"]["full_results_removed"] = True
        
        # Создаем резервную копию если файл существует
        if full_path.exists() and BACKUP_OLD_REPORTS:
            self._create_backup(full_path, MAX_BACKUPS)
        
        # Сохраняем файл
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            file_size_mb = full_path.stat().st_size / (1024 * 1024)
            print(f"💾 Результаты сохранены в {full_path}")
            print(f"   📁 Размер файла: {file_size_mb:.2f} MB")
            print(f"   📂 Структура каталогов: {paths['reports'].relative_to(paths['base'])}")
            
            return str(full_path)
            
        except Exception as e:
            print(f"❌ Ошибка сохранения в {full_path}: {e}")
            return ""
    
    def _create_backup(self, file_path: Path, max_backups: int = 5):
        """Создает резервную копию существующего файла"""
        try:
            from pathlib import Path
            
            # Создаем имя резервной копии с timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
            backup_path = file_path.parent / "backups" / backup_name
            
            # Создаем каталог для резервных копий
            backup_path.parent.mkdir(exist_ok=True)
            
            # Копируем файл
            import shutil
            shutil.copy2(file_path, backup_path)
            print(f"🔄 Создана резервная копия: {backup_path.name}")
            
            # Удаляем старые резервные копии если их слишком много
            self._cleanup_old_backups(backup_path.parent, file_path.stem, max_backups)
            
        except Exception as e:
            print(f"⚠️ Ошибка создания резервной копии: {e}")
    
    def _cleanup_old_backups(self, backup_dir: Path, file_stem: str, max_backups: int):
        """Удаляет старые резервные копии, оставляя только последние max_backups"""
        try:
            # Находим все резервные копии для данного файла
            pattern = f"{file_stem}_backup_*"
            backups = list(backup_dir.glob(pattern))
            
            # Сортируем по времени создания (новые сначала)
            backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Удаляем старые копии
            for old_backup in backups[max_backups:]:
                old_backup.unlink()
                print(f"🗑️ Удалена старая резервная копия: {old_backup.name}")
                
        except Exception as e:
            print(f"⚠️ Ошибка очистки старых резервных копий: {e}")
    
    def print_summary(self, results: Dict):
        """Выводит краткую сводку результатов"""
        if 'error' in results:
            print(f"❌ Ошибка: {results['error']}")
            return
        
        print("\n" + "="*60)
        print("📋 СВОДКА АНАЛИЗА")
        print("="*60)
        
        stats = results['statistics']
        print(f"📊 Статистика:")
        print(f"   • Запросов сгенерировано: {stats['queries_generated']}")
        print(f"   • Статей найдено: {stats['papers_found']}")
        print(f"   • Статей проанализировано: {stats['papers_analyzed']}")
        print(f"   • Валидных анализов: {stats['valid_analyses']}")
        print(f"   • Время выполнения: {results['duration_seconds']:.1f} сек")
        
        print(f"\n🏆 ТОП-5 СТАТЕЙ:")
        for i, paper in enumerate(results['top_papers'][:5], 1):
            print(f"\n{i}. {paper['title'][:60]}...")
            print(f"   📈 Оценка: {paper['score']:.3f} | arXiv: {paper['arxiv_id']}")
            print(f"   👥 Авторы: {', '.join(paper['authors'])}")
            print(f"   💡 Инсайт: {paper['key_insights'][0] if paper['key_insights'] else 'Не указан'}")
        
        print("\n" + "="*60)


async def main():
    """Основная функция для тестирования"""
    
    # Пример 1: Анализ arXiv статей (оригинальная функциональность)
    print("=" * 60)
    print("📖 АНАЛИЗ ARXIV СТАТЕЙ")
    print("=" * 60)
    
    analyzer = ArxivAnalyzer()
    
    results = await analyzer.run_full_analysis(
        max_papers_per_query=5,  # Меньше для тестирования
        max_total_papers=20,     # Меньше для тестирования
        use_llm_ranking=True
    )
    
    analyzer.print_summary(results)
    
    if 'error' not in results:
        await analyzer.save_results(results, custom_dir=analyzer.custom_output_dir)
    
    print("\n" + "=" * 60)
    print("📁 АНАЛИЗ PDF ФАЙЛОВ")
    print("=" * 60)
    
    # Пример 2: Анализ PDF файлов из указанной папки
    pdf_analyzer = ArxivAnalyzer(
        pdf_directory="lcgr/downloaded_pdfs/references_dlya_statiy_2025"
    )
    
    # Запускаем анализ PDF файлов
    pdf_results = await pdf_analyzer.run_pdf_analysis(
        max_papers=10,           # Максимум PDF для анализа
        use_llm_ranking=True,
        use_cache=True,
        max_workers=4
    )
    
    # Выводим сводку
    pdf_analyzer.print_summary(pdf_results)
    
    # Сохраняем результаты
    if 'error' not in pdf_results:
        await pdf_analyzer.save_results(pdf_results, filename="pdf_analysis_results.json")


async def analyze_pdf_folder(pdf_directory: str = "lcgr/downloaded_pdfs/references_dlya_statiy_2025"):
    """Простая функция для анализа PDF файлов из указанной папки"""
    print(f"🚀 Быстрый анализ PDF файлов из папки: {pdf_directory}")
    
    analyzer = ArxivAnalyzer(pdf_directory=pdf_directory)
    
    # Запускаем анализ
    results = await analyzer.run_pdf_analysis(
        max_papers=100,
        use_llm_ranking=True,
        use_cache=True,
        max_workers=30
    )
    
    # Выводим сводку
    analyzer.print_summary(results)
    
    # Сохраняем результаты
    if 'error' not in results:
        saved_path = await analyzer.save_results(results, filename="pdf_analysis_results.json")
        print(f"💾 Результаты сохранены: {saved_path}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main()) 