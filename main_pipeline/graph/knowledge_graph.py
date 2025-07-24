# -*- coding: utf-8 -*-
"""
Граф знаний для анализа научных статей
Простой класс для построения и управления графом знаний
"""

import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from tqdm import tqdm
import concurrent.futures

from core.models import ExtractedKnowledge
from processing.pdf_processing import SimplePDFReader, CacheManager
from config import llm_extractor_client
from .entity_normalizer import EntityNormalizer

class ScientificKnowledgeGraph:
    """Граф знаний для научных статей"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.pdf_reader = SimplePDFReader()
        self.cache = CacheManager()
        self.entity_normalizer = EntityNormalizer()

    def save_graph(self, filepath: str = "knowledge_graph.graphml"):
        """Сохраняет граф в файл GraphML"""
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            nx.write_graphml(self.graph, filepath)
            print(f"💾 Граф сохранен в файл: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения графа: {e}")
            return False

    def load_graph(self, filepath: str = "knowledge_graph.graphml") -> bool:
        """Загружает граф из файла GraphML"""
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                print(f"📁 Файл графа не найден: {filepath}")
                return False
            
            self.graph = nx.read_graphml(filepath)
            print(f"✅ Граф загружен из файла: {filepath}")
            print(f"   📊 Узлов: {self.graph.number_of_nodes()}, Рёбер: {self.graph.number_of_edges()}")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки графа: {e}")
            return False

    def get_graph_stats(self):
        """Возвращает статистику графа"""
        if not self.graph:
            return "Граф пуст"
        
        stats = {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'papers': len([n for n, d in self.graph.nodes(data=True) if d.get('type') == 'Paper']),
            'hypotheses': len([n for n, d in self.graph.nodes(data=True) if d.get('type') == 'Hypothesis']),
            'methods': len([n for n, d in self.graph.nodes(data=True) if d.get('type') == 'Method']),
            'results': len([n for n, d in self.graph.nodes(data=True) if d.get('type') == 'Result']),
            'conclusions': len([n for n, d in self.graph.nodes(data=True) if d.get('type') == 'Conclusion']),
            'entities': len([n for n, d in self.graph.nodes(data=True) if d.get('type') == 'Entity'])
        }
        return stats

    def _extract_scientific_concepts(self, paper_id: str, text: str) -> ExtractedKnowledge:
        """Извлекает научные концепты из текста статьи"""
        # Ограничиваем текст если он слишком большой
        text_for_prompt = text[:200000] + ("..." if len(text) > 80000 else "")
        
        prompt_text = f"""
        You are an expert in scientific research methodology and bioinformatics.
        
        TASK: Analyze the following FULL scientific paper text and extract its core components.
        
        IMPORTANT DISTINCTIONS:
        - Hypothesis: A testable prediction or proposed explanation (often starts with "we hypothesize", "we propose", "we test the hypothesis")
        - Method: The experimental technique or approach used (e.g., "using CRISPR", "via flow cytometry", "mass spectrometry")  
        - Result: The actual findings or observations from experiments (e.g., "we observed", "showed", "revealed")
        - Conclusion: Final interpretations or implications drawn from results (e.g., "we conclude", "this confirms")
        
        For each component, identify all mentioned biological entities (Genes like SIRT1, Proteins like mTOR, Diseases, Compounds like Rapamycin, Processes like senescence).
        
        BE PRECISE: A hypothesis without corresponding results in the same paper should remain unconnected.

        CRITICAL: Your response MUST be a structured JSON that follows the ExtractedKnowledge schema.
        CRITICAL: All text fields (statements, entity names) MUST be in English only.

        FULL PAPER TEXT: "{text_for_prompt}"
        
        Paper ID: {paper_id}
        """
        
        try:
            knowledge = llm_extractor_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt_text}],
                response_model=ExtractedKnowledge
            )
            knowledge.paper_id = paper_id
            return knowledge
        except Exception as e:
            print(f"⚠️ Ошибка извлечения концептов для {paper_id}: {e}")
            return ExtractedKnowledge(paper_id=paper_id, concepts=[])

    def _process_single_document(self, paper_id, doc_data):
        """Обрабатывает один документ для извлечения концептов"""
        year = doc_data.get('year', 2024)
        
        # Если есть PDF файл - извлекаем концепты напрямую из PDF
        if doc_data.get('has_pdf') and doc_data.get('pdf_path'):
            print(f"  📄 {paper_id}: прямое извлечение из PDF")
            extracted_knowledge = self.pdf_reader.extract_concepts_from_pdf(
                doc_data['pdf_path'], paper_id
            )
            text = f"Processed from PDF: {doc_data['pdf_path']}"
        else:
            # Иначе используем текст (для обратной совместимости)
            text = doc_data['full_text']
            extracted_knowledge = self._extract_scientific_concepts(paper_id, text)
        
        if extracted_knowledge:
            print(f"  📄 {paper_id}: найдено {len(extracted_knowledge.concepts)} концептов")
        else:
            print(f"  ❌ {paper_id}: не удалось извлечь концепты")
            extracted_knowledge = ExtractedKnowledge(paper_id=paper_id, concepts=[])
        
        return paper_id, text, year, extracted_knowledge

    def build_graph(self, documents: dict, max_workers=4, force_rebuild_normalization=False):
        """Строит граф знаний из документов с нормализацией сущностей"""
        print(f"🚀 Запускаем параллельное извлечение концептов из {len(documents)} документов (потоков: {max_workers})")
        
        # Фаза 1: Параллельно извлекаем все концепты
        all_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_paper = {
                executor.submit(self._process_single_document, paper_id, doc_data): paper_id 
                for paper_id, doc_data in documents.items()
            }
            
            # Используем tqdm без desc для избежания дублирования в многопоточности
            for future in tqdm(concurrent.futures.as_completed(future_to_paper), 
                             total=len(documents), desc="Извлечение концептов", 
                             position=0, leave=True):
                paper_id = future_to_paper[future]
                try:
                    result = future.result()
                    all_results.append(result)
                except Exception as e:
                    print(f"❌ Ошибка обработки {paper_id}: {e}")
        
        # Фаза 2: Нормализация сущностей
        print("\n🔄 Фаза нормализации сущностей...")
        
        # Собираем все извлеченные знания для нормализации
        all_extracted_knowledge = [result[3] for result in all_results]  # result[3] = extracted_knowledge
        
        # Собираем все уникальные сущности
        unique_entities = self.entity_normalizer.collect_all_entities(all_extracted_knowledge)
        
        if unique_entities:
            # Проверяем существующий мапинг нормализации
            normalization_file = "entity_normalization_map.json"
            
            # Удаляем старый мапинг при принудительном пересоздании
            if force_rebuild_normalization and Path(normalization_file).exists():
                print(f"🗑️ Удаляю старый мапинг нормализации: {normalization_file}")
                Path(normalization_file).unlink()
            
            if Path(normalization_file).exists() and not force_rebuild_normalization:
                print(f"📁 Найден существующий мапинг нормализации: {normalization_file}")
                if self.entity_normalizer.load_mapping(normalization_file):
                    print("   ✅ Мапинг загружен успешно")
                else:
                    print("   ⚠️ Ошибка загрузки, создаем новый мапинг")
                    self.entity_normalizer.normalize_entities(unique_entities)
                    self.entity_normalizer.save_mapping(normalization_file)
            else:
                # Создаем новый мапинг нормализации
                print("🆕 Создаю новый мапинг нормализации...")
                self.entity_normalizer.normalize_entities(unique_entities)
                self.entity_normalizer.save_mapping(normalization_file)
                
            # Выводим статистику нормализации
            self.entity_normalizer.print_statistics()
        else:
            print("   ⚠️ Не найдено сущностей для нормализации")
        
        # Фаза 3: Строим граф с нормализованными сущностями
        print("\n🏗️ Строим граф из извлеченных концептов...")
        
        for paper_id, text, year, extracted_knowledge in tqdm(all_results, desc="Построение графа"):
            # Добавляем узел для статьи
            self.graph.add_node(paper_id, type='Paper', content=text[:500], year=year)
            
            # Добавляем концепты и связи
            for concept in extracted_knowledge.concepts:
                concept_id = f"{paper_id}_{concept.concept_type}_{hash(concept.statement)}"
                self.graph.add_node(concept_id, 
                                  type=concept.concept_type, 
                                  content=concept.statement, 
                                  statement=concept.statement,
                                  paper_id=paper_id)
                self.graph.add_edge(paper_id, concept_id, type='CONTAINS')
                
                # Добавляем сущности с нормализацией
                for entity in concept.mentioned_entities:
                    # Используем каноническое имя вместо исходного
                    canonical_name = self.entity_normalizer.get_canonical_name(entity.name)
                    entity_id = f"{entity.type}_{canonical_name.upper()}"
                    
                    if not self.graph.has_node(entity_id):
                        self.graph.add_node(entity_id, 
                                          type='Entity', 
                                          entity_type=entity.type, 
                                          name=canonical_name.upper(),
                                          canonical_name=canonical_name)
                    self.graph.add_edge(concept_id, entity_id, type='MENTIONS', context=concept.statement)

    def visualize_graph(self):
        """Простая визуализация графа"""
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.graph, k=1, iterations=50)
        
        # Цвета для разных типов узлов
        colors = {
            'Paper': 'lightblue', 
            'Hypothesis': 'lightgreen', 
            'Method': 'lightyellow', 
            'Result': 'lightcoral', 
            'Conclusion': 'lightpink', 
            'Entity': 'lightgray'
        }
        
        for node_type in colors:
            nodes = [n for n, data in self.graph.nodes(data=True) if data.get('type') == node_type]
            nx.draw_networkx_nodes(self.graph, pos, nodelist=nodes, 
                                 node_color=colors[node_type], 
                                 node_size=300, alpha=0.8)
        
        nx.draw_networkx_edges(self.graph, pos, alpha=0.5, arrows=True)
        plt.title("Scientific Knowledge Graph")
        plt.axis('off')
        plt.show() 