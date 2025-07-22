#!/usr/bin/env python3
"""
Примеры workflow для полного пайплайна обработки PDF документов
Демонстрирует интеграцию всех компонентов Extractor v2.0
"""

import json
import pathlib
from typing import List, Dict, Optional
from document_storage import DocumentStorage, DocumentProcessor
from pdf_reader import PDFReader
from extractor import KnowledgeExtractor
# Переменные окружения загружаются автоматически при импорте config


class PDFProcessingPipeline:
    """
    Полный пайплайн обработки PDF документов:
    Хранение → Извлечение → Структурирование → Экспорт
    """
    
    def __init__(self, storage_path: str = "./pdf_documents"):
        """
        Инициализация пайплайна.
        
        Args:
            storage_path: Путь для локального хранения PDF файлов
        """
        # Настраиваем хранилище
        self.storage = DocumentStorage({
            'local_storage_path': storage_path
        })
        
        # Создаем процессор документов
        self.processor = DocumentProcessor(self.storage)
        
        # Создаем экстрактор для текстовых данных
        self.text_extractor = KnowledgeExtractor()
        
        # Результаты обработки
        self.processing_results = []
    
    def add_pdf_from_url(self, pdf_url: str, source_id: str, 
                        metadata: Optional[Dict] = None) -> bool:
        """
        Добавляет PDF документ из URL.
        
        Args:
            pdf_url: URL PDF документа
            source_id: Уникальный идентификатор
            metadata: Дополнительные метаданные
            
        Returns:
            bool: True если документ успешно добавлен
        """
        try:
            doc_ref = self.processor.add_pdf_for_processing(
                source=pdf_url,
                source_id=source_id,
                is_url=True,
                metadata=metadata or {}
            )
            
            print(f"✅ PDF добавлен: {source_id} ({doc_ref.storage_type.value})")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка добавления PDF {source_id}: {e}")
            return False
    
    def add_pdf_from_file(self, file_path: str, source_id: str, 
                         metadata: Optional[Dict] = None) -> bool:
        """
        Добавляет PDF документ из локального файла.
        
        Args:
            file_path: Путь к PDF файлу
            source_id: Уникальный идентификатор
            metadata: Дополнительные метаданные
            
        Returns:
            bool: True если документ успешно добавлен
        """
        try:
            doc_ref = self.processor.add_pdf_for_processing(
                source=file_path,
                source_id=source_id,
                is_url=False,
                metadata=metadata or {}
            )
            
            print(f"✅ PDF добавлен: {source_id} ({doc_ref.storage_type.value})")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка добавления PDF {source_id}: {e}")
            return False
    
    def process_document(self, source_id: str) -> Dict:
        """
        Обрабатывает документ полным пайплайном.
        
        Args:
            source_id: Идентификатор документа
            
        Returns:
            Dict: Результат обработки
        """
        try:
            print(f"🔄 Обработка документа: {source_id}")
            
            # Извлекаем научную нарративу
            result = self.processor.process_document_with_extractor(source_id)
            
            # Получаем метаданные документа
            doc_ref = self.storage.get_document(source_id)
            
            # Формируем результат
            processing_result = {
                'source_id': source_id,
                'storage_info': {
                    'type': doc_ref.storage_type.value,
                    'location': doc_ref.location,
                    'size_mb': round((doc_ref.size_bytes or 0) / (1024 * 1024), 2),
                    'content_hash': doc_ref.content_hash
                } if doc_ref else None,
                'extraction_result': result.model_dump(),
                'summary': {
                    'total_statements': len(result.scientific_narrative),
                    'statement_types': self._get_statement_type_counts(result.scientific_narrative),
                    'total_triples': sum(len(stmt.knowledge_triples) for stmt in result.scientific_narrative)
                }
            }
            
            self.processing_results.append(processing_result)
            
            print(f"✅ Обработка завершена: {len(result.scientific_narrative)} утверждений")
            return processing_result
            
        except Exception as e:
            print(f"❌ Ошибка обработки {source_id}: {e}")
            return {'source_id': source_id, 'error': str(e)}
    
    def _get_statement_type_counts(self, statements) -> Dict[str, int]:
        """Подсчитывает количество утверждений по типам."""
        counts = {}
        for stmt in statements:
            stmt_type = stmt.statement_type
            counts[stmt_type] = counts.get(stmt_type, 0) + 1
        return counts
    
    def process_all_documents(self) -> List[Dict]:
        """
        Обрабатывает все документы в хранилище.
        
        Returns:
            List[Dict]: Результаты обработки всех документов
        """
        all_docs = self.storage.list_documents()
        
        print(f"🚀 Начинаем пакетную обработку {len(all_docs)} документов")
        
        results = []
        for doc_ref in all_docs:
            result = self.process_document(doc_ref.source_id)
            results.append(result)
        
        print(f"🏁 Пакетная обработка завершена: {len(results)} документов")
        return results
    
    def export_results(self, output_file: str = "extraction_results.jsonl") -> str:
        """
        Экспортирует результаты обработки в JSONL файл.
        
        Args:
            output_file: Имя выходного файла
            
        Returns:
            str: Путь к сохраненному файлу
        """
        output_path = pathlib.Path(output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for result in self.processing_results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        print(f"💾 Результаты экспортированы: {output_path.absolute()}")
        return str(output_path.absolute())
    
    def get_pipeline_stats(self) -> Dict:
        """Возвращает статистику пайплайна."""
        storage_stats = self.storage.get_storage_stats()
        
        total_statements = sum(
            result.get('summary', {}).get('total_statements', 0) 
            for result in self.processing_results
        )
        
        total_triples = sum(
            result.get('summary', {}).get('total_triples', 0) 
            for result in self.processing_results
        )
        
        return {
            'storage': storage_stats,
            'processing': {
                'processed_documents': len(self.processing_results),
                'total_statements': total_statements,
                'total_knowledge_triples': total_triples
            }
        }


def workflow_example_1_research_papers():
    """
    Workflow 1: Обработка научных статей о долголетии
    """
    print("📚 Workflow 1: Научные статьи о долголетии")
    print("=" * 50)
    
    # Создаем пайплайн
    pipeline = PDFProcessingPipeline("./longevity_papers")
    
    # Примеры научных статей (реальные URL)
    papers = [
        {
            'url': 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3654510/pdf/nihms-462482.pdf',
            'id': 'caloric_restriction_2013',
            'metadata': {
                'title': 'Caloric Restriction and Human Longevity',
                'topic': 'caloric_restriction',
                'year': 2013,
                'source': 'PMC'
            }
        }
    ]
    
    # Добавляем документы
    for paper in papers:
        pipeline.add_pdf_from_url(
            pdf_url=paper['url'],
            source_id=paper['id'],
            metadata=paper['metadata']
        )
    
    # Обрабатываем все документы
    results = pipeline.process_all_documents()
    
    # Экспортируем результаты
    pipeline.export_results("longevity_papers_results.jsonl")
    
    # Показываем статистику
    stats = pipeline.get_pipeline_stats()
    print("\n📊 Статистика обработки:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


def workflow_example_2_local_files():
    """
    Workflow 2: Обработка локальных PDF файлов
    """
    print("📁 Workflow 2: Локальные PDF файлы")
    print("=" * 50)
    
    # Создаем пайплайн
    pipeline = PDFProcessingPipeline("./local_pdfs")
    
    # Пример обработки локальных файлов
    local_files = [
        {
            'path': '/path/to/aging_research.pdf',
            'id': 'aging_001',
            'metadata': {'topic': 'aging_mechanisms'}
        }
    ]
    
    # Добавляем только существующие файлы
    for file_info in local_files:
        if pathlib.Path(file_info['path']).exists():
            pipeline.add_pdf_from_file(
                file_path=file_info['path'],
                source_id=file_info['id'],
                metadata=file_info['metadata']
            )
        else:
            print(f"⚠️  Файл не найден: {file_info['path']}")
    
    # Обрабатываем документы
    pipeline.process_all_documents()
    
    # Показываем статистику
    stats = pipeline.get_pipeline_stats()
    print(f"📊 Обработано документов: {stats['processing']['processed_documents']}")


def workflow_example_3_batch_processing():
    """
    Workflow 3: Пакетная обработка из конфигурационного файла
    """
    print("⚡ Workflow 3: Пакетная обработка")
    print("=" * 50)
    
    # Создаем конфигурацию документов
    config = {
        'documents': [
            {
                'source': 'https://example.com/paper1.pdf',
                'source_id': 'longevity_paper_1',
                'is_url': True,
                'metadata': {'topic': 'mTOR', 'year': 2024}
            },
            {
                'source': 'https://example.com/paper2.pdf',
                'source_id': 'longevity_paper_2',
                'is_url': True,
                'metadata': {'topic': 'autophagy', 'year': 2024}
            }
        ]
    }
    
    # Создаем пайплайн
    pipeline = PDFProcessingPipeline("./batch_processed")
    
    # Добавляем все документы
    for doc_config in config['documents']:
        if doc_config['is_url']:
            pipeline.add_pdf_from_url(
                pdf_url=doc_config['source'],
                source_id=doc_config['source_id'],
                metadata=doc_config.get('metadata', {})
            )
        else:
            pipeline.add_pdf_from_file(
                file_path=doc_config['source'],
                source_id=doc_config['source_id'],
                metadata=doc_config.get('metadata', {})
            )
    
    # Пакетная обработка
    results = pipeline.process_all_documents()
    
    # Экспорт результатов
    output_file = pipeline.export_results("batch_results.jsonl")
    
    print(f"✅ Пакетная обработка завершена: {len(results)} документов")
    print(f"📄 Результаты: {output_file}")


def main():
    """Запуск примеров workflow."""
    print("🔄 Примеры Workflow для PDF Processing Pipeline")
    print("=" * 60)
    
    # Выбираем workflow
    workflows = [
        ("1", "Научные статьи о долголетии", workflow_example_1_research_papers),
        ("2", "Локальные PDF файлы", workflow_example_2_local_files),
        ("3", "Пакетная обработка", workflow_example_3_batch_processing)
    ]
    
    print("Доступные workflow:")
    for num, description, _ in workflows:
        print(f"  {num}. {description}")
    
    # По умолчанию запускаем третий workflow (демо)
    print(f"\n🚀 Запускаем Workflow 3 (демо)...")
    workflow_example_3_batch_processing()


if __name__ == "__main__":
    main() 