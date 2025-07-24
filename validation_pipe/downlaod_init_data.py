#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для скачивания начальных данных из Google Drive
Простой код для junior разработчиков
"""

import os
import pathlib
import gdown
import json
from typing import Dict, List

# Конфигурация по умолчанию
DEFAULT_CONFIG = {
    "google_drive_folder_url": "https://drive.google.com/drive/folders/1OAECK_1YX0NCqcTLMewNZRgoPKCKYfgt",
    "input_pdf_count": 20,  # Количество PDF для папки input
    "predict_pdf_count": 1,  # Количество PDF для папки topredict
    "download_timeout": 60   # Таймаут скачивания в секундах
}

class DataDownloader:
    """Класс для скачивания данных из Google Drive"""
    
    def __init__(self, config: Dict = None):
        """Инициализация загрузчика"""
        self.config = config or DEFAULT_CONFIG
        
        # Пути к папкам
        self.base_dir = pathlib.Path("data/dataset2")
        self.input_dir = self.base_dir / "input"
        self.topredict_dir = self.base_dir / "topredict"
        self.temp_dir = self.base_dir / "temp"
        
        # Создаем папки
        self.create_directories()
        
        print("✅ Загрузчик данных инициализирован")
    
    def create_directories(self):
        """Создает необходимые папки"""
        directories = [self.input_dir, self.topredict_dir, self.temp_dir]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"📁 Создана папка: {directory}")
    
    def extract_folder_id(self, url: str) -> str:
        """Извлекает ID папки из URL Google Drive"""
        try:
            # Извлекаем ID из URL вида: https://drive.google.com/drive/folders/FOLDER_ID
            if "folders/" in url:
                folder_id = url.split("folders/")[1].split("?")[0]
                return folder_id
            else:
                print("❌ Неверный формат URL Google Drive папки")
                return None
        except Exception as e:
            print(f"❌ Ошибка извлечения ID папки: {e}")
            return None
    
    def download_folder(self, folder_url: str) -> bool:
        """Скачивает папку с Google Drive"""
        try:
            folder_id = self.extract_folder_id(folder_url)
            if not folder_id:
                return False
            
            print(f"🔗 Скачивание папки с ID: {folder_id}")
            
            # Скачиваем папку в temp директорию
            download_path = str(self.temp_dir)
            
            try:
                gdown.download_folder(
                    id=folder_id,
                    output=download_path,
                    quiet=False,
                    use_cookies=False
                )
                print("✅ Папка скачана успешно")
                return True
                
            except Exception as e:
                print(f"❌ Ошибка скачивания папки через gdown: {e}")
                print("💡 Попробуем альтернативный метод...")
                return self.download_folder_alternative(folder_id)
                
        except Exception as e:
            print(f"❌ Ошибка скачивания: {e}")
            return False
    
    def download_folder_alternative(self, folder_id: str) -> bool:
        """Альтернативный метод скачивания"""
        try:
            # Используем прямую ссылку на zip архив
            zip_url = f"https://drive.google.com/uc?id={folder_id}&export=download"
            output_file = self.temp_dir / "downloaded_folder.zip"
            
            print(f"📦 Скачивание ZIP архива...")
            gdown.download(zip_url, str(output_file), quiet=False)
            
            # Распаковываем архив
            import zipfile
            with zipfile.ZipFile(output_file, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            # Удаляем zip файл
            output_file.unlink()
            
            print("✅ Альтернативное скачивание успешно")
            return True
            
        except Exception as e:
            print(f"❌ Альтернативное скачивание не удалось: {e}")
            return False
    
    def find_pdf_files(self) -> List[pathlib.Path]:
        """Находит все PDF файлы в скачанной папке"""
        pdf_files = []
        
        # Ищем PDF файлы в temp папке
        for pdf_file in self.temp_dir.rglob("*.pdf"):
            pdf_files.append(pdf_file)
        
        print(f"📄 Найдено PDF файлов: {len(pdf_files)}")
        return pdf_files
    
    def organize_files(self, pdf_files: List[pathlib.Path]) -> bool:
        """Организует скачанные файлы по папкам"""
        try:
            if len(pdf_files) == 0:
                print("❌ PDF файлы не найдены")
                return False
            
            # Определяем сколько файлов скачано
            total_files = len(pdf_files)
            input_count = min(self.config["input_pdf_count"], total_files - 1)  # Оставляем 1 для predict
            predict_count = min(self.config["predict_pdf_count"], total_files - input_count)
            
            print(f"📊 Организация файлов:")
            print(f"   - В папку input: {input_count} файлов")
            print(f"   - В папку topredict: {predict_count} файлов")
            
            # Копируем файлы в input
            for i in range(input_count):
                source_file = pdf_files[i]
                target_file = self.input_dir / f"research_paper_{i+1:02d}.pdf"
                
                # Копируем файл
                import shutil
                shutil.copy2(source_file, target_file)
                print(f"📄 Скопирован: {target_file.name}")
            
            # Копируем файлы в topredict
            for i in range(predict_count):
                source_file = pdf_files[input_count + i]
                target_file = self.topredict_dir / f"validation_paper_{i+1:02d}.pdf"
                
                # Копируем файл
                import shutil
                shutil.copy2(source_file, target_file)
                print(f"📄 Скопирован для валидации: {target_file.name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка организации файлов: {e}")
            return False
    
    def cleanup_temp(self):
        """Очищает временную папку"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print("🧹 Временная папка очищена")
        except Exception as e:
            print(f"⚠️ Ошибка очистки временной папки: {e}")
    
    def create_sample_report(self):
        """Создает пример отчета если его нет"""
        report_file = self.input_dir / "hierarchical_research_report.json"
        
        if report_file.exists():
            print("📊 Отчет уже существует")
            return
        
        # Создаем пример отчета
        sample_report = {
            "timestamp": "2025-01-24T12:00:00.000000",
            "total_programs": 1,
            "programs": [
                {
                    "program_title": "Валидация исследований долголетия",
                    "program_summary": "Программа для валидации и анализа научных исследований",
                    "subgroups": [
                        {
                            "subgroup_type": "Биологические исследования",
                            "subgroup_description": "Анализ биологических механизмов и процессов",
                            "directions": [
                                {
                                    "rank": 1,
                                    "title": "Молекулярные механизмы старения",
                                    "description": "Исследование фундаментальных процессов старения на молекулярном уровне",
                                    "research_type": "Фундаментальное исследование",
                                    "critique": {
                                        "is_interesting": True,
                                        "novelty_score": 8.5,
                                        "impact_score": 9.0,
                                        "feasibility_score": 7.5,
                                        "final_score": 8.3,
                                        "recommendation": "Настоятельно рекомендуется"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(sample_report, f, ensure_ascii=False, indent=2)
            print("📊 Создан пример отчета для валидации")
        except Exception as e:
            print(f"❌ Ошибка создания отчета: {e}")
    
    def run_download(self) -> bool:
        """Запускает полный процесс скачивания"""
        print("🚀 Запуск скачивания данных...")
        print(f"🔗 Источник: {self.config['google_drive_folder_url']}")
        
        # 1. Скачиваем папку
        success = self.download_folder(self.config["google_drive_folder_url"])
        if not success:
            print("❌ Не удалось скачать данные")
            return False
        
        # 2. Находим PDF файлы
        pdf_files = self.find_pdf_files()
        if not pdf_files:
            print("❌ PDF файлы не найдены в скачанных данных")
            return False
        
        # 3. Организуем файлы
        success = self.organize_files(pdf_files)
        if not success:
            print("❌ Не удалось организовать файлы")
            return False
        
        # 4. Создаем пример отчета
        self.create_sample_report()
        
        # 5. Очищаем временные файлы
        self.cleanup_temp()
        
        print("✅ Скачивание данных завершено успешно!")
        return True


def load_config() -> Dict:
    """Загружает конфигурацию из файла или использует по умолчанию"""
    config_file = pathlib.Path("download_config.json")
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ Загружена конфигурация из {config_file}")
            return config
        except Exception as e:
            print(f"⚠️ Ошибка загрузки конфигурации: {e}")
            print("💡 Используется конфигурация по умолчанию")
    
    return DEFAULT_CONFIG


def save_config(config: Dict):
    """Сохраняет конфигурацию в файл"""
    config_file = pathlib.Path("download_config.json")
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"💾 Конфигурация сохранена в {config_file}")
    except Exception as e:
        print(f"❌ Ошибка сохранения конфигурации: {e}")


def main():
    """Главная функция"""
    print("📦 Загрузчик данных для валидации")
    print("=" * 50)
    
    # Проверяем зависимости
    try:
        import gdown
    except ImportError:
        print("❌ Библиотека gdown не установлена")
        print("📦 Установите: pip install gdown")
        return
    
    # Загружаем конфигурацию
    config = load_config()
    
    # Создаем и запускаем загрузчик
    downloader = DataDownloader(config)
    success = downloader.run_download()
    
    if success:
        print("\n🎉 Данные готовы для валидации!")
        print("📁 Структура данных:")
        print("   - data/dataset2/input/ - файлы для обучения")
        print("   - data/dataset2/topredict/ - файлы для валидации")
        print("\n🚀 Запустите валидацию: python run_validation.py")
    else:
        print("\n❌ Скачивание не удалось")


if __name__ == "__main__":
    main()
