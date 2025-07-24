# -*- coding: utf-8 -*-
"""
Graph модуль для работы с графом знаний и нормализацией сущностей
"""

from .knowledge_graph import ScientificKnowledgeGraph
from .entity_normalizer import EntityNormalizer

__all__ = ['ScientificKnowledgeGraph', 'EntityNormalizer'] 