# -*- coding: utf-8 -*-
"""
Модуль анализа графа знаний и генерации направлений исследований
Простой аналитик для поиска перспективных направлений
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import concurrent.futures
import numpy as np

from core.models import Critique, PrioritizedDirection, SynthesizedBridgeIdea, ThematicProgram, HierarchicalReport, DirectionSubgroup, DirectionType
from config import llm_critic_client

class ResearchAnalyst:
    """Аналитик для исследования графа знаний"""
    
    def __init__(self, knowledge_graph):
        self.graph = knowledge_graph.graph

    def _generate_directions_from_white_spots(self, max_workers=4) -> list:
        """Поиск 'белых пятен' с помощью Агента-Синтезатора качественных описаний"""
        print("  🔬 Запускаю Агента-Синтезатора для анализа белых пятен...")
        directions = []
        
        # Находим все гипотезы
        all_hypotheses = [(node_id, data) for node_id, data in self.graph.nodes(data=True) 
                         if data.get('type') == 'Hypothesis']
        print(f"     🔍 Найдено гипотез для анализа: {len(all_hypotheses)}")
        
        # Собираем задачи для параллельного выполнения
        whitespot_tasks = []
        for node_id, data in all_hypotheses:
            successors = list(self.graph.successors(node_id))
            has_results = any(self.graph.nodes[n].get('type') == 'Result' 
                            for n in successors)
            
            if not has_results:
                paper_id = data.get('paper_id')
                paper_node = self.graph.nodes.get(paper_id, {})
                paper_context = paper_node.get('content', '')
                hypothesis_text = data.get('statement', data.get('content', 'N/A'))
                
                whitespot_tasks.append({
                    'hypothesis_text': hypothesis_text,
                    'paper_id': paper_id,
                    'paper_context': paper_context
                })
        
        print(f"     📋 Подготовлено {len(whitespot_tasks)} задач для параллельного синтеза ({max_workers} потоков)")
        
        # Параллельное выполнение синтеза белых пятен
        def process_whitespot(task):
            idea = self._synthesize_whitespot_idea(
                task['hypothesis_text'], 
                task['paper_id'], 
                task['paper_context']
            )
            if idea:
                return {
                    "type": "White Spot",
                    "title": idea.title,
                    "description": f"{idea.scientific_premise} {idea.proposed_direction}",
                    "supporting_papers": [task['paper_id']]
                }
            return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(process_whitespot, task): task 
                for task in whitespot_tasks
            }
            
            for future in tqdm(concurrent.futures.as_completed(future_to_task), 
                             total=len(whitespot_tasks), desc="Анализ белых пятен",
                             position=0, leave=True):
                try:
                    result = future.result()
                    if result:
                        directions.append(result)
                except Exception as e:
                    print(f"⚠️ Ошибка обработки белого пятна: {e}")
        
        print(f"     ✅ Синтезировано {len(directions)} качественных описаний белых пятен")
        return directions

    def _generate_directions_from_bridges(self, max_workers=4) -> list:
        """Поиск 'междисциплинарных мостов' с помощью Агента-Синтезатора."""
        print("  🧠 Запускаю Агента-Синтезатора для поиска междисциплинарных мостов...")
        directions = []
        entity_papers = defaultdict(set)
        
        # 1. Сначала собираем все статьи для каждой сущности, как и раньше
        for u, v, data in self.graph.edges(data=True):
            if data.get('type') == 'MENTIONS':
                concept_node = self.graph.nodes[u]
                entity_node = self.graph.nodes[v]
                paper_id = concept_node.get('paper_id')
                entity_name = entity_node.get('name')
                if paper_id and entity_name:
                    entity_papers[entity_name].add(paper_id)

        # Собираем задачи для параллельного синтеза мостов
        bridge_tasks = []
        for entity, papers in entity_papers.items():
            if len(papers) > 1:
                # Извлекаем контекст для этой сущности из всех связей
                contexts = defaultdict(list)
                for u, v, data in self.graph.edges(data=True):
                    if data.get('type') == 'MENTIONS' and self.graph.nodes[v].get('name') == entity:
                        paper_id = self.graph.nodes[u].get('paper_id')
                        if paper_id in papers and data.get('context'):
                            contexts[paper_id].append(data['context'])
                
                if contexts:
                    bridge_tasks.append({
                        'entity': entity,
                        'contexts': dict(contexts),
                        'papers': list(papers)
                    })
        
        print(f"     📋 Подготовлено {len(bridge_tasks)} задач для параллельного синтеза мостов ({max_workers} потоков)")
        
        # Параллельное выполнение синтеза идей-мостов
        def process_bridge(task):
            idea = self._synthesize_bridge_idea(task['entity'], task['contexts'])
            if idea:
                return {
                    "type": "Bridge",
                    "title": idea.title,
                    "description": f"{idea.scientific_premise} {idea.proposed_direction}",
                    "supporting_papers": task['papers']
                }
            return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(process_bridge, task): task 
                for task in bridge_tasks
            }
            
            for future in tqdm(concurrent.futures.as_completed(future_to_task), 
                             total=len(bridge_tasks), desc="Синтез идей-мостов",
                             position=0, leave=True):
                try:
                    result = future.result()
                    if result:
                        directions.append(result)
                except Exception as e:
                    print(f"⚠️ Ошибка обработки моста: {e}")
        return directions

    def _generate_directions_from_new_methods(self, max_workers=4) -> list:
        """Поиск 'новых инструментов для старых проблем' с помощью Агента-Синтезатора"""
        print("  🧪 Запускаю Агента-Синтезатора для анализа новых методов...")
        directions = []
        
        # Находим самый свежий год в наборе данных  
        latest_year = max((data.get('year', 0) for n, data in self.graph.nodes(data=True) 
                          if data.get('type') == 'Paper'), default=2024)
        
        print(f"     📅 Анализирую методы из свежих статей ({latest_year} год)")
        
        method_entity_pairs = []
        for node_id, data in self.graph.nodes(data=True):
            if (data.get('type') == 'Method' and 
                self.graph.nodes.get(data.get('paper_id', ''), {}).get('year') == latest_year):
                
                for successor in self.graph.successors(node_id):
                    if self.graph.nodes[successor].get('type') == 'Entity':
                        entity_name = self.graph.nodes[successor].get('name')
                        method_entity_pairs.append({
                            'method_text': data.get('statement', data.get('content', 'N/A')),
                            'entity_name': entity_name,
                            'paper_id': data.get('paper_id'),
                            'paper_year': latest_year
                        })
        
        print(f"     🔍 Найдено {len(method_entity_pairs)} пар метод-сущность для анализа ({max_workers} потоков)")
        
        # Параллельное выполнение синтеза новых методов
        def process_new_method(pair):
            idea = self._synthesize_new_method_idea(
                pair['method_text'], 
                pair['entity_name'], 
                pair['paper_id'], 
                pair['paper_year']
            )
            if idea:
                return {
                    "type": "New Tool, Old Problem",
                    "title": idea.title,
                    "description": f"{idea.scientific_premise} {idea.proposed_direction}",
                    "supporting_papers": [pair['paper_id']]
                }
            return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(process_new_method, task): task 
                for task in method_entity_pairs
            }
            
            for future in tqdm(concurrent.futures.as_completed(future_to_task), 
                             total=len(method_entity_pairs), desc="Анализ новых методов",
                             position=0, leave=True):
                try:
                    result = future.result()
                    if result:
                        directions.append(result)
                except Exception as e:
                    print(f"⚠️ Ошибка обработки нового метода: {e}")
        
        print(f"     ✅ Синтезировано {len(directions)} идей применения новых методов")
        return directions

    def _synthesize_bridge_idea(self, entity_name: str, contexts: dict) -> SynthesizedBridgeIdea:
        """Вызывает LLM для синтеза идеи на основе контекстов."""
        prompt = f"""# ROLE
