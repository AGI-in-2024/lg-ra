# -*- coding: utf-8 -*-
"""
Модели данных для системы анализа графа знаний
Простые Pydantic модели для структурирования данных
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# Типы для онтологии графа
ConceptType = Literal["Hypothesis", "Method", "Result", "Conclusion"]
EntityType = Literal["Gene", "Protein", "Disease", "Compound", "Process"]

class MentionedEntity(BaseModel):
    """Биологическая сущность упомянутая в тексте"""
    name: str = Field(..., description="Нормализованное имя сущности, например 'SIRT1', 'mTOR'")
    type: EntityType

class ScientificConcept(BaseModel):
    """Научный концепт из статьи"""
    concept_type: ConceptType
    statement: str
    mentioned_entities: List[MentionedEntity] = Field(default_factory=list)

class ExtractedKnowledge(BaseModel):
    """Извлеченные знания из статьи"""
    paper_id: str
    concepts: List[ScientificConcept]

class Critique(BaseModel):
    """Критика направления исследования от агента-критика"""
    is_interesting: bool = Field(..., description="Проходит ли направление базовую проверку интереса?")
    novelty_score: float = Field(..., description="Оценка новизны 0-10. 10 - новая парадигма")
    impact_score: float = Field(..., description="Оценка влияния 0-10. 10 - Нобелевская премия") 
    feasibility_score: float = Field(..., description="Оценка выполнимости 0-10. 10 - можно сделать за год")
    final_score: float = Field(..., description="Итоговая оценка (0.5*impact + 0.3*novelty + 0.2*feasibility)")
    strengths: List[str] = Field(..., description="Сильные стороны направления")
    weaknesses: List[str] = Field(..., description="Слабые стороны и риски")
    recommendation: Literal["Strongly Recommend", "Consider", "Reject"]

class PrioritizedDirection(BaseModel):
    """Приоритизированное направление исследования"""
    rank: int
    title: str
    description: str
    critique: Critique
    supporting_papers: List[str]
    research_type: Optional[str] = Field(default=None, description="Type of research direction (Bridge, White Spot, etc.)")

# Новые модели для v2.0
class SynthesizedBridgeIdea(BaseModel):
    """Синтезированная идея-мост от Агента-Синтезатора"""
    title: str = Field(..., description="A short, catchy, and scientifically accurate title for the research direction.")
    scientific_premise: str = Field(..., description="A 1-2 sentence explanation of WHY this connection is interesting, based on the provided contexts.")
    proposed_direction: str = Field(..., description="A concrete, 1-2 sentence proposal for a research direction.")

# v2.1: Структурированные подгруппы внутри программ
DirectionType = Literal["Fundamental Mechanism Exploration", "Hypothesis Validation", "Methodological Application"]

class DirectionSubgroup(BaseModel):
    """Подгруппа направлений внутри тематической программы"""
    subgroup_type: DirectionType = Field(..., description="Type of research approaches in this subgroup")
    subgroup_description: str = Field(..., description="1-2 sentence explanation of this subgroup's focus") 
    directions: List[PrioritizedDirection] = Field(..., description="Directions belonging to this subgroup")

class ThematicProgram(BaseModel):
    """Тематическая программа исследований v2.1 с внутренней структурой"""
    program_title: str = Field(..., description="A high-level title for the strategic research program.")
    program_summary: str = Field(..., description="A 2-3 sentence summary explaining the program's importance and scope.")
    subgroups: List[DirectionSubgroup] = Field(..., description="Structured subgroups of directions within this program")
    
    @property
    def component_directions(self) -> List[PrioritizedDirection]:
        """Все направления программы (для обратной совместимости)"""
        all_directions = []
        for subgroup in self.subgroups:
            all_directions.extend(subgroup.directions)
        return all_directions

class HierarchicalReport(BaseModel):
    """Иерархический отчет v2.0"""
    timestamp: str
    total_programs: int
    programs: List[ThematicProgram]
    unclustered_directions: List[PrioritizedDirection]  # Для идей, не попавших в кластеры 