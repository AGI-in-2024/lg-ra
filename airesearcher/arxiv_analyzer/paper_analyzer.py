"""
Анализатор научных статей по чеклисту из initialtask.md
"""

import asyncio
from typing import List, Dict, Any
from openai import OpenAI

try:
    from .models import (
        PaperInfo, 
        PaperAnalysis, 
        FlatPaperAnalysis,
        PrioritizationAnalysis,
        ValidationAnalysis,
        ArchitectureAnalysis,
        KnowledgeAnalysis,
        ImplementationAnalysis,
        AnalysisScore
    )
    from .config import (
        GEMINI_API_KEY,
        GEMINI_BASE_URL,
        GEMINI_MODEL,
        ANALYSIS_TEMPERATURE,
        ANALYSIS_MAX_TOKENS,
        TASK_DESCRIPTION_PATH
    )
except ImportError:
    from models import (
        PaperInfo, 
        PaperAnalysis, 
        FlatPaperAnalysis,
        PrioritizationAnalysis,
        ValidationAnalysis,
        ArchitectureAnalysis,
        KnowledgeAnalysis,
        ImplementationAnalysis,
        AnalysisScore
    )
    from config import (
        GEMINI_API_KEY,
        GEMINI_BASE_URL,
        GEMINI_MODEL,
        ANALYSIS_TEMPERATURE,
        ANALYSIS_MAX_TOKENS,
        TASK_DESCRIPTION_PATH
    )


class PaperAnalyzer:
    """Анализатор статей по критериям из чеклиста"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=GEMINI_API_KEY,
            base_url=GEMINI_BASE_URL
        )
        self.task_description = self._load_task_description()
    
    def _load_task_description(self) -> str:
        """Загружает описание задачи"""
        try:
            with open(TASK_DESCRIPTION_PATH, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "Описание задачи не найдено"
    
    def _create_analysis_prompt(self, paper: PaperInfo) -> str:
        """Создает промпт для анализа статьи"""
        return f"""# РОЛЬ
Ты — ведущий эксперт по AI-исследованиям и научный аналитик с глубокими знаниями в области language models, multi-agent systems и автономных исследователей.

# ЗАДАЧА
Проанализируй научную статью по детальному чеклисту критериев и дай структурированную оценку её релевантности для нашей задачи построения автономного научного аналитика.

# КОНТЕКСТ НАШЕЙ ЗАДАЧИ
{self.task_description}

# АНАЛИЗИРУЕМАЯ СТАТЬЯ
**Название:** {paper.title}

**Авторы:** {', '.join(paper.authors)}

**Аннотация:** {paper.abstract}

**Категории arXiv:** {', '.join(paper.categories)}

# ИНСТРУКЦИИ ПО АНАЛИЗУ
Оцени статью по 5 ключевым категориям. Для каждого критерия дай:
- **Оценку от 1 до 5** (1 = не релевантно/отсутствует, 5 = отлично/крайне релевантно)
- **Объяснение** (2-3 предложения)
- **Доказательства** (конкретные цитаты из аннотации, если есть)

## КАТЕГОРИИ АНАЛИЗА:

### 1. ПРИОРИТИЗАЦИЯ И ГЕНЕРАЦИЯ ИДЕЙ
- **algorithm_search**: Описывает ли статья алгоритм поиска перспективных направлений? Есть ли формализация "пробелов в знаниях"?
- **relevance_justification**: Как обосновывается важность найденных направлений? Есть ли многокритериальная оценка?
- **knowledge_gaps**: Способна ли система выявлять научные противоречия и белые пятна?
- **balance_hotness_novelty**: Как балансируется популярность темы vs её новизна?

### 2. ОЦЕНКА И ВАЛИДАЦИЯ
- **benchmarks**: Есть ли стандартные бенчмарки? Как создаются новые?
- **metrics**: Какие конкретные метрики используются (Completion Rate, Correctness Score)?
- **evaluation_methodology**: Используется ли "LLM как Судья"? Как борются с bias?
- **expert_validation**: Привлекались ли люди-эксперты для валидации?

### 3. АРХИТЕКТУРА И ВЗАИМОДЕЙСТВИЕ АГЕНТОВ
- **roles_and_sops**: Описаны ли роли агентов и их стандартные процедуры?
- **communication**: Как агенты общаются? Структурированные объекты или текст?
- **memory_context**: Как решается проблема удержания контекста? Внешняя память?
- **self_correction**: Есть ли механизмы самокоррекции и агенты-советники?