You are a perceptive scientific strategist, adept at seeing non-obvious connections between different fields of research.

# TASK
I have discovered a structural link: the entity '{entity_name}' is mentioned in several papers in different contexts. Your task is to analyze these contexts and synthesize a valuable and original research idea from them. Do not state the obvious. Look for a genuine scientific gap.

# CONTEXTS OF MENTION
"""
        for paper_id, context_list in contexts.items():
            # Берем только первый, самый релевантный контекст для краткости
            prompt += f"- In paper {paper_id}: \"{context_list[0][:500]}...\"\n"

        prompt += """
# INSTRUCTIONS
Generate a title, a scientific premise, and a concrete research proposal. Be concise but compelling. Your response MUST be a JSON object matching the SynthesizedBridgeIdea schema.
"""
        try:
            # Используем тот же мощный клиент, что и для критики
            from config import llm_critic_client 
            synthesized_idea = llm_critic_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                response_model=SynthesizedBridgeIdea
            )
            return synthesized_idea
        except Exception as e:
            print(f"⚠️ Ошибка синтеза идеи для '{entity_name}': {e}")
            return None

    def _synthesize_whitespot_idea(self, hypothesis_text: str, paper_id: str, paper_context: str = "") -> SynthesizedBridgeIdea:
        """Синтезирует качественное описание белого пятна на основе гипотезы"""
        prompt = f"""# ROLE
