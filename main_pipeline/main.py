# -*- coding: utf-8 -*-
"""
Главный файл системы анализа графа знаний для исследований долголетия
Простая точка входа без сложных конструкций
"""

from pathlib import Path
from datetime import datetime
import os

from graph import ScientificKnowledgeGraph
from analysis import ResearchAnalyst
from processing import load_documents

def create_results_folder():
    """Создает уникальную папку для результатов анализа"""
    # Базовая папка для всех результатов
    base_results_dir = Path("results")
    
    # Создаем базовую папку если её нет
    base_results_dir.mkdir(exist_ok=True)
    
    # Создаем уникальную папку с датой и временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    analysis_dir = base_results_dir / f"analysis_{timestamp}"
    analysis_dir.mkdir(exist_ok=True)
    
    print(f"📁 Создана папка для результатов: {analysis_dir}")
    return analysis_dir

def main():
    """Главная функция запуска системы"""
    # Создаем уникальную папку для результатов
    results_dir = create_results_folder()
    
    # Файлы будут сохраняться в папке результатов
    GRAPH_FILE = results_dir / "longevity_knowledge_graph.graphml"
    REPORT_FILE = results_dir / "research_report.json"
    HIERARCHICAL_REPORT_FILE = results_dir / "hierarchical_research_report.json"
    ENTITY_MAP_FILE = results_dir / "entity_normalization_map.json"
    
    # Настройки для анализа
    FORCE_REBUILD = True  # Установите True для принудительного пересоздания графа
    MAX_WORKERS = 30  # Количество потоков для параллельной обработки
    
    # Путь к документам - ИЗМЕНИТЕ ЗДЕСЬ для другой папки
    PDF_FOLDER = "downloaded_pdfs/references_dlya_statiy_2025"
    USE_CACHE = True  # Установите False для принудительного перечитывания PDF файлов
    
    print("🧬 --- LONGEVITY RESEARCH GRAPH ANALYZER ---")
    print(f"📂 Результаты будут сохранены в: {results_dir}")
    
    # Создаем объект графа знаний
    skg = ScientificKnowledgeGraph()
    
    # Проверяем, нужно ли загружать существующий граф
    # Примечание: теперь каждый запуск создает новый граф, но можно изменить логику
    graph_exists = GRAPH_FILE.exists()
    
    if graph_exists and not FORCE_REBUILD:
        print(f"📁 Найден сохранённый граф: {GRAPH_FILE}")
        if skg.load_graph(str(GRAPH_FILE)):
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
        
        # Загружаем документы из указанной папки
        print(f"📁 Загружаем документы из папки: {PDF_FOLDER}")
        documents = load_documents(data_source=PDF_FOLDER, use_cache=USE_CACHE, max_workers=MAX_WORKERS)
        
        if not documents:
            print("❌ Не найдено документов для обработки!")
            return
        
        print("🧬 --- Stage 1: Building the Knowledge Graph ---")
        skg.build_graph(documents, max_workers=MAX_WORKERS, force_rebuild_normalization=FORCE_REBUILD)
        
        # Сохраняем граф
        if skg.save_graph(str(GRAPH_FILE)):
            stats = skg.get_graph_stats()
            print(f"✅ Граф построен и сохранён: {stats['nodes']} узлов, {stats['edges']} рёбер")
        else:
            print("⚠️ Граф построен, но сохранение не удалось")
        
        # Копируем файл нормализации сущностей в папку результатов
        import shutil
        source_entity_map = "entity_normalization_map.json"
        if Path(source_entity_map).exists():
            try:
                shutil.copy2(source_entity_map, str(ENTITY_MAP_FILE))
                print(f"✅ Карта нормализации сущностей скопирована в: {ENTITY_MAP_FILE}")
            except Exception as e:
                print(f"⚠️ Ошибка копирования карты сущностей: {e}")
        else:
            print("⚠️ Файл нормализации сущностей не найден")
    
    print("\n🔬 --- Stage 2: Analysis and Prioritization ---")
    analyst = ResearchAnalyst(skg)

    print("\n   🌟 -> Divergent Phase: Generating raw research directions...")
    raw_directions = analyst.generate_research_directions(max_workers=MAX_WORKERS)
    print(f"   ✅ Сгенерировано {len(raw_directions)} исходных направлений.")
    
    if raw_directions:
        # Новый вызов иерархического анализа v2.0
        hierarchical_report = analyst.analyze_and_synthesize_report(raw_directions, max_workers=MAX_WORKERS)
        
        # Сохраняем новый иерархический отчет
        if analyst.save_hierarchical_report(hierarchical_report, str(HIERARCHICAL_REPORT_FILE)):
            print(f"✅ Иерархический отчет сохранен в: {HIERARCHICAL_REPORT_FILE}")
        
        # Также сохраняем старый формат для совместимости (только если есть программы)
        if hierarchical_report.programs:
            all_directions = []
            for program in hierarchical_report.programs:
                all_directions.extend(program.component_directions)
            all_directions.extend(hierarchical_report.unclustered_directions)
            
            if analyst.save_report(all_directions, str(REPORT_FILE)):
                print(f"✅ Старый формат отчета сохранен в: {REPORT_FILE}")

        # Выводим новый саммари
        print("\n🏆 --- FINAL HIERARCHICAL REPORT SUMMARY ---")
        print(f"   📈 Всего стратегических программ: {hierarchical_report.total_programs}")
        print(f"   📈 Несгруппированных направлений: {len(hierarchical_report.unclustered_directions)}")
        
        for i, program in enumerate(hierarchical_report.programs):
            print(f"\n   📋 СТРАТЕГИЧЕСКАЯ ПРОГРАММА #{i+1}: {program.program_title}")
            print(f"      📝 Описание: {program.program_summary}")
            print(f"      🔗 Включает идей: {len(program.component_directions)}")
            print(f"      📂 Структурировано в {len(program.subgroups)} подгрупп:")
            
            # Показываем структуру подгрупп
            for j, subgroup in enumerate(program.subgroups):
                print(f"         {j+1}. {subgroup.subgroup_type} ({len(subgroup.directions)} идей)")
                print(f"            {subgroup.subgroup_description}")
                
                # Лучшая идея в подгруппе
                if subgroup.directions:
                    best_in_subgroup = min(subgroup.directions, key=lambda d: d.rank)
                    print(f"            🏆 Топ: {best_in_subgroup.title[:60]}... (скор: {best_in_subgroup.critique.final_score:.2f})")
            
            # Общая лучшая идея в программе
            if program.component_directions:
                best_overall = min(program.component_directions, key=lambda d: d.rank)
                print(f"      🥇 Общий топ программы: {best_overall.title} (скор: {best_overall.critique.final_score:.2f})")
        
        print(f"\n   🔍 Полный иерархический отчет см. в файле: {HIERARCHICAL_REPORT_FILE}")
    else:
        print("   ⚠️ Не найдено направлений для анализа. Проверьте входные данные.")
    
    print(f"\n💾 Результаты сохранены в папке: {results_dir}")
    print(f"   • Граф знаний: {GRAPH_FILE.name}")
    print(f"   • Иерархический отчет v2.0: {HIERARCHICAL_REPORT_FILE.name}")
    print(f"   • Старый формат отчета: {REPORT_FILE.name}")
    print(f"   • Карта нормализации сущностей: {ENTITY_MAP_FILE.name}")
    print("🔄 Для принудительного пересоздания графа установите FORCE_REBUILD = True")

if __name__ == '__main__':
    main() 