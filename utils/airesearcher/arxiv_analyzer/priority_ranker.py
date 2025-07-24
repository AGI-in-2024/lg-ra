"""
Модуль для ранжирования статей по приоритетности
"""

import asyncio
from typing import List, Dict, Tuple
from openai import OpenAI

try:
    from .models import PaperAnalysis, RankedPaper
    from .config import (
        GEMINI_API_KEY,
        GEMINI_BASE_URL,
        GEMINI_MODEL,
        ANALYSIS_TEMPERATURE,
        CATEGORY_WEIGHTS
    )
except ImportError:
    from models import PaperAnalysis, RankedPaper
    from config import (
        GEMINI_API_KEY,
        GEMINI_BASE_URL,
        GEMINI_MODEL,
        ANALYSIS_TEMPERATURE,
        CATEGORY_WEIGHTS
    )


class PriorityRanker:
    """Ранжировщик статей по приоритетности"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=GEMINI_API_KEY,
            base_url=GEMINI_BASE_URL
        )
    
    def calculate_weighted_score(self, analysis: PaperAnalysis) -> float:
        """Вычисляет взвешенную оценку статьи"""
        scores = {}
        
        # Приоритизация (25%)
        prioritization_scores = [
            analysis.prioritization.algorithm_search.score,
            analysis.prioritization.relevance_justification.score,
            analysis.prioritization.knowledge_gaps.score,
            analysis.prioritization.balance_hotness_novelty.score
        ]
        scores['prioritization'] = sum(prioritization_scores) / len(prioritization_scores)
        
        # Валидация (20%)
        validation_scores = [
            analysis.validation.benchmarks.score,
            analysis.validation.metrics.score,
            analysis.validation.evaluation_methodology.score,
            analysis.validation.expert_validation.score
        ]
        scores['validation'] = sum(validation_scores) / len(validation_scores)
        
        # Архитектура (25%)
        architecture_scores = [
            analysis.architecture.roles_and_sops.score,
            analysis.architecture.communication.score,
            analysis.architecture.memory_context.score,
            analysis.architecture.self_correction.score
        ]
        scores['architecture'] = sum(architecture_scores) / len(architecture_scores)
        
        # Знания (15%)
        knowledge_scores = [
            analysis.knowledge.extraction.score,
            analysis.knowledge.representation.score,
            analysis.knowledge.conflict_resolution.score
        ]
        scores['knowledge'] = sum(knowledge_scores) / len(knowledge_scores)
        
        # Реализация (15%)
        implementation_scores = [
            analysis.implementation.tools_frameworks.score,
            analysis.implementation.open_source.score,
            analysis.implementation.reproducibility.score
        ]
        scores['implementation'] = sum(implementation_scores) / len(implementation_scores)
        
        # Вычисляем взвешенную оценку
        weighted_score = 0.0
        for category, weight in CATEGORY_WEIGHTS.items():
            weighted_score += scores[category] * weight
        
        # Нормализуем к диапазону 0-1 (так как исходные оценки от 1 до 5)
        normalized_score = (weighted_score - 1) / 4
        
        # Комбинируем с overall_score из анализа
        final_score = (normalized_score * 0.7) + (analysis.overall_score * 0.3)
        
        return min(1.0, max(0.0, final_score))
    
    def rank_papers_simple(self, analyses: List[PaperAnalysis]) -> List[RankedPaper]:
        """Простое ранжирование на основе взвешенных оценок"""
        # Вычисляем оценки и сортируем
        scored_papers = []
        for analysis in analyses:
            score = self.calculate_weighted_score(analysis)
            scored_papers.append((analysis, score))
        
        # Сортируем по убыванию оценки
        scored_papers.sort(key=lambda x: x[1], reverse=True)
        
        # Создаем RankedPaper объекты
        ranked_papers = []
        for rank, (analysis, score) in enumerate(scored_papers, 1):
            justification = self._create_simple_justification(analysis, score, rank)
            
            ranked_paper = RankedPaper(
                analysis=analysis,
                priority_rank=rank,
                priority_score=score,
                priority_justification=justification
            )
            ranked_papers.append(ranked_paper)
        
        return ranked_papers
    
    def _create_simple_justification(self, analysis: PaperAnalysis, score: float, rank: int) -> str:
        """Создает простое обоснование ранга"""
        category_scores = {}
        
        # Вычисляем оценки по категориям
        prioritization_avg = sum([
            analysis.prioritization.algorithm_search.score,
            analysis.prioritization.relevance_justification.score,
            analysis.prioritization.knowledge_gaps.score,
            analysis.prioritization.balance_hotness_novelty.score
        ]) / 4
        
        validation_avg = sum([
            analysis.validation.benchmarks.score,
            analysis.validation.metrics.score,
            analysis.validation.evaluation_methodology.score,
            analysis.validation.expert_validation.score
        ]) / 4
        
        architecture_avg = sum([
            analysis.architecture.roles_and_sops.score,
            analysis.architecture.communication.score,
            analysis.architecture.memory_context.score,
            analysis.architecture.self_correction.score
        ]) / 4
        
        # Находим сильные стороны
        strengths = []
        if prioritization_avg >= 4.0:
            strengths.append("отличные методы приоритизации")
        if validation_avg >= 4.0:
            strengths.append("сильная валидация")
        if architecture_avg >= 4.0:
            strengths.append("продвинутая архитектура")
        
        justification = f"Ранг {rank} (оценка: {score:.2f}). "
        
        if strengths:
            justification += f"Сильные стороны: {', '.join(strengths)}. "
        
        if analysis.overall_score > 0.7:
            justification += "Высокая релевантность к нашей задаче."
        elif analysis.overall_score > 0.4:
            justification += "Умеренная релевантность к нашей задаче."
        else:
            justification += "Низкая релевантность к нашей задаче."
        
        return justification
    
    async def rank_papers_with_llm(self, analyses: List[PaperAnalysis]) -> List[RankedPaper]:
        """Ранжирование с использованием LLM для более глубокого анализа"""
        # Сначала делаем простое ранжирование
        simple_ranking = self.rank_papers_simple(analyses)
        
        # Создаем промпт для LLM анализа
        ranking_prompt = self._create_ranking_prompt(simple_ranking[:10])  # Топ-10
        
        try:
            response = self.client.chat.completions.create(
                model=GEMINI_MODEL,
                temperature=ANALYSIS_TEMPERATURE,
                messages=[
                    {"role": "user", "content": ranking_prompt}
                ]
            )
            
            llm_analysis = response.choices[0].message.content
            
            # Обновляем обоснования для топ-10 на основе LLM анализа
            enhanced_ranking = self._enhance_rankings_with_llm_analysis(
                simple_ranking, llm_analysis
            )
            
            return enhanced_ranking
            
        except Exception as e:
            print(f"Ошибка LLM ранжирования: {e}")
            return simple_ranking
    
    def _create_ranking_prompt(self, top_papers: List[RankedPaper]) -> str:
        """Создает промпт для анализа ранжирования"""
        papers_summary = ""
        for paper in top_papers:
            papers_summary += f"""