You are a strategic research advisor specializing in identifying high-impact validation opportunities in biomedical research.

# TASK
I have identified an untested hypothesis from a scientific paper. Your task is to analyze this hypothesis and craft a compelling research direction that explains WHY validating this hypothesis is scientifically important and HOW it could advance the field.

# HYPOTHESIS DETAILS
Paper ID: {paper_id}
Hypothesis: "{hypothesis_text}"
Additional Context: {paper_context[:500] if paper_context else "Limited context available"}

# INSTRUCTIONS
Analyze the hypothesis and generate:
1. A compelling title that captures the validation opportunity
2. A scientific premise explaining WHY this hypothesis matters (what gap it fills, what it could reveal)
3. A concrete research proposal for HOW to validate it experimentally

Focus on the scientific significance, not just the mechanics. Your response MUST be a JSON object matching the SynthesizedBridgeIdea schema.
"""
        try:
            synthesized_idea = llm_critic_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                response_model=SynthesizedBridgeIdea
            )
            return synthesized_idea
        except Exception as e:
            print(f"⚠️ Ошибка синтеза белого пятна для {paper_id}: {e}")
            return None

    def _synthesize_new_method_idea(self, method_text: str, entity_name: str, paper_id: str, paper_year: int) -> SynthesizedBridgeIdea:
        """Синтезирует идею применения нового метода к старым проблемам"""
        prompt = f"""# ROLE
You are a translational research strategist, expert at identifying how cutting-edge methodologies can solve longstanding problems in different fields.

# TASK
I have identified a novel methodology from recent research. Your task is to envision how this method could be applied to address well-established, unresolved challenges involving the same biological entity in other contexts.

# METHOD DETAILS
Paper ID: {paper_id} (Year: {paper_year})
Method: "{method_text}"
Target Entity: {entity_name}

# INSTRUCTIONS
Think creatively about:
1. What established, challenging problems exist around {entity_name} that current methods struggle with?
2. How could this novel approach provide a breakthrough solution?
3. What specific old problem could be solved with this new tool?

Generate:
- A title that captures the methodological innovation opportunity
- A scientific premise explaining what old problem this new method could solve
- A concrete proposal for applying the method to that specific challenge

Be specific about the problem being solved, not just the method being applied. Your response MUST be a JSON object matching the SynthesizedBridgeIdea schema.
"""
        try:
            synthesized_idea = llm_critic_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                response_model=SynthesizedBridgeIdea
            )
            return synthesized_idea
        except Exception as e:
            print(f"⚠️ Ошибка синтеза нового метода для {paper_id}: {e}")
            return None

    def generate_research_directions(self, max_workers=4) -> list:
        """Генерирует исследовательские направления (фаза расхождения)"""
        all_directions = []
        all_directions.extend(self._generate_directions_from_white_spots(max_workers))
        all_directions.extend(self._generate_directions_from_bridges(max_workers))
        all_directions.extend(self._generate_directions_from_new_methods(max_workers))
        
        # Удаляем дубликаты по названию
        unique_directions = {d['title']: d for d in all_directions}.values()
        return list(unique_directions)

    def _critique_single_direction(self, direction: dict) -> dict:
        """Критикует одно направление (для параллелизации)"""
        PROMPT_CRITIC = """
# ROLE
You are a cynical but fair, world-renowned scientific reviewer for the journal 'Nature'. Your task is to ruthlessly but objectively evaluate the proposed scientific direction. You are looking for true breakthroughs, not incremental improvements.

# TASK
Evaluate the proposed research direction. Your verdict must be structured and based on three pillars: Novelty, Potential Impact, and Feasibility. Don't fall for fancy words, look at the essence.

# PROPOSED DIRECTION:
"{description}"

# EVALUATION INSTRUCTIONS:
1.  **Interest check (is_interesting):** Does this even make sense? If the idea is absurd or trivial, immediately set `false`.
2.  **Novelty (novelty_score):** Is this really something new, or just repackaging old ideas? (10 = new paradigm, 1 = another BERT paper).
3.  **Impact (impact_score):** If this works, will it change the world or just add +0.1% to some benchmark? (10 = Nobel Prize, 1 = nobody will notice).
4.  **Feasibility (feasibility_score):** Can this be tested today or is it science fiction 50 years ahead? (10 = can be done in a year in grad school, 1 = requires building a time machine).
5.  **Final Score (final_score):** Calculate as `0.5*impact + 0.3*novelty + 0.2*feasibility`.
6.  **Strengths:** 1-2 points what can be praised.
7.  **Weaknesses:** 1-2 points where the main risks and problems are.
8.  **Recommendation:** 'Strongly Recommend' (if final_score > 7.5), 'Consider' (if final_score > 5.0), 'Reject' (in all other cases).

