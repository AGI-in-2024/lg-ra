"""
Paper Evaluator - оценщик релевантности научных статей
"""

import json
import logging
from typing import List, Dict, Any
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

from .models import Paper, RankedPaper
from .config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    PAPER_EVALUATOR_PROMPT,
    LLM_REQUEST_TIMEOUT,
    MIN_SCORE_THRESHOLD
)


logger = logging.getLogger(__name__)


class PaperEvaluator:
    """Класс для оценки релевантности научных статей"""
    
    def __init__(self):
        # Инициализируем клиент с поддержкой Gemini API
        client_kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_BASE_URL:
            client_kwargs["base_url"] = OPENAI_BASE_URL
        
        self.client = OpenAI(**client_kwargs)
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self) -> str:
        """Загружает промпт из файла"""
        try:
            with open(PAPER_EVALUATOR_PROMPT, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Файл промпта не найден: {PAPER_EVALUATOR_PROMPT}")
            return ""
    
    def evaluate_paper(self, paper: Paper, research_topic: str) -> RankedPaper:
        """
        Оценивает релевантность статьи для исследовательской темы
        
        Args:
            paper: Объект статьи для оценки
            research_topic: Тема исследования
            
        Returns:
            Объект RankedPaper с оценкой
        """
        logger.debug(f"Оценка статьи: {paper.title[:50]}...")
        
        try:
            # Форматируем промпт
            prompt = self.prompt_template.format(
                research_topic=research_topic,
                title=paper.title,
                authors=", ".join(paper.authors),
                published_date=paper.published_date,
                summary=paper.summary
            )
            
            # Вызываем LLM для оценки
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=OPENAI_TEMPERATURE,
                timeout=LLM_REQUEST_TIMEOUT
            )
            
            content = response.choices[0].message.content
            
            # Извлекаем JSON из ответа с помощью надежного метода
            evaluation = self._extract_json_from_response(content)
            
            # Создаем RankedPaper объект
            ranked_paper = RankedPaper(
                **paper.dict(),
                score=float(evaluation.get('score', 0)),
                justification=evaluation.get('justification', 'No justification provided')
            )
            
            logger.debug(f"Оценка: {ranked_paper.score}")
            return ranked_paper
            
        except Exception as e:
            logger.error(f"Ошибка при оценке статьи {paper.id}: {e}")
            # Возвращаем статью с минимальной оценкой в случае ошибки
            return RankedPaper(
                **paper.dict(),
                score=0.0,
                justification=f"Error during evaluation: {str(e)}"
            )
    
    def evaluate_papers(self, papers: List[Paper], research_topic: str) -> List[RankedPaper]:
        """
        Оценивает список статей одним вызовом к LLM
        
        Args:
            papers: Список статей для оценки
            research_topic: Тема исследования
            
        Returns:
            Список оцененных статей, отсортированный по убыванию оценки
        """
        logger.info(f"Массовая оценка {len(papers)} статей")
        
        if not papers:
            return []
        
        # Преобразуем статьи в JSON для промпта
        papers_data = []
        for paper in papers:
            papers_data.append({
                "title": paper.title,
                "abstract": paper.summary,
                "authors": paper.authors,
                "published_date": paper.published_date
            })
        
        # Формируем промпт (используем replace для избежания конфликтов с JSON)
        papers_json = json.dumps(papers_data, ensure_ascii=False, indent=2)
        full_prompt = self.prompt_template.replace(
            "{research_topic}", research_topic
        ).replace(
            "{papers_data}", papers_json
        )
        
        logger.debug(f"Сформированный промпт: {full_prompt[:200]}...")
        
        # Вызываем LLM
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": full_prompt}],
            temperature=OPENAI_TEMPERATURE,
            timeout=LLM_REQUEST_TIMEOUT
        )
        
        content = response.choices[0].message.content
        logger.debug(f"Ответ LLM: {content[:200]}...")
        
        # Парсим ответ
        evaluation_results = self._extract_ranking_from_response(content)
        
        # Преобразуем в RankedPaper объекты
        ranked_papers = []
        
        for eval_result in evaluation_results:
            # Находим оригинальную статью по названию
            original_paper = None
            for paper in papers:
                if paper.title == eval_result.get('title', ''):
                    original_paper = paper
                    break
            
            if original_paper:
                ranked_paper = RankedPaper(
                    id=original_paper.id,
                    title=original_paper.title,
                    authors=original_paper.authors,
                    published_date=original_paper.published_date,
                    summary=original_paper.summary,
                    url=original_paper.url,
                    score=eval_result.get('score', 1.0),
                    justification=eval_result.get('justification', 'No justification provided'),
                    rank=eval_result.get('rank', len(ranked_papers) + 1)
                )
                ranked_papers.append(ranked_paper)
        
        # Добавляем статьи, которые не были найдены в результатах (с низкой оценкой)
        evaluated_titles = {result.get('title', '') for result in evaluation_results}
        for paper in papers:
            if paper.title not in evaluated_titles:
                logger.warning(f"Статья не найдена в результатах оценки: {paper.title[:50]}...")
                ranked_paper = RankedPaper(
                    id=paper.id,
                    title=paper.title,
                    authors=paper.authors,
                    published_date=paper.published_date,
                    summary=paper.summary,
                    url=paper.url,
                    score=1.0,
                    justification="Статья не была обработана системой оценки",
                    rank=len(ranked_papers) + 1
                )
                ranked_papers.append(ranked_paper)
        
        # Сортируем по убыванию оценки
        ranked_papers.sort(key=lambda x: x.score, reverse=True)
        
        # Обновляем ранги после сортировки
        for rank, paper in enumerate(ranked_papers, 1):
            paper.rank = rank
        
        logger.info(f"Массовая оценка завершена. Топ оценка: {ranked_papers[0].score if ranked_papers else 0}")
        
        return ranked_papers
    
    def filter_validated_papers(self, ranked_papers: List[RankedPaper]) -> List[RankedPaper]:
        """
        Фильтрует статьи по минимальному порогу оценки
        
        Args:
            ranked_papers: Список оцененных статей
            
        Returns:
            Список валидированных статей (score >= threshold)
        """
        validated = [p for p in ranked_papers if p.score >= MIN_SCORE_THRESHOLD]
        
        logger.info(f"Валидировано {len(validated)} статей из {len(ranked_papers)} (порог: {MIN_SCORE_THRESHOLD})")
        
        return validated
    
    def evaluate_papers_parallel(self, papers: List[Paper], research_topic: str, batch_size: int = 10, max_workers: int = 3) -> List[RankedPaper]:
        """
        Параллельная оценка большого количества статей с разбивкой на батчи
        
        Args:
            papers: Список статей для оценки
            research_topic: Тема исследования
            batch_size: Размер батча для одного LLM вызова (рекомендуется 5-15)
            max_workers: Максимальное количество параллельных потоков
            
        Returns:
            Список оцененных статей, отсортированный по убыванию оценки
        """
        logger.info(f"🚀 Параллельная оценка {len(papers)} статей (батчи по {batch_size}, {max_workers} потоков)")
        
        if not papers:
            return []
        
        # Разбиваем статьи на батчи
        batches = []
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i + batch_size]
            batches.append((i // batch_size + 1, batch))
        
        logger.info(f"📦 Разбито на {len(batches)} батчей")
        
        all_ranked_papers = []
        
        def evaluate_batch(batch_info: tuple) -> List[RankedPaper]:
            """Оценивает один батч статей"""
            batch_num, batch_papers = batch_info
            
            try:
                logger.info(f"🔍 Обработка батча {batch_num}/{len(batches)} ({len(batch_papers)} статей)...")
                
                # Используем существующий метод для батча
                ranked_papers = self.evaluate_papers(batch_papers, research_topic)
                
                logger.info(f"✅ Батч {batch_num} обработан. Лучшая оценка: {ranked_papers[0].score if ranked_papers else 0}")
                return ranked_papers
                
            except Exception as e:
                logger.error(f"❌ Ошибка в батче {batch_num}: {e}")
                # Возвращаем статьи с минимальными оценками в случае ошибки
                return [
                    RankedPaper(
                        id=paper.id,
                        title=paper.title,
                        authors=paper.authors,
                        published_date=paper.published_date,
                        summary=paper.summary,
                        url=paper.url,
                        score=1.0,
                        justification=f"Ошибка обработки: {str(e)[:100]}",
                        rank=999
                    ) for paper in batch_papers
                ]
        
        # Параллельная обработка батчей
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Отправляем все батчи на обработку
            future_to_batch = {
                executor.submit(evaluate_batch, batch_info): batch_info[0] 
                for batch_info in batches
            }
            
            # Собираем результаты по мере выполнения
            for future in as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    ranked_papers = future.result()
                    all_ranked_papers.extend(ranked_papers)
                except Exception as e:
                    logger.error(f"❌ Критическая ошибка в батче {batch_num}: {e}")
        
        # Финальная сортировка всех статей
        all_ranked_papers.sort(key=lambda x: x.score, reverse=True)
        
        # Обновляем ранги после общей сортировки
        for rank, paper in enumerate(all_ranked_papers, 1):
            paper.rank = rank
        
        logger.info(f"🎯 Параллельная оценка завершена! Обработано {len(all_ranked_papers)} статей. Топ оценка: {all_ranked_papers[0].score if all_ranked_papers else 0}")
        
        return all_ranked_papers
    
    def _extract_ranking_from_response(self, content: str) -> List[Dict[str, Any]]:
        """
        Извлекает массив ранжированных статей из ответа LLM
        
        Args:
            content: Ответ от LLM с массивом статей
            
        Returns:
            Список словарей с ранжированными статьями
        """
        logger.debug(f"🔧 Начинаем парсинг массива статей из ответа...")
        
        try:
            # Попытка 1: Найти JSON блок в markdown
            if '```json' in content:
                logger.debug("📋 Найден JSON блок в markdown")
                start_idx = content.find('```json') + 7
                end_idx = content.find('```', start_idx)
                if end_idx != -1:
                    json_str = content[start_idx:end_idx].strip()
                    logger.debug(f"JSON строка из markdown: {repr(json_str[:200])}")
                    result = json.loads(json_str)
                    if isinstance(result, list):
                        logger.debug(f"✅ Успешно распарсен массив из {len(result)} статей")
                        return result
            
            # Попытка 2: Найти JSON массив без markdown  
            logger.debug("🔍 Ищем JSON массив без markdown")
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                logger.debug(f"JSON строка без markdown: {repr(json_str[:200])}")
                result = json.loads(json_str)
                if isinstance(result, list):
                    logger.debug(f"✅ Успешно распарсен массив из {len(result)} статей")
                    return result
            
            # Попытка 3: Парсить весь ответ как JSON
            logger.debug("📄 Пытаемся парсить весь ответ как JSON")
            stripped_content = content.strip()
            result = json.loads(stripped_content)
            if isinstance(result, list):
                logger.debug(f"✅ Успешно распарсен весь ответ как массив из {len(result)} статей")
                return result
                
        except json.JSONDecodeError as e:
            logger.warning(f"❌ Ошибка парсинга JSON массива: {e}")
            logger.debug(f"Проблемный контент: {repr(content[:500])}")
            
        except Exception as e:
            logger.error(f"Не удалось извлечь массив статей: {e}")
            
        # Fallback: возвращаем пустой список
        logger.warning("Используем fallback: возвращаем пустой список")
        return []

    def _extract_json_from_response(self, content: str) -> dict:
        """
        Надежно извлекает JSON из ответа LLM
        
        Args:
            content: Ответ от LLM
            
        Returns:
            Словарь с оценкой и обоснованием
        """
        logger.debug(f"🔧 Начинаем парсинг JSON из ответа...")
        logger.debug(f"Тип контента: {type(content)}")
        logger.debug(f"Первые 100 символов: {repr(content[:100])}")
        
        try:
            # Попытка 1: Найти JSON блок в markdown
            if '```json' in content:
                logger.debug("📋 Найден JSON блок в markdown")
                start_idx = content.find('```json') + 7
                end_idx = content.find('```', start_idx)
                if end_idx != -1:
                    json_str = content[start_idx:end_idx].strip()
                    logger.debug(f"JSON строка из markdown: {repr(json_str)}")
                    result = json.loads(json_str)
                    logger.debug(f"✅ Успешно распарсен JSON из markdown: {result}")
                    return result
            
            # Попытка 2: Найти JSON блок без markdown  
            logger.debug("🔍 Ищем JSON блок без markdown")
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                logger.debug(f"JSON строка без markdown: {repr(json_str)}")
                result = json.loads(json_str)
                logger.debug(f"✅ Успешно распарсен JSON без markdown: {result}")
                return result
            
            # Попытка 3: Парсить весь ответ как JSON
            logger.debug("📄 Пытаемся парсить весь ответ как JSON")
            stripped_content = content.strip()
            logger.debug(f"Очищенный контент: {repr(stripped_content)}")
            result = json.loads(stripped_content)
            logger.debug(f"✅ Успешно распарсен весь ответ как JSON: {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"❌ Ошибка парсинга JSON: {e}")
            logger.debug(f"Проблемный контент: {repr(content)}")
            
            # Попытка 4: Извлечь оценку и обоснование с помощью регулярных выражений
            logger.debug("🛠️ Используем fallback парсинг с регулярными выражениями")
            import re
            
            score_match = re.search(r'"?score"?\s*:\s*(\d+(?:\.\d+)?)', content, re.IGNORECASE)
            just_match = re.search(r'"?justification"?\s*:\s*"([^"]*)"', content, re.IGNORECASE)
            
            score = float(score_match.group(1)) if score_match else 5.0
            justification = just_match.group(1) if just_match else "Could not parse justification from response"
            
            logger.warning(f"Использован fallback парсинг. Score: {score}, Justification: {justification[:50]}...")
            
            return {
                "score": score,
                "justification": justification
            }
        
        except Exception as e:
            logger.error(f"Не удалось извлечь JSON: {e}")
            return {
                "score": 1.0,
                "justification": f"Error parsing response: {str(e)}"
            } 