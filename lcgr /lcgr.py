# -*- coding: utf-8 -*-
# 1. УСТАНОВКА ЗАВИСИМОСТЕЙ И ИМПОРТЫ
# Убедитесь, что у вас есть .env файл с вашим GOOGLE_API_KEY

# !pip install instructor langchain-google-genai matplotlib networkx numpy python-dotenv scikit-learn spacy tqdm pydantic jsonref

# 🚀 ПАРАЛЛЕЛИЗАЦИЯ: Теперь поддерживается многопоточная обработка PDF и извлечение концептов
# Настройте MAX_WORKERS в main блоке для управления количеством потоков

import networkx as nx
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import instructor
import os
import json
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import matplotlib.pyplot as plt
from collections import defaultdict
import concurrent.futures
import threading
from datetime import datetime

# Добавляем поддержку PDF
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    print("⚠️ google-genai не установлен для чтения PDF")
    GENAI_AVAILABLE = False

# Загрузка переменных окружения
load_dotenv()

# Проверяем наличие Google API ключа
if not os.getenv('GOOGLE_API_KEY'):
    print("❌ Ошибка: GOOGLE_API_KEY не найден!")
    print("🔧 Получите ключ: https://makersuite.google.com/app/apikey")
    print("🔧 Установите: export GOOGLE_API_KEY=your_api_key_here")
    exit(1)

os.environ["GOOGLE_API_KEY"] = os.getenv('GOOGLE_API_KEY')
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Клиенты Gemini через Instructor
print("🚀 Инициализация Gemini клиентов...")
try:
    # Клиент для извлечения (быстрый, дешевый)
    llm_extractor_client = instructor.from_provider(
        "google/gemini-2.0-flash",
        mode=instructor.Mode.GENAI_TOOLS
    )
    
    # Клиент для анализа и критики (мощный)
    llm_critic_client = instructor.from_provider(
        "google/gemini-2.5-flash", 
        mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS
    )
    print("✅ Gemini клиенты успешно инициализированы!")
except Exception as e:
    print(f"❌ Ошибка инициализации Gemini: {e}")
    print("🔧 Проверьте ваш GOOGLE_API_KEY")
    exit(1)

# --- 2. МОДЕЛИ ДАННЫХ (Pydantic) ---
# Описываем нашу онтологию графа + добавляем модели для оценки

ConceptType = Literal["Hypothesis", "Method", "Result", "Conclusion"]
EntityType = Literal["Gene", "Protein", "Disease", "Compound", "Process"]

class MentionedEntity(BaseModel):
    name: str = Field(..., description="Normalized name of the biological entity, e.g., 'SIRT1', 'mTOR'")
    type: EntityType

class ScientificConcept(BaseModel):
    concept_type: ConceptType
    statement: str
    mentioned_entities: List[MentionedEntity] = Field(default_factory=list)

class ExtractedKnowledge(BaseModel):
    paper_id: str
    concepts: List[ScientificConcept]

# УЛУЧШЕННЫЕ МОДЕЛИ для оценки направлений
class Critique(BaseModel):
    """Структура для ответа от Агента-Критика."""
    is_interesting: bool = Field(..., description="Does this direction pass the basic sanity check for being interesting?")
    novelty_score: float = Field(..., description="Score from 0-10 for scientific novelty. 10 is a completely new paradigm.")
    impact_score: float = Field(..., description="Score from 0-10 for potential impact. 10 could lead to a Nobel prize.")
    feasibility_score: float = Field(..., description="Score from 0-10 for technical feasibility. 10 can be done with current tech in <1 year.")
    final_score: float = Field(..., description="A final weighted score (0.5*impact + 0.3*novelty + 0.2*feasibility).")
    strengths: List[str] = Field(..., description="Bulleted list of key strengths.")
    weaknesses: List[str] = Field(..., description="Bulleted list of critical weaknesses and potential risks.")
    recommendation: Literal["Strongly Recommend", "Consider", "Reject"]

class PrioritizedDirection(BaseModel):
    rank: int
    title: str
    description: str
    critique: Critique
    supporting_papers: List[str]

# --- НОВЫЕ КЛАССЫ ДЛЯ PDF И КЭШИРОВАНИЯ ---