**{paper.priority_rank}. {paper.analysis.paper_info.title}**
- Общая оценка: {paper.priority_score:.2f}
- Ключевые инсайты: {', '.join(paper.analysis.key_insights[:2])}
- Релевантность: {paper.analysis.relevance_to_task[:100]}...

"""
        
        return f"""# ЗАДАЧА
Проанализируй топ-10 статей по релевантности для создания автономного научного аналитика. 
Дай краткую характеристику каждой статьи и объясни, почему она важна или не важна для нашей задачи.

# СТАТЬИ ДЛЯ АНАЛИЗА
{papers_summary}

# ИНСТРУКЦИИ
1. Для каждой статьи напиши 2-3 предложения о её значимости
2. Выдели самые ценные инсайты для нашего проекта
3. Укажи, если есть статьи, которые стоит переранжировать
4. Предложи конкретные применения найденных методов

Отвечай кратко и по существу."""
    
    def _enhance_rankings_with_llm_analysis(
        self, 
        rankings: List[RankedPaper], 
        llm_analysis: str
    ) -> List[RankedPaper]:
        """Улучшает обоснования ранжирования на основе LLM анализа"""
        # Для упрощения просто добавляем LLM анализ в начало обоснования топ-статей
        enhanced = rankings.copy()
        
        for i, ranked_paper in enumerate(enhanced[:10]):
            # Добавляем prefix с результатами LLM анализа
            enhanced_justification = f"[AI-анализ]: {llm_analysis[:200]}... | {ranked_paper.priority_justification}"
            enhanced[i] = RankedPaper(
                analysis=ranked_paper.analysis,
                priority_rank=ranked_paper.priority_rank,
                priority_score=ranked_paper.priority_score,
                priority_justification=enhanced_justification
            )
        
        return enhanced
    
    def get_ranking_summary(self, ranked_papers: List[RankedPaper]) -> Dict:
        """Создает сводку по ранжированию"""
        if not ranked_papers:
            return {"total": 0, "top_5_avg_score": 0, "categories_analysis": {}}
        
        top_5 = ranked_papers[:5]
        top_5_avg = sum(paper.priority_score for paper in top_5) / len(top_5)
        
        # Анализ по категориям для топ-5
        category_analysis = {
            "prioritization": [],
            "validation": [],
            "architecture": [],
            "knowledge": [],
            "implementation": []
        }
        
        for paper in top_5:
            analysis = paper.analysis
            
            prioritization_avg = sum([
                analysis.prioritization.algorithm_search.score,
                analysis.prioritization.relevance_justification.score,
                analysis.prioritization.knowledge_gaps.score,
                analysis.prioritization.balance_hotness_novelty.score
            ]) / 4
            category_analysis["prioritization"].append(prioritization_avg)
            
            validation_avg = sum([
                analysis.validation.benchmarks.score,
                analysis.validation.metrics.score,
                analysis.validation.evaluation_methodology.score,
                analysis.validation.expert_validation.score
            ]) / 4
            category_analysis["validation"].append(validation_avg)
            
            architecture_avg = sum([
                analysis.architecture.roles_and_sops.score,
                analysis.architecture.communication.score,
                analysis.architecture.memory_context.score,
                analysis.architecture.self_correction.score
            ]) / 4
            category_analysis["architecture"].append(architecture_avg)
        
        # Средние по категориям
        categories_avg = {}
        for category, scores in category_analysis.items():
            if scores:
                categories_avg[category] = sum(scores) / len(scores)
        
        return {
            "total": len(ranked_papers),
            "top_5_avg_score": top_5_avg,
            "categories_analysis": categories_avg,
            "top_paper": {
                "title": ranked_papers[0].analysis.paper_info.title,
                "score": ranked_papers[0].priority_score,
                "key_insights": ranked_papers[0].analysis.key_insights[:3]
            } if ranked_papers else None
        }


async def main():
    """Тестовая функция"""
    # Здесь должен быть тест с реальными анализами
    print("Тест ранжировщика будет реализован в основном скрипте")


if __name__ == "__main__":
    asyncio.run(main()) 