### 4. РАБОТА СО ЗНАНИЯМИ
- **extraction**: Какие промпты для извлечения знаний (троек, гипотез, методов)?
- **representation**: Как хранятся знания? Граф, векторы, гибрид?
- **conflict_resolution**: Как разрешаются противоречия между источниками?

### 5. ПРАКТИЧЕСКАЯ РЕАЛИЗАЦИЯ
- **tools_frameworks**: Какие фреймворки используются (LlamaIndex, LangChain, Neo4j)?
- **open_source**: Открыт ли код? Доступны ли промпты?
- **reproducibility**: Можно ли воспроизвести результаты?

# ДОПОЛНИТЕЛЬНО
- **overall_score**: Общая оценка релевантности (0.0-1.0)
- **key_insights**: 3-5 ключевых инсайтов из статьи
- **relevance_to_task**: Как именно эта статья поможет в решении нашей задачи?

Будь критичен, но справедлив. Фокусируйся на инновационных подходах, которые можно применить в нашей системе.
"""

    async def analyze_paper(self, paper: PaperInfo) -> PaperAnalysis:
        """Анализирует одну статью"""
        prompt = self._create_analysis_prompt(paper)
        
        try:
            response = self.client.beta.chat.completions.parse(
                model=GEMINI_MODEL,
                temperature=ANALYSIS_TEMPERATURE,
                max_tokens=ANALYSIS_MAX_TOKENS,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format=FlatPaperAnalysis
            )
            
            flat_analysis = response.choices[0].message.parsed
            
            # Конвертируем плоскую модель в структурированную
            analysis = self._convert_flat_to_structured(flat_analysis, paper)
            
            return analysis
            
        except Exception as e:
            # Возвращаем базовый анализ в случае ошибки
            print(f"Ошибка анализа статьи {paper.title}: {e}")
            return self._create_default_analysis(paper)
    
    def _convert_flat_to_structured(self, flat: FlatPaperAnalysis, paper: PaperInfo) -> PaperAnalysis:
        """Конвертирует плоскую модель в структурированную для обратной совместимости"""
        
        # Создаем AnalysisScore объекты из плоских оценок
        def create_score(score: int, category: str) -> AnalysisScore:
            return AnalysisScore(
                score=score,
                explanation=f"Оценка {score}/5 в категории {category}",
                evidence="Извлечено из автоматического анализа"
            )
        
        # Собираем структурированный анализ точно по чек-листу
        prioritization = PrioritizationAnalysis(
            algorithm_search=create_score(flat.algorithm_search_score, "алгоритм поиска направлений"),
            relevance_justification=create_score(flat.relevance_justification_score, "обоснование релевантности"),
            knowledge_gaps=create_score(flat.knowledge_gaps_score, "выявление пробелов в знаниях"),
            balance_hotness_novelty=create_score(flat.balance_hotness_novelty_score, "баланс популярности/новизны")
        )
        
        validation = ValidationAnalysis(
            benchmarks=create_score(flat.benchmarks_score, "бенчмарки"),
            metrics=create_score(flat.metrics_score, "метрики"),
            evaluation_methodology=create_score(flat.evaluation_methodology_score, "методология оценки"),
            expert_validation=create_score(flat.expert_validation_score, "экспертная валидация")
        )
        
        architecture = ArchitectureAnalysis(
            roles_and_sops=create_score(flat.roles_and_sops_score, "роли и SOPs"),
            communication=create_score(flat.communication_score, "коммуникация"),
            memory_context=create_score(flat.memory_context_score, "память и контекст"),
            self_correction=create_score(flat.self_correction_score, "самокоррекция")
        )
        
        knowledge = KnowledgeAnalysis(
            extraction=create_score(flat.extraction_score, "извлечение знаний"),
            representation=create_score(flat.representation_score, "представление знаний"),
            conflict_resolution=create_score(flat.conflict_resolution_score, "разрешение конфликтов")
        )
        
        implementation = ImplementationAnalysis(
            tools_frameworks=create_score(flat.tools_frameworks_score, "инструменты и фреймворки"),
            open_source=create_score(flat.open_source_score, "открытый код"),
            reproducibility=create_score(flat.reproducibility_score, "воспроизводимость")
        )
        
        # Используем переданный paper объект вместо flat.paper_info
        return PaperAnalysis(
            paper_info=paper,
            prioritization=prioritization,
            validation=validation,
            architecture=architecture,
            knowledge=knowledge,
            implementation=implementation,
            overall_score=flat.overall_score,
            key_insights=flat.key_insights,
            relevance_to_task=flat.relevance_to_task
        )
    
    def _create_default_analysis(self, paper: PaperInfo) -> PaperAnalysis:
        """Создает базовый анализ в случае ошибки"""
        default_score = AnalysisScore(
            score=1,
            explanation="Ошибка анализа",
            evidence=None
        )
        
        return PaperAnalysis(
            paper_info=paper,
            prioritization=PrioritizationAnalysis(
                algorithm_search=default_score,
                relevance_justification=default_score,
                knowledge_gaps=default_score,
                balance_hotness_novelty=default_score
            ),
            validation=ValidationAnalysis(
                benchmarks=default_score,
                metrics=default_score,
                evaluation_methodology=default_score,
                expert_validation=default_score
            ),
            architecture=ArchitectureAnalysis(
                roles_and_sops=default_score,
                communication=default_score,
                memory_context=default_score,
                self_correction=default_score
            ),
            knowledge=KnowledgeAnalysis(
                extraction=default_score,
                representation=default_score,
                conflict_resolution=default_score
            ),
            implementation=ImplementationAnalysis(
                tools_frameworks=default_score,
                open_source=default_score,
                reproducibility=default_score
            ),
            overall_score=0.1,
            key_insights=["Анализ не удался"],
            relevance_to_task="Требуется ручной анализ"
        )
    
    async def analyze_papers_batch(self, papers: List[PaperInfo], max_concurrent: int = 3) -> List[PaperAnalysis]:
        """Анализирует список статей с ограничением на количество одновременных запросов"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_semaphore(paper: PaperInfo) -> PaperAnalysis:
            async with semaphore:
                return await self.analyze_paper(paper)
        
        # Создаем задачи для всех статей
        tasks = [analyze_with_semaphore(paper) for paper in papers]
        
        # Выполняем все задачи параллельно (с ограничением)
        analyses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        valid_analyses = []
        for i, result in enumerate(analyses):
            if isinstance(result, Exception):
                print(f"Ошибка анализа статьи {papers[i].title}: {result}")
                valid_analyses.append(self._create_default_analysis(papers[i]))
            else:
                valid_analyses.append(result)
        
        return valid_analyses
    
    def calculate_category_scores(self, analysis: PaperAnalysis) -> Dict[str, float]:
        """Вычисляет средние оценки по категориям"""
        scores = {}
        
        # Приоритизация
        prioritization_scores = [
            analysis.prioritization.algorithm_search.score,
            analysis.prioritization.relevance_justification.score,
            analysis.prioritization.knowledge_gaps.score,
            analysis.prioritization.balance_hotness_novelty.score
        ]
        scores['prioritization'] = sum(prioritization_scores) / len(prioritization_scores)
        
        # Валидация
        validation_scores = [
            analysis.validation.benchmarks.score,
            analysis.validation.metrics.score,
            analysis.validation.evaluation_methodology.score,
            analysis.validation.expert_validation.score
        ]
        scores['validation'] = sum(validation_scores) / len(validation_scores)
        
        # Архитектура
        architecture_scores = [
            analysis.architecture.roles_and_sops.score,
            analysis.architecture.communication.score,
            analysis.architecture.memory_context.score,
            analysis.architecture.self_correction.score
        ]
        scores['architecture'] = sum(architecture_scores) / len(architecture_scores)
        
        # Знания
        knowledge_scores = [
            analysis.knowledge.extraction.score,
            analysis.knowledge.representation.score,
            analysis.knowledge.conflict_resolution.score
        ]
        scores['knowledge'] = sum(knowledge_scores) / len(knowledge_scores)
        
        # Реализация
        implementation_scores = [
            analysis.implementation.tools_frameworks.score,
            analysis.implementation.open_source.score,
            analysis.implementation.reproducibility.score
        ]
        scores['implementation'] = sum(implementation_scores) / len(implementation_scores)
        
        return scores


async def main():
    """Тестовая функция"""
    # Создаем тестовую статью
    test_paper = PaperInfo(
        title="Multi-Agent Systems for Autonomous Research",
        authors=["John Doe", "Jane Smith"],
        abstract="This paper presents a novel approach to autonomous research using multi-agent systems. We propose a framework where specialized agents collaborate to identify research gaps, generate hypotheses, and validate findings through automated experiments.",
        arxiv_id="2024.0001",
        pdf_url="https://arxiv.org/pdf/2024.0001.pdf",
        published="2024-01-01",
        categories=["cs.AI", "cs.MA"]
    )
    
    analyzer = PaperAnalyzer()
    
    try:
        analysis = await analyzer.analyze_paper(test_paper)
        print(f"Анализ завершен для: {analysis.paper_info.title}")
        print(f"Общая оценка: {analysis.overall_score}")
        print(f"Ключевые инсайты: {analysis.key_insights}")
        
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 