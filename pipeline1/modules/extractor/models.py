"""
Модели данных для Модуля 2 - Extractor v2.0
Система извлечения научной нарративы из исследовательских документов
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class KnowledgeTriple(BaseModel):
    """Структурированный факт в формате Субъект-Предикат-Объект."""
    subject: str = Field(..., description="Субъект тройки знания")
    predicate: str = Field(..., description="Предикат (отношение) тройки знания")
    object: str = Field(..., description="Объект тройки знания")


class ScientificStatement(BaseModel):
    """Один компонент научной нарративы."""
    statement_type: Literal[
        "Hypothesis", "Method", "Result", "Conclusion", "Dataset", "Comment"
    ] = Field(..., description="Тип научного утверждения")
    
    statement_content: str = Field(
        ..., 
        description="Точный текст утверждения, извлеченный из документа"
    )
    
    knowledge_triples: List[KnowledgeTriple] = Field(
        default_factory=list, 
        description="Список структурированных фактов, содержащихся в этом утверждении"
    )


class ExtractedNarrative(BaseModel):
    """Полная структурированная научная нарратива одного документа."""
    scientific_narrative: List[ScientificStatement] = Field(
        ..., 
        description="Список научных утверждений, извлеченных из документа"
    )


class DocumentInput(BaseModel):
    """Входной документ для обработки."""
    source_id: str = Field(..., description="Уникальный идентификатор документа")
    source_url: Optional[str] = Field(None, description="URL источника документа")
    title: str = Field(..., description="Название документа")
    abstract: str = Field(..., description="Аннотация документа")
    content: Optional[str] = Field(None, description="Полный текст документа (если доступен)")


class ProcessedDocument(BaseModel):
    """Обработанный документ с извлеченной нарративой."""
    source_id: str = Field(..., description="Уникальный идентификатор документа")
    source_url: Optional[str] = Field(None, description="URL источника документа")
    scientific_narrative: List[ScientificStatement] = Field(
        ..., 
        description="Список научных утверждений, извлеченных из документа"
    )


# Алиасы для совместимости с новым Knowledge Extractor
InputDocument = DocumentInput  # Алиас для DocumentInput


# Новые модели для Knowledge Extractor (согласно ТЗ)
class Entity(BaseModel):
    """Научная сущность (ген, белок, болезнь, соединение, метод)."""
    name: str = Field(..., description="Название сущности")
    type: str = Field(..., description="Тип сущности (Gene/Protein, Disease, Chemical, Method, etc.)")


class Relationship(BaseModel):
    """Отношение между сущностями в формате тройки."""
    subject: str = Field(..., description="Субъект отношения")
    predicate: str = Field(..., description="Предикат (тип отношения)")
    object: str = Field(..., description="Объект отношения")


class DocumentClassification(BaseModel):
    """Классификация документа."""
    research_area: str = Field(
        ..., 
        description="Область исследования (epigenetics, immunology, metabolism, senescence, etc.)"
    )
    maturity_level: Literal[
        "basic_research", 
        "clinical_development", 
        "product_ready", 
        "review"
    ] = Field(..., description="Уровень зрелости исследования")


class KnowledgeGraph(BaseModel):
    """Граф знаний из документа."""
    entities: List[Entity] = Field(
        default_factory=list,
        description="Список всех извлеченных сущностей"
    )
    relationships: List[Relationship] = Field(
        default_factory=list,
        description="Список всех извлеченных отношений"
    )


class ExtractedDocument(BaseModel):
    """Полный результат извлечения знаний из документа (для Knowledge Extractor)."""
    source_id: str = Field(..., description="ID документа из входного файла")
    source_url: Optional[str] = Field(None, description="URL документа")
    classification: DocumentClassification = Field(..., description="Классификация документа")
    knowledge_graph: KnowledgeGraph = Field(..., description="Извлеченный граф знаний")


# Примеры значений для классификации
RESEARCH_AREAS = [
    "epigenetics",
    "immunology", 
    "metabolism",
    "senescence",
    "autophagy",
    "mitochondria",
    "stem_cells",
    "genetics",
    "proteomics",
    "microbiome",
    "longevity_interventions",
    "aging_mechanisms",
    "other"
]

ENTITY_TYPES = [
    "Gene/Protein",
    "Disease", 
    "Chemical/Drug",
    "Biological_Process",
    "Cell_Type",
    "Tissue/Organ",
    "Method/Technology",
    "Biomarker",
    "Pathway",
    "Species/Model",
    "Other"
] 