CRITICAL: Your response MUST be ONLY a JSON object that corresponds to the Pydantic Critique schema. 
CRITICAL: All text fields (strengths, weaknesses) MUST be in English only.
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

    def critique_and_prioritize(self, directions: list, max_workers=4) -> list:
        """Критикует и приоритизирует направления (фаза схождения)"""
        print(f"     🚀 Запускаем параллельную критику {len(directions)} направлений ({max_workers} потоков)")
        
        critiqued_directions = []
        
        # Параллельная обработка направлений
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_direction = {
                executor.submit(self._critique_single_direction, direction): direction 
                for direction in directions
            }
            
            for future in tqdm(concurrent.futures.as_completed(future_to_direction), 
                             total=len(directions), desc="Критика направлений",
                             position=0, leave=True):
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
                supporting_papers=direction['supporting_papers'],
                research_type=direction.get('type', 'Unknown')
            )
            for i, direction in enumerate(sorted_directions)
        ]
        return final_ranking

    def save_report(self, prioritized_list: list, filepath: str = "research_report.json"):
        """Сохраняет финальный отчет в JSON файл"""
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Создаем отчет в виде словаря
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

    def _synthesize_cluster_report(self, cluster_directions: list) -> ThematicProgram:
        """Вызывает Главного Аналитика v2.1 для синтеза структурированной программы с подгруппами."""
        
        # Готовим детальный список для промпта
        detailed_directions = [
            {
                "rank": d.rank, 
                "title": d.title, 
                "description": d.description,
                "type": d.research_type,  # Тип направления из первичной генерации
                "final_score": d.critique.final_score
            } 
            for d in cluster_directions
        ]

        prompt = f"""# ROLE
You are a Chief Scientific Officer with expertise in structuring complex research portfolios. Your analysts have provided you with a cluster of related research directions. Your task is to create a strategic research program with internal structure.

# TASK
Analyze the following research directions and create a structured strategic program:

1. Write a high-level program title and summary
2. CRITICALLY: Group the directions into 2-4 focused subgroups based on research approach:
   - "Fundamental Mechanism Exploration" (basic science, understanding how things work)
   - "Hypothesis Validation" (testing specific untested claims or predictions)  
   - "Methodological Application" (applying new tools/techniques to solve problems)

Each subgroup should contain 2-8 related directions. Provide a 1-2 sentence description of each subgroup's focus.

# INPUT DATA (CLUSTERED RESEARCH DIRECTIONS)
{json.dumps(detailed_directions, indent=2)}

# INSTRUCTIONS
Your response MUST follow this exact JSON structure:
{{
  "program_title": "Strategic Program Title",
  "program_summary": "2-3 sentence summary of importance and scope",
  "subgroups": [
    {{
      "subgroup_type": "Fundamental Mechanism Exploration",
      "subgroup_description": "Brief focus description",
      "direction_ranks": [1, 3, 5]
    }},
    {{
      "subgroup_type": "Hypothesis Validation", 
      "subgroup_description": "Brief focus description",
      "direction_ranks": [2, 4]
    }}
  ]
}}

CRITICAL: Only use the exact subgroup_type names provided. Include direction_ranks as list of integers.
"""
        try:
            from pydantic import BaseModel
            from typing import List

            class SubgroupStructure(BaseModel):
                subgroup_type: DirectionType
                subgroup_description: str
                direction_ranks: List[int]

            class StructuredProgram(BaseModel):
                program_title: str
                program_summary: str
                subgroups: List[SubgroupStructure]

            response = llm_critic_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                response_model=StructuredProgram
            )
            
            # Создаем финальную структуру с распределением направлений по подгруппам
            final_subgroups = []
            rank_to_direction = {d.rank: d for d in cluster_directions}
            
            for subgroup in response.subgroups:
                subgroup_directions = []
                for rank in subgroup.direction_ranks:
                    if rank in rank_to_direction:
                        subgroup_directions.append(rank_to_direction[rank])
                
                if subgroup_directions:  # Только непустые подгруппы
                    # Сортируем направления внутри подгруппы по рангу (лучшие сначала)
                    subgroup_directions.sort(key=lambda d: d.rank)
                    final_subgroups.append(DirectionSubgroup(
                        subgroup_type=subgroup.subgroup_type,
                        subgroup_description=subgroup.subgroup_description,
                        directions=subgroup_directions
                    ))
            
            return ThematicProgram(
                program_title=response.program_title,
                program_summary=response.program_summary,
                subgroups=final_subgroups
            )
            
        except Exception as e:
            print(f"⚠️ Ошибка синтеза структурированной программы: {e}")
            return None

    def _get_gemini_embeddings(self, texts: list) -> np.ndarray:
        """Получает эмбеддинги текстов через Gemini API"""
        try:
            from google import genai
            import os
            import numpy as np
            
            # Создаем клиент Gemini для эмбеддингов согласно документации
            client = genai.Client()
            
            print(f"      🔢 Получаю эмбеддинги для {len(texts)} описаний через Gemini...")
            
            # Получаем эмбеддинги согласно официальной документации
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=texts  # contents, не content!
            )
            
            # Конвертируем в numpy array для sklearn
            embeddings_list = []
            for embedding in result.embeddings:  # result.embeddings, не result['embedding']
                embeddings_list.append(embedding.values)  # embedding.values для получения чисел
            
            embeddings_array = np.array(embeddings_list)
            print(f"      ✅ Получены эмбеддинги размерности {embeddings_array.shape}")
            
            return embeddings_array
            
        except Exception as e:
            print(f"⚠️ Ошибка получения эмбеддингов Gemini: {e}")
            # Fallback: возвращаем случайные эмбеддинги для тестирования
            print("   🔄 Используем случайные эмбеддинги для тестирования...")
            return np.random.rand(len(texts), 768)

    def analyze_and_synthesize_report(self, directions: list, max_workers=4) -> HierarchicalReport:
        """Новый главный метод, включающий критику, кластеризацию и синтез."""
        
        # 1. Критикуем все направления, как и раньше
        print("   🎯 -> Phase 2.1: Critiquing and prioritizing directions...")
        critiqued_list = self.critique_and_prioritize(directions, max_workers)

        if not critiqued_list:
            return HierarchicalReport(timestamp=datetime.now().isoformat(), total_programs=0, programs=[], unclustered_directions=[])
        
        # 2. Векторизация и Кластеризация
        print("   🧠 -> Phase 2.2: Clustering directions thematically...")
        from sklearn.cluster import DBSCAN
        import numpy as np
        
        # Используем Gemini embeddings для получения векторов
        embeddings = self._get_gemini_embeddings([d.description for d in critiqued_list])

        # Используем DBSCAN для кластеризации (строгие параметры для фокусированных кластеров)
        dbscan = DBSCAN(eps=0.35, min_samples=2, metric='cosine')
        clusters = dbscan.fit_predict(embeddings)

        clustered_directions = defaultdict(list)
        unclustered_directions = []
        for i, direction in enumerate(critiqued_list):
            if clusters[i] == -1: # -1 это шум (не попали в кластер)
                unclustered_directions.append(direction)
            else:
                clustered_directions[clusters[i]].append(direction)
        
        print(f"      ✅ Найдено {len(clustered_directions)} тематических кластеров.")

        # 3. Синтез отчета Главным Аналитиком
        print("   🏆 -> Phase 2.3: Synthesizing the final strategic report...")
        final_programs = []
        for cluster_id, directions_in_cluster in tqdm(clustered_directions.items(), 
                                                     desc="Синтез программ",
                                                     position=0, leave=True):
            # Сортируем идеи внутри кластера по рангу
            sorted_directions = sorted(directions_in_cluster, key=lambda d: d.rank)
            program = self._synthesize_cluster_report(sorted_directions)
            if program:
                final_programs.append(program)

        # Сортируем сами программы по важности (например, по лучшему скору внутри)
        final_programs.sort(key=lambda p: max(d.critique.final_score for d in p.component_directions), reverse=True)

        return HierarchicalReport(
            timestamp=datetime.now().isoformat(),
            total_programs=len(final_programs),
            programs=final_programs,
            unclustered_directions=sorted(unclustered_directions, key=lambda d: d.rank)
        )

    def save_hierarchical_report(self, report: HierarchicalReport, filepath: str):
        """Сохраняет иерархический отчет в JSON файл"""
        try:
            with open(filepath, "w", encoding='utf-8') as f:
                f.write(report.model_dump_json(indent=2))
            print(f"💾 Иерархический отчет сохранен в: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения иерархического отчета: {e}")
            return False 