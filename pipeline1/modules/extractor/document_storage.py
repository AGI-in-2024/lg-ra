"""
Модуль управления хранением PDF документов для Extractor v2.0
Поддерживает различные стратегии хранения и доступа к документам
"""

import os
import hashlib
import shutil
import pathlib
from typing import Optional, Union, Dict, List
from urllib.parse import urlparse
import httpx
from dataclasses import dataclass
from enum import Enum


class StorageType(Enum):
    """Типы хранилищ документов."""
    LOCAL = "local"
    URL = "url"
    S3 = "s3"
    DATABASE = "database"


@dataclass
class DocumentReference:
    """Ссылка на документ в системе хранения."""
    source_id: str
    storage_type: StorageType
    location: str  # путь, URL, или идентификатор
    filename: Optional[str] = None
    size_bytes: Optional[int] = None
    content_hash: Optional[str] = None
    metadata: Optional[Dict] = None


class DocumentStorage:
    """
    Управляет хранением и доступом к PDF документам.
    
    Поддерживает различные стратегии хранения:
    - Локальная файловая система
    - URL ссылки на внешние документы
    - Облачные хранилища (S3-совместимые)
    - База данных (будущая интеграция)
    """
    
    def __init__(self, storage_config: Optional[Dict] = None):
        """
        Инициализация хранилища документов.
        
        Args:
            storage_config: Конфигурация хранилища
        """
        self.config = storage_config or {}
        self.local_storage_path = pathlib.Path(
            self.config.get('local_storage_path', './documents')
        )
        
        # Создаем директорию для локального хранения
        self.local_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Реестр документов
        self.document_registry: Dict[str, DocumentReference] = {}
    
    def _calculate_file_hash(self, file_path: pathlib.Path) -> str:
        """Вычисляет SHA256 хеш файла."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def store_local_pdf(self, source_path: Union[str, pathlib.Path], 
                       source_id: str, metadata: Optional[Dict] = None) -> DocumentReference:
        """
        Сохраняет PDF файл в локальное хранилище.
        
        Args:
            source_path: Путь к исходному PDF файлу
            source_id: Уникальный идентификатор документа
            metadata: Дополнительные метаданные
            
        Returns:
            DocumentReference: Ссылка на сохраненный документ
        """
        source_path = pathlib.Path(source_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Файл не найден: {source_path}")
        
        # Создаем имя файла на основе source_id
        filename = f"{source_id}.pdf"
        target_path = self.local_storage_path / filename
        
        # Копируем файл
        shutil.copy2(source_path, target_path)
        
        # Вычисляем хеш и размер
        file_hash = self._calculate_file_hash(target_path)
        file_size = target_path.stat().st_size
        
        # Создаем ссылку на документ
        doc_ref = DocumentReference(
            source_id=source_id,
            storage_type=StorageType.LOCAL,
            location=str(target_path),
            filename=filename,
            size_bytes=file_size,
            content_hash=file_hash,
            metadata=metadata or {}
        )
        
        # Регистрируем документ
        self.document_registry[source_id] = doc_ref
        
        return doc_ref
    
    def store_pdf_from_url(self, pdf_url: str, source_id: str, 
                          download_local: bool = True, 
                          metadata: Optional[Dict] = None) -> DocumentReference:
        """
        Регистрирует PDF документ по URL, опционально скачивает локально.
        
        Args:
            pdf_url: URL PDF документа
            source_id: Уникальный идентификатор документа
            download_local: Скачать ли файл локально для кеширования
            metadata: Дополнительные метаданные
            
        Returns:
            DocumentReference: Ссылка на документ
        """
        if download_local:
            # Скачиваем файл локально
            try:
                response = httpx.get(pdf_url, timeout=60.0)
                response.raise_for_status()
                
                filename = f"{source_id}.pdf"
                target_path = self.local_storage_path / filename
                
                with open(target_path, 'wb') as f:
                    f.write(response.content)
                
                file_hash = self._calculate_file_hash(target_path)
                file_size = target_path.stat().st_size
                
                doc_ref = DocumentReference(
                    source_id=source_id,
                    storage_type=StorageType.LOCAL,
                    location=str(target_path),
                    filename=filename,
                    size_bytes=file_size,
                    content_hash=file_hash,
                    metadata={**(metadata or {}), 'original_url': pdf_url}
                )
                
            except Exception as e:
                print(f"Ошибка скачивания {pdf_url}: {e}")
                # Fallback к URL ссылке
                doc_ref = DocumentReference(
                    source_id=source_id,
                    storage_type=StorageType.URL,
                    location=pdf_url,
                    metadata=metadata or {}
                )
        else:
            # Только URL ссылка
            doc_ref = DocumentReference(
                source_id=source_id,
                storage_type=StorageType.URL,
                location=pdf_url,
                metadata=metadata or {}
            )
        
        self.document_registry[source_id] = doc_ref
        return doc_ref
    
    def get_document(self, source_id: str) -> Optional[DocumentReference]:
        """Получает ссылку на документ по ID."""
        return self.document_registry.get(source_id)
    
    def list_documents(self) -> List[DocumentReference]:
        """Возвращает список всех зарегистрированных документов."""
        return list(self.document_registry.values())
    
    def get_document_path_or_url(self, source_id: str) -> Optional[str]:
        """
        Возвращает путь к файлу или URL для обработки.
        
        Args:
            source_id: Идентификатор документа
            
        Returns:
            str: Путь к файлу или URL, None если документ не найден
        """
        doc_ref = self.get_document(source_id)
        if not doc_ref:
            return None
        
        return doc_ref.location
    
    def is_local_file(self, source_id: str) -> bool:
        """Проверяет, является ли документ локальным файлом."""
        doc_ref = self.get_document(source_id)
        return bool(doc_ref and doc_ref.storage_type == StorageType.LOCAL)
    
    def is_url(self, source_id: str) -> bool:
        """Проверяет, является ли документ URL ссылкой."""
        doc_ref = self.get_document(source_id)
        return bool(doc_ref and doc_ref.storage_type == StorageType.URL)
    
    def remove_document(self, source_id: str, delete_file: bool = False) -> bool:
        """
        Удаляет документ из реестра.
        
        Args:
            source_id: Идентификатор документа
            delete_file: Удалить ли физический файл (для локальных файлов)
            
        Returns:
            bool: True если документ был удален
        """
        doc_ref = self.document_registry.get(source_id)
        if not doc_ref:
            return False
        
        if delete_file and doc_ref.storage_type == StorageType.LOCAL:
            file_path = pathlib.Path(doc_ref.location)
            if file_path.exists():
                file_path.unlink()
        
        del self.document_registry[source_id]
        return True
    
    def get_storage_stats(self) -> Dict:
        """Возвращает статистику хранилища."""
        local_count = sum(1 for doc in self.document_registry.values() 
                         if doc.storage_type == StorageType.LOCAL)
        url_count = sum(1 for doc in self.document_registry.values() 
                       if doc.storage_type == StorageType.URL)
        
        total_size = sum(doc.size_bytes or 0 for doc in self.document_registry.values() 
                        if doc.size_bytes)
        
        return {
            'total_documents': len(self.document_registry),
            'local_files': local_count,
            'url_references': url_count,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }


class DocumentProcessor:
    """
    Интегрирует хранилище документов с модулем извлечения.
    """
    
    def __init__(self, storage: DocumentStorage):
        """
        Инициализация процессора документов.
        
        Args:
            storage: Экземпляр хранилища документов
        """
        self.storage = storage
    
    def add_pdf_for_processing(self, source: Union[str, pathlib.Path], 
                              source_id: str, is_url: bool = False,
                              metadata: Optional[Dict] = None) -> DocumentReference:
        """
        Добавляет PDF документ для обработки.
        
        Args:
            source: Путь к файлу или URL
            source_id: Уникальный идентификатор
            is_url: True если source это URL
            metadata: Дополнительные метаданные
            
        Returns:
            DocumentReference: Ссылка на добавленный документ
        """
        if is_url:
            return self.storage.store_pdf_from_url(
                pdf_url=str(source),
                source_id=source_id,
                download_local=True,  # Кешируем локально для быстрого доступа
                metadata=metadata
            )
        else:
            return self.storage.store_local_pdf(
                source_path=source,
                source_id=source_id,
                metadata=metadata
            )
    
    def process_document_with_extractor(self, source_id: str):
        """
        Обрабатывает документ с помощью экстрактора.
        
        Args:
            source_id: Идентификатор документа для обработки
            
        Returns:
            ProcessedDocument: Результат обработки
        """
        from pdf_reader import PDFReader
        
        doc_ref = self.storage.get_document(source_id)
        if not doc_ref:
            raise ValueError(f"Документ {source_id} не найден в хранилище")
        
        reader = PDFReader()
        
        if doc_ref.storage_type == StorageType.LOCAL:
            return reader.extract_scientific_narrative_from_pdf_file(
                file_path=doc_ref.location,
                source_id=source_id
            )
        elif doc_ref.storage_type == StorageType.URL:
            return reader.extract_scientific_narrative_from_pdf_url(
                pdf_url=doc_ref.location,
                source_id=source_id
            )
        else:
            raise NotImplementedError(f"Тип хранилища {doc_ref.storage_type} не поддерживается")


def main():
    """Пример использования системы хранения документов."""
    print("📁 Система хранения PDF документов")
    print("=" * 40)
    
    # Создаем хранилище
    storage = DocumentStorage({
        'local_storage_path': './pdf_documents'
    })
    
    processor = DocumentProcessor(storage)
    
    # Пример добавления документов
    examples = [
        {
            'source': 'https://example.com/longevity_paper.pdf',
            'source_id': 'longevity_001',
            'is_url': True,
            'metadata': {'topic': 'longevity', 'year': 2024}
        }
    ]
    
    for example in examples:
        try:
            print(f"Добавление документа: {example['source_id']}")
            doc_ref = processor.add_pdf_for_processing(**example)
            print(f"✅ Документ добавлен: {doc_ref.storage_type.value}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    # Статистика
    stats = storage.get_storage_stats()
    print(f"\n📊 Статистика хранилища:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main() 