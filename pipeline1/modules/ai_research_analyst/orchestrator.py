"""
Orchestrator - главный управляющий модуль AI Research Analyst
"""

import logging
from typing import List, Tuple
from tqdm import tqdm

from .models import Paper, RankedPaper
from .query_strategist import QueryStrategist
from .arxiv_harvester import ArxivHarvester
from .paper_evaluator import PaperEvaluator
from .final_synthesizer import FinalSynthesizer
from .config import TARGET_PAPER_COUNT, MIN_SCORE_THRESHOLD


logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """Главный оркестратор для управления процессом исследования"""
    
    def __init__(self):
        self.query_strategist = QueryStrategist()
        self.arxiv_harvester = ArxivHarvester()
        self.paper_evaluator = PaperEvaluator()
        self.final_synthesizer = FinalSynthesizer()
        
        self.validated_papers: List[RankedPaper] = []
        self.all_papers_analyzed: List[RankedPaper] = []
    
    def run_research_pipeline(self, research_topic: str, target_count: int = TARGET_PAPER_COUNT) -> str:
        """
        Запускает полный пайплайн исследования
        
        Args:
            research_topic: Тема исследования
            target_count: Целевое количество валидированных статей
            
        Returns:
            Итоговый отчет в формате Markdown
        """
        logger.info(f"🚀 Запуск пайплайна исследования по теме: '{research_topic}'")
        logger.info(f"🎯 Цель: {target_count} валидированных статей (порог оценки: {MIN_SCORE_THRESHOLD})")
        
        try:
            # Шаг 1: Генерация поисковых запросов
            logger.info("\n📝 Шаг 1: Генерация поисковых запросов...")
            queries = self.query_strategist.generate_queries(research_topic)
            logger.info(f"✅ Сгенерировано {len(queries)} запросов")
            
            # Шаг 2: Основной цикл сбора и оценки статей
            logger.info(f"\n🔄 Шаг 2: Основной цикл сбора и анализа...")
            self._research_loop(research_topic, queries, target_count)
            
            # Шаг 3: Создание итогового отчета
            logger.info(f"\n📊 Шаг 3: Создание итогового отчета...")
            report = self._create_final_report(research_topic)
            
            logger.info(f"✨ Пайплайн завершен успешно!")
            self._print_summary()
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в пайплайне: {e}")
            return self._create_error_report(research_topic, str(e))
    
    def _research_loop(self, research_topic: str, queries: List[str], target_count: int):
        """Параллельный цикл исследования"""
        logger.info(f"🚀 Запуск параллельного поиска по {len(queries)} запросам")
        
        with tqdm(desc="Параллельный поиск и оценка", 
                 total=target_count, 
                 unit="статей") as pbar:
            
            # Шаг 1: Параллельный поиск статей по всем запросам сразу
            logger.info(f"\n🔍 Параллельный поиск статей...")
            search_results = self.arxiv_harvester.search_papers_parallel(queries, max_workers=5)
            
            # Собираем все найденные статьи
            all_found_papers = []
            for query, papers in search_results.items():
                if papers:
                    logger.info(f"📊 Запрос '{query[:50]}...' -> {len(papers)} статей")
                    all_found_papers.extend(papers)
                else:
                    logger.warning(f"⚠️ Запрос '{query[:50]}...' -> 0 статей")
            
            if not all_found_papers:
                logger.warning("⚠️ Не найдено ни одной статьи по всем запросам")
                return
            
            logger.info(f"📈 Всего найдено {len(all_found_papers)} статей")
            
            # Шаг 2: Фильтрация дубликатов и уже проанализированных статей
            logger.info(f"\n🔧 Фильтрация дубликатов...")
            unique_papers = self._remove_duplicates(all_found_papers)
            logger.info(f"📊 После удаления дубликатов: {len(unique_papers)} статей")
            
            new_papers = self._filter_new_papers(unique_papers)
            if not new_papers:
                logger.info(f"ℹ️ Все статьи уже были проанализированы")
                return
            
            logger.info(f"📊 Новых статей для анализа: {len(new_papers)}")
            
            # Шаг 3: Параллельная оценка статей
            logger.info(f"\n📊 Параллельная оценка {len(new_papers)} статей...")
            
            # Выбираем метод оценки в зависимости от количества статей
            if len(new_papers) > 30:
                # Для большого количества используем параллельную оценку батчами
                ranked_papers = self.paper_evaluator.evaluate_papers_parallel(
                    new_papers, 
                    research_topic, 
                    batch_size=10, 
                    max_workers=3
                )
            else:
                # Для малого количества используем обычную батчевую оценку
                ranked_papers = self.paper_evaluator.evaluate_papers(new_papers, research_topic)
            
            # Шаг 4: Обновление результатов
            self.all_papers_analyzed.extend(ranked_papers)
            
            # Фильтрация валидированных статей
            newly_validated = self.paper_evaluator.filter_validated_papers(ranked_papers)
            
            if newly_validated:
                self.validated_papers.extend(newly_validated)
                # Сортируем и оставляем только лучшие
                self.validated_papers.sort(key=lambda x: x.score, reverse=True)
                self.validated_papers = self.validated_papers[:target_count * 2]  # Держим запас
                
                logger.info(f"✅ Найдено {len(newly_validated)} валидированных статей")
                pbar.update(min(len(newly_validated), target_count - pbar.n))
            else:
                logger.warning(f"⚠️ Валидированных статей не найдено")
            
            # Финальный лог состояния
            current_validated = len(self.validated_papers)
            logger.info(f"📈 Итого: {current_validated}/{target_count} валидированных статей")
        
        # Финальная сортировка и обрезка до нужного количества
        self.validated_papers.sort(key=lambda x: x.score, reverse=True)
        self.validated_papers = self.validated_papers[:target_count]
        
        # Обновляем ранги
        for rank, paper in enumerate(self.validated_papers, 1):
            paper.rank = rank
    
    def _remove_duplicates(self, papers: List[Paper]) -> List[Paper]:
        """Удаляет дубликаты статей по ID"""
        seen_ids = set()
        unique_papers = []
        
        for paper in papers:
            if paper.id not in seen_ids:
                seen_ids.add(paper.id)
                unique_papers.append(paper)
        
        return unique_papers
    
    def _filter_new_papers(self, papers: List[Paper]) -> List[Paper]:
        """Фильтрует новые статьи, исключая уже проанализированные"""
        analyzed_ids = {p.id for p in self.all_papers_analyzed}
        return [p for p in papers if p.id not in analyzed_ids]
    
    def _create_final_report(self, research_topic: str) -> str:
        """Создает итоговый отчет"""
        if not self.validated_papers:
            return self._create_no_results_report(research_topic)
        
        return self.final_synthesizer.create_report(
            research_topic=research_topic,
            top_papers=self.validated_papers,
            total_analyzed=len(self.all_papers_analyzed)
        )
    
    def _create_no_results_report(self, research_topic: str) -> str:
        """Создает отчет для случая, когда не найдено валидированных статей"""
        logger.warning("⚠️ Не найдено валидированных статей")
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""# AI Research Analyst Report