class SimplePDFReader:
    def __init__(self):
        if GENAI_AVAILABLE:
            self.client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
        else:
            self.client = None
    
    def read_pdf(self, pdf_path: str) -> str:
        if not self.client:
            return "PDF reader недоступен - установите google-genai"
        
        try:
            pdf_path = Path(pdf_path)
            pdf_data = pdf_path.read_bytes()
            
            prompt = """Извлеки ВЕСЬ текст из научного PDF. 
            Включи: введение, методы, результаты, обсуждение, заключение.
            НЕ суммируй - нужен полный текст!"""
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                    prompt
                ]
            )
            return response.text
        except Exception as e:
            print(f"⚠️ Ошибка чтения PDF {pdf_path}: {e}")
            return ""

class CacheManager:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.pdf_cache_file = self.cache_dir / "pdf_texts.json"
        self.pdf_cache = self._load_cache()
        # Добавляем блокировку для потокобезопасности
        self._lock = threading.Lock()
    
    def _load_cache(self):
        try:
            if self.pdf_cache_file.exists():
                with open(self.pdf_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def _save_cache(self):
        with self._lock:  # Блокируем сохранение для потокобезопасности
            with open(self.pdf_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.pdf_cache, f, ensure_ascii=False, indent=2)
    
    def get_pdf_text(self, pdf_path: str) -> str:
        file_key = f"{Path(pdf_path).name}_{os.path.getmtime(pdf_path)}"
        with self._lock:  # Блокируем чтение для потокобезопасности
            return self.pdf_cache.get(file_key, "")
    
    def save_pdf_text(self, pdf_path: str, text: str):
        file_key = f"{Path(pdf_path).name}_{os.path.getmtime(pdf_path)}"
        with self._lock:  # Блокируем запись для потокобезопасности
            self.pdf_cache[file_key] = text
        self._save_cache()

# --- 3. АДАПТИРОВАННЫЙ КЛАСС ДЛЯ ГРАФА ЗНАНИЙ ---

class ScientificKnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        # Добавляем поддержку PDF и кэша
        self.pdf_reader = SimplePDFReader()
        self.cache = CacheManager()

    def save_graph(self, filepath: str = "knowledge_graph.graphml"):
        """Сохраняет граф в файл GraphML."""
        try:
            filepath = Path(filepath)
            # Создаем папку если не существует
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            nx.write_graphml(self.graph, filepath)
            print(f"💾 Граф сохранен в файл: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения графа: {e}")
            return False

    def load_graph(self, filepath: str = "knowledge_graph.graphml") -> bool:
        """Загружает граф из файла GraphML."""
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
        """Возвращает статистику графа."""
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
        # Ограничиваем текст для промпта если он слишком большой
        text_for_prompt = text[:80000] + ("..." if len(text) > 80000 else "")
        
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

        FULL PAPER TEXT: "{text_for_prompt}"
        
        Paper ID: {paper_id}
        """
        
        try:
            knowledge = llm_extractor_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt_text}],
                response_model=ExtractedKnowledge
            )
            knowledge.paper_id = paper_id  # Устанавливаем правильный paper_id
            return knowledge
        except Exception as e:
            print(f"⚠️ Ошибка извлечения концептов для {paper_id}: {e}")
            # Возвращаем пустой результат в случае ошибки
            return ExtractedKnowledge(paper_id=paper_id, concepts=[])

    def _process_single_document(self, paper_id, doc_data):
        """Обрабатывает один документ для извлечения концептов (для параллелизации)."""
        text = doc_data['full_text']
        year = doc_data.get('year', 2024)
        
        # Извлекаем концепты
        extracted_knowledge = self._extract_scientific_concepts(paper_id, text)
        
        print(f"  📄 {paper_id}: найдено {len(extracted_knowledge.concepts)} концептов")
        
        return paper_id, text, year, extracted_knowledge

    def build_graph(self, documents: dict, max_workers=4):
        print(f"🚀 Запускаем параллельное извлечение концептов из {len(documents)} документов (потоков: {max_workers})")
        
        # Сначала параллельно извлекаем все концепты
        all_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Отправляем все задачи на выполнение
            future_to_paper = {
                executor.submit(self._process_single_document, paper_id, doc_data): paper_id 
                for paper_id, doc_data in documents.items()
            }
            
            # Собираем результаты по мере готовности
            for future in tqdm(concurrent.futures.as_completed(future_to_paper), 
                             total=len(documents), desc="Извлечение концептов"):
                paper_id = future_to_paper[future]
                try:
                    result = future.result()
                    all_results.append(result)
                except Exception as e:
                    print(f"❌ Ошибка обработки {paper_id}: {e}")
        
        print("🏗️ Строим граф из извлеченных концептов...")
        # Теперь последовательно строим граф (здесь параллелизация сложнее из-за состояния графа)
        for paper_id, text, year, extracted_knowledge in tqdm(all_results, desc="Построение графа"):
            # Добавляем узел для статьи с метаданными
            self.graph.add_node(paper_id, type='Paper', content=text[:500], year=year)
            
            # Выводим отладочную информацию
            for concept in extracted_knowledge.concepts:
                print(f"    - {concept.concept_type}: {concept.statement[:50]}...")
            
            for concept in extracted_knowledge.concepts:
                concept_id = f"{paper_id}_{concept.concept_type}_{hash(concept.statement)}"
                self.graph.add_node(concept_id, 
                                  type=concept.concept_type, 
                                  content=concept.statement, 
                                  statement=concept.statement,
                                  paper_id=paper_id)
                self.graph.add_edge(paper_id, concept_id, type='CONTAINS')
                
                for entity in concept.mentioned_entities:
                    entity_id = f"{entity.type}_{entity.name.upper()}"
                    if not self.graph.has_node(entity_id):
                        self.graph.add_node(entity_id, 
                                          type='Entity', 
                                          entity_type=entity.type, 
                                          name=entity.name.upper())
                    self.graph.add_edge(concept_id, entity_id, type='MENTIONS')
            
            # ❌ УБИРАЕМ автоматические связи - пусть LLM сам определяет связи
            # НЕ создаем автоматически связи между всеми гипотезами и результатами!

    def visualize_graph(self):
        # Простая визуализация для отладки
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.graph, k=1, iterations=50)
        
        # Разные цвета для разных типов узлов
        colors = {'Paper': 'lightblue', 'Hypothesis': 'lightgreen', 
                 'Method': 'lightyellow', 'Result': 'lightcoral', 
                 'Conclusion': 'lightpink', 'Entity': 'lightgray'}
        
        for node_type in colors:
            nodes = [n for n, data in self.graph.nodes(data=True) if data.get('type') == node_type]
            nx.draw_networkx_nodes(self.graph, pos, nodelist=nodes, 
                                 node_color=colors[node_type], 
                                 node_size=300, alpha=0.8)
        
        nx.draw_networkx_edges(self.graph, pos, alpha=0.5, arrows=True)
        plt.title("Scientific Knowledge Graph")
        plt.axis('off')
        plt.show()

# --- 4. УЛУЧШЕННЫЙ НАУЧНЫЙ АНАЛИТИК ---

class ResearchAnalyst:
    def __init__(self, knowledge_graph: ScientificKnowledgeGraph):
        self.graph = knowledge_graph.graph

    # --- МЕТОДЫ ДЛЯ ФАЗЫ РАСХОЖДЕНИЯ (DIVERGENT) ---
    
    def _generate_directions_from_white_spots(self) -> List[dict]:
        """Аналитика №1: Поиск "белых пятен" - гипотез без прямых доказательств."""
        directions = []
        
        # 🐛 ОТЛАДКА: покажем все гипотезы
        all_hypotheses = [(node_id, data) for node_id, data in self.graph.nodes(data=True) 
                         if data.get('type') == 'Hypothesis']
        print(f"  🔍 Найдено гипотез: {len(all_hypotheses)}")
        
        for node_id, data in all_hypotheses:
            successors = list(self.graph.successors(node_id))
            has_results = any(self.graph.nodes[n].get('type') == 'Result' 
                            for n in successors)
            
            print(f"    - Гипотеза {data.get('paper_id')}: '{data.get('statement', 'N/A')[:30]}...'")
            print(f"      Связей: {len(successors)}, Результатов: {has_results}")
            
            if not has_results:
                directions.append({
                    "type": "White Spot",
                    "title": f"Validation of Hypothesis from paper {data.get('paper_id')}",
                    "description": f"The paper {data.get('paper_id')} states the hypothesis '{data.get('content', data.get('statement', 'N/A'))}', but does not provide direct experimental results to support it within the abstract. This represents a 'white spot' and a clear opportunity for experimental validation.",
                    "supporting_papers": [data.get('paper_id')]
                })
        
        print(f"  ✅ Найдено белых пятен: {len(directions)}")
        return directions

    def _generate_directions_from_bridges(self) -> List[dict]:
        """Аналитика №2: Поиск "междисциплинарных мостов" - общих сущностей в разных статьях."""
        directions = []
        entity_papers = defaultdict(set)
        
        for node_id, data in self.graph.nodes(data=True):
            if data.get('type') == 'Entity':
                for predecessor in self.graph.predecessors(node_id):
                    paper_id = self.graph.nodes[predecessor].get('paper_id')
                    if paper_id:
                        entity_papers[data.get('name')].add(paper_id)
        
        for entity, papers in entity_papers.items():
            if len(papers) > 1:
                directions.append({
                    "type": "Bridge",
                    "title": f"Investigate the Cross-Disciplinary Role of {entity}",
                    "description": f"The entity '{entity}' is mentioned in several potentially disconnected research areas across papers {list(papers)}. This suggests an unexplored common mechanism that could be a novel research direction, bridging these fields.",
                    "supporting_papers": list(papers)
                })
        return directions

    def _generate_directions_from_new_methods(self) -> List[dict]:
        """Аналитика №3: Поиск "новых инструментов для старых проблем"."""
        directions = []
        # Находим самый свежий год в нашем наборе данных
        latest_year = max((data.get('year', 0) for n, data in self.graph.nodes(data=True) 
                          if data.get('type') == 'Paper'), default=2024)
        
        for node_id, data in self.graph.nodes(data=True):
            if (data.get('type') == 'Method' and 
                self.graph.nodes[data.get('paper_id', '')].get('year') == latest_year):
                
                for successor in self.graph.successors(node_id):
                    if self.graph.nodes[successor].get('type') == 'Entity':
                        entity_name = self.graph.nodes[successor].get('name')
                        directions.append({
                            "type": "New Tool, Old Problem",
                            "title": f"Apply Novel Method to Problems Involving {entity_name}",
                            "description": f"A recent paper ({data.get('paper_id')}, {latest_year}) introduced a new method: '{data.get('content', data.get('statement', 'N/A'))}'. This method was used in the context of '{entity_name}'. There is a significant opportunity to apply this state-of-the-art method to other, well-established problems where '{entity_name}' is a key factor.",
                            "supporting_papers": [data.get('paper_id')]
                        })
        return directions

    def generate_research_directions(self) -> List[dict]:
        """Главный метод фазы расхождения: собирает все идеи."""
        all_directions = []
        all_directions.extend(self._generate_directions_from_white_spots())
        all_directions.extend(self._generate_directions_from_bridges())
        all_directions.extend(self._generate_directions_from_new_methods())
        
        # Удаляем дубликаты по названию
        unique_directions = {d['title']: d for d in all_directions}.values()
        return list(unique_directions)

    # --- МЕТОД ДЛЯ ФАЗЫ СХОЖДЕНИЯ (CONVERGENT) ---

    def _critique_single_direction(self, direction: dict) -> dict:
        """Критикует одно направление (для параллелизации)."""
        PROMPT_CRITIC = """
# РОЛЬ
Ты — циничный, но справедливый, всемирно известный научный рецензент для журнала 'Nature'. Твоя задача — беспощадно, но объективно оценить предложенное научное направление. Ты ищешь настоящий прорыв, а не инкрементальные улучшения.

# ЗАДАЧА
Оцени предложенное направление для исследования. Твой вердикт должен быть структурирован и основан на трех столпах: Новизна, Потенциальное Влияние и Реализуемость. Не поддавайся на красивые слова, смотри в суть.

# ПРЕДЛОЖЕННОЕ НАПРАВЛЕНИЕ:
"{description}"

# ИНСТРУКЦИИ ПО ОЦЕНКЕ:
1.  **Проверка на интерес (is_interesting):** Это вообще имеет смысл? Если идея абсурдна или тривиальна, сразу ставь `false`.
2.  **Новизна (novelty_score):** Это действительно что-то новое, или просто переупаковка старых идей? (10 = новая парадигма, 1 = очередная статья про BERT).
3.  **Влияние (impact_score):** Если это сработает, это изменит мир или просто добавит +0.1% к какому-то бенчмарку? (10 = Нобелевская премия, 1 = никто не заметит).
4.  **Реализуемость (feasibility_score):** Это можно проверить сегодня или это научная фантастика на 50 лет вперед? (10 = можно сделать за год в аспирантуре, 1 = требует постройки машины времени).
5.  **Итоговая Оценка (final_score):** Рассчитай как `0.5*impact + 0.3*novelty + 0.2*feasibility`.
6.  **Сильные стороны (strengths):** 1-2 пункта, за что можно похвалить.
7.  **Слабые стороны (weaknesses):** 1-2 пункта, где главные риски и проблемы.
8.  **Рекомендация (recommendation):** 'Strongly Recommend' (если final_score > 7.5), 'Consider' (если final_score > 5.0), 'Reject' (во всех остальных случаях).

Твой ответ ДОЛЖЕН быть только JSON-объектом, который соответствует Pydantic-схеме Critique.
"""
        
        try:
            critique = llm_critic_client.chat.completions.create(
                messages=[{"role": "user", "content": PROMPT_CRITIC.format(description=direction['description'])}],
                response_model=Critique
            )
            
            if critique.is_interesting:
                direction['critique'] = critique
                return direction
            else:
                return None
        except Exception as e:
            print(f"⚠️ Ошибка при обработке направления '{direction['title']}': {e}")
            return None

    def critique_and_prioritize(self, directions: List[dict], max_workers=4) -> List[PrioritizedDirection]:
        """Главный метод фазы схождения: использует Агента-Критика с параллелизацией."""
        print(f"🚀 Запускаем параллельную критику {len(directions)} направлений (потоков: {max_workers})")
        
        critiqued_directions = []
        
        # Параллельная обработка направлений
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Отправляем все задачи на выполнение
            future_to_direction = {
                executor.submit(self._critique_single_direction, direction): direction 
                for direction in directions
            }
            
            # Собираем результаты по мере готовности
            for future in tqdm(concurrent.futures.as_completed(future_to_direction), 
                             total=len(directions), desc="Критика направлений"):
                try:
                    result = future.result()
                    if result is not None:
                        critiqued_directions.append(result)
                except Exception as e:
                    print(f"❌ Ошибка обработки направления: {e}")
        
        sorted_directions = sorted(critiqued_directions, key=lambda x: x['critique'].final_score, reverse=True)
        
        final_ranking = [
            PrioritizedDirection(
                rank=i + 1,
                title=direction['title'],
                description=direction['description'],
                critique=direction['critique'],
                supporting_papers=direction['supporting_papers']
            )
            for i, direction in enumerate(sorted_directions)
        ]
        return final_ranking

    def save_report(self, prioritized_list: List[PrioritizedDirection], filepath: str = "research_report.json"):
        """Сохраняет финальный отчет в JSON файл."""
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Конвертируем в словарь для сохранения
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "total_directions": len(prioritized_list),
                "directions": []
            }
            
            for direction in prioritized_list:
                direction_data = {
                    "rank": direction.rank,
                    "title": direction.title,
                    "description": direction.description,
                    "supporting_papers": direction.supporting_papers,
                    "critique": {
                        "is_interesting": direction.critique.is_interesting,
                        "novelty_score": direction.critique.novelty_score,
                        "impact_score": direction.critique.impact_score,
                        "feasibility_score": direction.critique.feasibility_score,
                        "final_score": direction.critique.final_score,
                        "strengths": direction.critique.strengths,
                        "weaknesses": direction.critique.weaknesses,
                        "recommendation": direction.critique.recommendation
                    }
                }
                report_data["directions"].append(direction_data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Отчет сохранен в файл: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения отчета: {e}")
            return False

# --- 5. ФУНКЦИЯ ЗАГРУЗКИ ДАННЫХ ---

def process_single_pdf(pdf_file, cache, pdf_reader):
    """Обрабатывает один PDF файл (для параллелизации)."""
    paper_id = f"PDF_{pdf_file.stem}"
    
    # Проверяем кэш
    if cache:
        cached_text = cache.get_pdf_text(str(pdf_file))
        if cached_text:
            print(f"  📁 {paper_id}: из кэша")
            return paper_id, cached_text, 2024
        else:
            print(f"  🔄 {paper_id}: читаем PDF...")
            full_text = pdf_reader.read_pdf(str(pdf_file))
            if full_text:
                cache.save_pdf_text(str(pdf_file), full_text)
            return paper_id, full_text, 2024
    else:
        full_text = pdf_reader.read_pdf(str(pdf_file))
        return paper_id, full_text, 2024

def load_documents(pdf_folder="downloaded_pdfs", use_cache=True, max_workers=4):
    """Загружает PDF файлы из папки или JSON файл."""
    
    # Ищем папку с PDF в разных местах
    possible_paths = [
        Path(pdf_folder),  # относительно текущей папки
        Path("downloaded_pdfs"),  # прямо downloaded_pdfs
        Path(".") / "downloaded_pdfs",  # в текущей папке
        Path("..") / pdf_folder,  # на уровень выше
    ]
    
    pdf_path = None
    for path in possible_paths:
        print(f"🔍 Проверяем путь: {path.absolute()} - существует: {path.exists()}, папка: {path.is_dir() if path.exists() else 'N/A'}")
        if path.exists() and path.is_dir():
            pdf_path = path
            break
    
    if pdf_path:
        print(f"📁 Найдена папка с PDF: {pdf_path}")
        documents = {}
        pdf_files = list(pdf_path.glob("*.pdf"))
        
        cache = CacheManager() if use_cache else None
        pdf_reader = SimplePDFReader()
        
        print(f"🚀 Запускаем параллельную обработку {len(pdf_files)} PDF файлов (потоков: {max_workers})")
        
        # Параллельная обработка PDF файлов
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Отправляем все задачи на выполнение
            future_to_pdf = {
                executor.submit(process_single_pdf, pdf_file, cache, pdf_reader): pdf_file 
                for pdf_file in pdf_files
            }
            
            # Собираем результаты по мере готовности
            for future in tqdm(concurrent.futures.as_completed(future_to_pdf), 
                             total=len(pdf_files), desc="Обработка PDF файлов"):
                pdf_file = future_to_pdf[future]
                try:
                    paper_id, full_text, year = future.result()
                    if full_text:
                        documents[paper_id] = {
                            "full_text": full_text,
                            "year": year
                        }
                except Exception as e:
                    print(f"❌ Ошибка обработки {pdf_file}: {e}")
        
        print(f"✅ Загружено {len(documents)} PDF файлов")
        return documents
    
    # Если папки нет, пробуем JSON (старая логика)
    try:
        with open("pubmed_corpus.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Конвертируем старый формат в новый
            converted = {}
            for paper_id, doc_data in data.items():
                converted[paper_id] = {
                    "full_text": doc_data.get('abstract', ''),
                    "year": doc_data.get('year', 2024)
                }
            print(f"Загружено {len(converted)} статей из JSON")
            return converted
    except FileNotFoundError:
        print("Используются тестовые данные")
        return {
            "TEST:1": {
                "full_text": "Here we test the hypothesis that SIRT1 activation extends lifespan. Using CRISPR-Cas9 as our primary method, we observed a 20% increase in lifespan in C. elegans. We conclude that SIRT1 is a key longevity gene.",
                "year": 2023
            },
            "TEST:2": {
                "full_text": "The role of mTOR in aging is well-established. We hypothesized that inhibiting mTOR with Rapamycin would reduce cellular senescence. Our results, obtained via flow cytometry, showed a significant decrease in senescent cells. This confirms the link between mTOR and senescence.",
                "year": 2022
            },
            "TEST:3": {
                "full_text": "This paper explores if SIRT1 is involved in cellular metabolism. We propose that it is a master regulator. However, our experiments using mass spectrometry did not yield conclusive results connecting it directly to glucose uptake.",
                "year": 2021
            },
            "TEST:4": {
                "full_text": "We investigated the protein landscape of senescent cells using a novel single-cell proteomics method. Our analysis revealed that mTOR signaling is consistently upregulated. We hypothesize this is a core driver of the senescent phenotype.",
                "year": 2024
            }
        }

# --- 6. ГЛАВНЫЙ ИСПОЛНЯЕМЫЙ БЛОК ---

if __name__ == '__main__':
    # Настройки для сохранения
    GRAPH_FILE = "longevity_knowledge_graph.graphml"
    REPORT_FILE = "research_report.json"  # Файл для сохранения отчета
    FORCE_REBUILD = False  # Установите True для принудительного пересоздания графа
    MAX_WORKERS = 4  # Количество потоков для параллельной обработки
    
    print("🧬 --- LONGEVITY RESEARCH GRAPH ANALYZER ---")
    
    # Создаем объект графа знаний
    skg = ScientificKnowledgeGraph()
    
    # Проверяем, нужно ли загружать существующий граф
    graph_exists = Path(GRAPH_FILE).exists()
    
    if graph_exists and not FORCE_REBUILD:
        print(f"📁 Найден сохранённый граф: {GRAPH_FILE}")
        if skg.load_graph(GRAPH_FILE):
            # Выводим статистику загруженного графа
            stats = skg.get_graph_stats()
            print(f"   📊 Статистика графа:")
            print(f"      • Статьи: {stats['papers']}")
            print(f"      • Гипотезы: {stats['hypotheses']}")
            print(f"      • Методы: {stats['methods']}")
            print(f"      • Результаты: {stats['results']}")
            print(f"      • Заключения: {stats['conclusions']}")
            print(f"      • Сущности: {stats['entities']}")
        else:
            print("❌ Ошибка загрузки графа. Начинаем построение с нуля.")
            graph_exists = False
    
    # Если графа нет или загрузка не удалась - строим новый
    if not graph_exists or FORCE_REBUILD:
        if FORCE_REBUILD:
            print("🔄 Принудительное пересоздание графа...")
        else:
            print("📁 Сохранённый граф не найден. Начинаю построение с нуля.")
        
        # Загружаем документы
        documents = load_documents(pdf_folder="downloaded_pdfs", max_workers=MAX_WORKERS)
        
        if not documents:
            print("❌ Не найдено документов для обработки!")
            exit(1)
        
        print("🧬 --- Stage 1: Building the Knowledge Graph ---")
        skg.build_graph(documents, max_workers=MAX_WORKERS)
        
        # Сохраняем граф
        if skg.save_graph(GRAPH_FILE):
            stats = skg.get_graph_stats()
            print(f"✅ Граф построен и сохранён: {stats['nodes']} узлов, {stats['edges']} рёбер")
        else:
            print("⚠️ Граф построен, но сохранение не удалось")
    
    print("\n🔬 --- Stage 2: Analysis and Prioritization ---")
    analyst = ResearchAnalyst(skg)

    print("\n   🌟 -> Divergent Phase: Generating raw research directions...")
    raw_directions = analyst.generate_research_directions()
    print(f"   ✅ Сгенерировано {len(raw_directions)} исходных направлений.")
    
    if raw_directions:
        print("   🎯 -> Convergent Phase: Critiquing and prioritizing directions...")
        prioritized_list = analyst.critique_and_prioritize(raw_directions, max_workers=MAX_WORKERS)

        # Сохраняем отчет в файл
        if analyst.save_report(prioritized_list, REPORT_FILE):
            print(f"✅ Отчет сохранен в: {REPORT_FILE}")
            # Краткая статистика отчета
            recommendations = {"Strongly Recommend": 0, "Consider": 0, "Reject": 0}
            for direction in prioritized_list:
                recommendations[direction.critique.recommendation] += 1
            print(f"   📊 Статистика рекомендаций: Strongly Recommend: {recommendations['Strongly Recommend']}, Consider: {recommendations['Consider']}, Reject: {recommendations['Reject']}")

        print("\n🏆 --- FINAL REPORT: PRIORITIZED RESEARCH DIRECTIONS ---")
        for direction in prioritized_list:
            print(f"\n🥇 RANK #{direction.rank}: {direction.title}")
            print(f"   📊 SCORE: {direction.critique.final_score:.2f}/10")
            print(f"   🎯 RECOMMENDATION: {direction.critique.recommendation}")
            print(f"   📝 Description: {direction.description}")
            print(f"   📚 Supporting Papers: {', '.join(direction.supporting_papers)}")
            print(f"   🔍 CRITIQUE:")
            print(f"     ✅ Novelty: {direction.critique.novelty_score}/10")
            print(f"     🎯 Impact: {direction.critique.impact_score}/10") 
            print(f"     ⚡ Feasibility: {direction.critique.feasibility_score}/10")
            
            # Правильное форматирование длинных строк
            strengths_text = '; '.join(direction.critique.strengths)
            weaknesses_text = '; '.join(direction.critique.weaknesses)
            
            print(f"     💪 Strengths:")
            for strength in direction.critique.strengths:
                print(f"        • {strength}")
            print(f"     ⚠️ Weaknesses:")  
            for weakness in direction.critique.weaknesses:
                print(f"        • {weakness}")
    else:
        print("   ⚠️ Не найдено направлений для анализа. Проверьте входные данные.")
    
    print(f"\n💾 Результаты сохранены:")
    print(f"   • Граф знаний: {GRAPH_FILE}")
    print(f"   • Отчет с направлениями: {REPORT_FILE}")
    print("🔄 Для принудительного пересоздания графа установите FORCE_REBUILD = True")