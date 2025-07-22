"""
Pydantic модели для структурированного анализа научных статей
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class SearchStrategy(str, Enum):
    """Стратегии поиска статей"""
    BROAD_OVERVIEW = "Broad Overview"
    FOCUSED_SEARCH = "Focused Search"
    ARCHITECTURE_SEARCH = "Architecture/Methodology Search"
    BENCHMARK_SEARCH = "Benchmark/Dataset Search"
    REVIEW_SEARCH = "Review Search"


class ArxivQuery(BaseModel):
    """Модель поискового запроса для arXiv"""
    strategy: SearchStrategy
    query: str
    max_results: int = Field(default=10, description="Максимальное количество результатов")


class PaperInfo(BaseModel):
    """Базовая информация о статье"""
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: str
    pdf_url: str
    published: str
    categories: List[str]


class AnalysisScore(BaseModel):
    """Оценка по конкретному критерию"""
    score: int = Field(ge=1, le=5, description="Оценка от 1 до 5")
    explanation: str = Field(description="Объяснение оценки")
    evidence: Optional[str] = Field(default=None, description="Доказательства из текста статьи")


class PrioritizationAnalysis(BaseModel):
    """Анализ приоритизации и генерации идей"""
    algorithm_search: AnalysisScore = Field(description="Алгоритм поиска перспективных направлений")
    relevance_justification: AnalysisScore = Field(description="Обоснование релевантности")
    knowledge_gaps: AnalysisScore = Field(description="Выявление пробелов в знаниях")
    balance_hotness_novelty: AnalysisScore = Field(description="Баланс между популярностью и новизной")


class ValidationAnalysis(BaseModel):
    """Анализ оценки и валидации"""
    benchmarks: AnalysisScore = Field(description="Качество бенчмарков")
    metrics: AnalysisScore = Field(description="Конкретные метрики оценки")
    evaluation_methodology: AnalysisScore = Field(description="Методология оценки")
    expert_validation: AnalysisScore = Field(description="Привлечение экспертов")


class ArchitectureAnalysis(BaseModel):
    """Анализ архитектуры и взаимодействия агентов"""
    roles_and_sops: AnalysisScore = Field(description="Роли и стандартные процедуры")
    communication: AnalysisScore = Field(description="Коммуникация между агентами")
    memory_context: AnalysisScore = Field(description="Память и контекст")
    self_correction: AnalysisScore = Field(description="Механизмы самокоррекции")


class KnowledgeAnalysis(BaseModel):
    """Анализ работы со знаниями"""
    extraction: AnalysisScore = Field(description="Извлечение знаний")
    representation: AnalysisScore = Field(description="Представление знаний")
    conflict_resolution: AnalysisScore = Field(description="Разрешение конфликтов")


class ImplementationAnalysis(BaseModel):
    """Анализ практической реализации"""
    tools_frameworks: AnalysisScore = Field(description="Инструменты и фреймворки")
    open_source: AnalysisScore = Field(description="Открытость исходного кода")
    reproducibility: AnalysisScore = Field(description="Воспроизводимость")


class PaperAnalysis(BaseModel):
    """Полный анализ статьи по всем категориям"""
    paper_info: Optional[PaperInfo] = Field(default=None, description="Информация о статье")
    prioritization: PrioritizationAnalysis = Field(description="Анализ приоритизации и генерации идей")
    validation: ValidationAnalysis = Field(description="Анализ оценки и валидации")
    architecture: ArchitectureAnalysis = Field(description="Анализ архитектуры и взаимодействия агентов")
    knowledge: KnowledgeAnalysis = Field(description="Анализ работы со знаниями")
    implementation: ImplementationAnalysis = Field(description="Анализ практической реализации")
    overall_score: float = Field(ge=0.0, le=1.0, description="Общая оценка релевантности от 0 до 1")
    key_insights: List[str] = Field(description="Ключевые инсайты")
    relevance_to_task: str = Field(description="Объяснение релевантности к основной задаче")


class SimplePaperAnalysis(BaseModel):
    """Упрощенная модель анализа для тестирования structured output"""
    title: str = Field(description="Название статьи")
    overall_score: float = Field(ge=0.0, le=1.0, description="Общая оценка релевантности от 0 до 1")
    key_insights: List[str] = Field(description="Ключевые инсайты (максимум 3)")
    relevance_explanation: str = Field(description="Краткое объяснение релевантности")


class FlatPaperAnalysis(BaseModel):
    """Плоская модель анализа статьи точно по критериям из initialtask.md"""
    # Убираем сложное поле paper_info - оно будет добавлено отдельно
    
    # Категория 1: Приоритизация и Генерация Идей (из чек-листа)
    algorithm_search_score: int = Field(ge=1, le=5, description="Алгоритм поиска перспективных направлений: анализ частоты, динамики роста, связей в графе")
    relevance_justification_score: int = Field(ge=1, le=5, description="Обоснование релевантности: многокритериальная оценка, агент-рецензент, отличие гипотез от корреляций")
    knowledge_gaps_score: int = Field(ge=1, le=5, description="Выявление пробелов в знаниях: формализация понятий 'пробел' и 'противоречие', алгоритмы поиска")
    balance_hotness_novelty_score: int = Field(ge=1, le=5, description="Баланс популярности/новизны: между горячими переполненными темами и потенциально прорывными")
    
    # Категория 2: Оценка и Валидация (из чек-листа)
    benchmarks_score: int = Field(ge=1, le=5, description="Бенчмарки: стандартные бенчмарки (Scientist-Bench), создание собственных, используемые данные")
    metrics_score: int = Field(ge=1, le=5, description="Метрики: Completion Rate, Correctness Score, сравнение с человеческими работами")
    evaluation_methodology_score: int = Field(ge=1, le=5, description="Методология: LLM как Судья, панель моделей, борьба с bias")
    expert_validation_score: int = Field(ge=1, le=5, description="Экспертная валидация: привлечение людей-экспертов для проверки результатов")
    
    # Категория 3: Архитектура и Взаимодействие Агентов (из чек-листа)
    roles_and_sops_score: int = Field(ge=1, le=5, description="Роли и SOPs: точная специализация агентов, стандартные операционные процедуры как в MetaGPT")
    communication_score: int = Field(ge=1, le=5, description="Коммуникация: неструктурированный текст vs типизированные объекты (JSON, Pydantic)")
    memory_context_score: int = Field(ge=1, le=5, description="Память и контекст: удержание контекста в долгих задачах, внешняя память (векторная БД, граф)")
    self_correction_score: int = Field(ge=1, le=5, description="Self-Correction: механизм самокоррекции, агент-советник для рецензирования")
    
    # Категория 4: Работа со Знаниями (из чек-листа)
    extraction_score: int = Field(ge=1, le=5, description="Извлечение знаний: конкретные промпты для извлечения троек, гипотез, методов")
    representation_score: int = Field(ge=1, le=5, description="Представление знаний: графовый, векторный или гибридный подход к хранению")
    conflict_resolution_score: int = Field(ge=1, le=5, description="Разрешение конфликтов: обработка противоречащих фактов из разных статей")
    
    # Категория 5: Практическая Реализация (из чек-листа)
    tools_frameworks_score: int = Field(ge=1, le=5, description="Инструменты: конкретные фреймворки (LlamaIndex, LangChain, Neo4j, CrewAI)")
    open_source_score: int = Field(ge=1, le=5, description="Open Source: открытость кода и промптов для перенятия лучших практик")
    reproducibility_score: int = Field(ge=1, le=5, description="Воспроизводимость: возможность повторить эксперименты и результаты")
    
    # Итоговые данные
    overall_score: float = Field(ge=0.0, le=1.0, description="Общая оценка релевантности к задаче автономного исследовательского агента")
    key_insights: List[str] = Field(description="Ключевые инсайты (максимум 5)")
    relevance_to_task: str = Field(description="Объяснение релевантности к созданию автономного научного аналитика")


class RankedPaper(BaseModel):
    """Статья с рангом приоритетности"""
    analysis: PaperAnalysis = Field(description="Результат анализа статьи")
    priority_rank: int = Field(description="Ранг приоритетности")
    priority_score: float = Field(ge=0.0, le=1.0, description="Оценка приоритетности от 0 до 1")
    priority_justification: str = Field(description="Обоснование приоритетности")


class QueryGeneration(BaseModel):
    """Список сгенерированных поисковых запросов"""
    queries: List[ArxivQuery] = Field(description="Список поисковых запросов для arXiv")