**Тема исследования:** {research_topic}
**Дата создания:** {timestamp}
**Результат:** Не найдено статей, соответствующих критериям

---

## Результаты поиска

К сожалению, в ходе анализа не было найдено статей, которые получили бы оценку выше порога {MIN_SCORE_THRESHOLD}.

**Всего проанализировано статей:** {len(self.all_papers_analyzed)}

## Рекомендации

1. Попробуйте расширить или изменить тему исследования
2. Рассмотрите возможность снижения порога оценки
3. Добавьте альтернативные ключевые слова и термины

## Топ-5 статей по оценке (даже если ниже порога)

{self._get_top_analyzed_papers_summary()}
"""
    
    def _get_top_analyzed_papers_summary(self) -> str:
        """Возвращает краткую сводку по топ-5 проанализированным статьям"""
        if not self.all_papers_analyzed:
            return "Нет проанализированных статей."
        
        top_papers = sorted(self.all_papers_analyzed, key=lambda x: x.score, reverse=True)[:5]
        
        summary = []
        for i, paper in enumerate(top_papers, 1):
            summary.append(f"{i}. **{paper.title}** (Оценка: {paper.score:.1f})")
        
        return "\n".join(summary)
    
    def _create_error_report(self, research_topic: str, error_message: str) -> str:
        """Создает отчет об ошибке"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""# AI Research Analyst Report - ОШИБКА

**Тема исследования:** {research_topic}
**Дата:** {timestamp}
**Статус:** Ошибка выполнения

---

## Ошибка

Произошла критическая ошибка при выполнении анализа:

```
{error_message}
```

**Проанализировано статей до ошибки:** {len(self.all_papers_analyzed)}
**Валидировано статей:** {len(self.validated_papers)}

Пожалуйста, проверьте конфигурацию системы и попробуйте снова.
"""
    
    def _print_summary(self):
        """Выводит итоговую сводку"""
        logger.info("\n" + "="*60)
        logger.info("📊 ИТОГОВАЯ СВОДКА")
        logger.info("="*60)
        logger.info(f"✅ Всего проанализировано статей: {len(self.all_papers_analyzed)}")
        logger.info(f"🎯 Валидированных статей: {len(self.validated_papers)}")
        logger.info(f"🏆 Топ оценка: {self.validated_papers[0].score if self.validated_papers else 0}")
        logger.info(f"📝 Средняя оценка валидированных: {sum(p.score for p in self.validated_papers) / len(self.validated_papers) if self.validated_papers else 0:.2f}")
        logger.info("="*60)
    
    def get_results(self) -> Tuple[List[RankedPaper], List[RankedPaper]]:
        """
        Возвращает результаты анализа
        
        Returns:
            Кортеж (валидированные_статьи, все_проанализированные_статьи)
        """
        return self.validated_papers, self.all_papers_analyzed 