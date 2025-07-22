#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для управления графами знаний
"""

import os
import sys
from pathlib import Path
import networkx as nx
from datetime import datetime

def show_graph_info(graph_file="longevity_knowledge_graph.graphml"):
    """Показывает информацию о сохранённом графе."""
    graph_path = Path(graph_file)
    
    if not graph_path.exists():
        print(f"❌ Граф не найден: {graph_path}")
        return
    
    try:
        # Загружаем граф
        graph = nx.read_graphml(graph_path)
        
        # Получаем статистику файла
        file_size = graph_path.stat().st_size
        modified_time = datetime.fromtimestamp(graph_path.stat().st_mtime)
        
        print(f"📊 ИНФОРМАЦИЯ О ГРАФЕ: {graph_path}")
        print(f"   📁 Размер файла: {file_size:,} байт ({file_size/1024:.1f} KB)")
        print(f"   🕒 Последнее изменение: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   🔗 Узлов: {graph.number_of_nodes():,}")
        print(f"   🔗 Рёбер: {graph.number_of_edges():,}")
        
        # Детальная статистика по типам узлов
        node_types = {}
        for node_id, data in graph.nodes(data=True):
            node_type = data.get('type', 'Unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print(f"\n   📋 Типы узлов:")
        for node_type, count in sorted(node_types.items()):
            print(f"      • {node_type}: {count:,}")
        
        # Статистика по типам рёбер
        edge_types = {}
        for u, v, data in graph.edges(data=True):
            edge_type = data.get('type', 'Unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        print(f"\n   🔗 Типы связей:")
        for edge_type, count in sorted(edge_types.items()):
            print(f"      • {edge_type}: {count:,}")
            
    except Exception as e:
        print(f"❌ Ошибка чтения графа: {e}")

def list_graph_files():
    """Показывает все файлы графов в текущей папке."""
    current_dir = Path(".")
    graph_files = list(current_dir.glob("*.graphml"))
    
    if not graph_files:
        print("📁 Файлы графов (*.graphml) не найдены в текущей папке")
        return
    
    print("📁 НАЙДЕННЫЕ ГРАФЫ:")
    for graph_file in sorted(graph_files):
        file_size = graph_file.stat().st_size
        modified_time = datetime.fromtimestamp(graph_file.stat().st_mtime)
        print(f"   • {graph_file.name}")
        print(f"     Размер: {file_size/1024:.1f} KB, Изменён: {modified_time.strftime('%Y-%m-%d %H:%M')}")

def delete_graph(graph_file="longevity_knowledge_graph.graphml"):
    """Удаляет граф с подтверждением."""
    graph_path = Path(graph_file)
    
    if not graph_path.exists():
        print(f"❌ Граф не найден: {graph_path}")
        return
    
    print(f"⚠️ Вы действительно хотите удалить граф: {graph_path}?")
    response = input("Введите 'yes' для подтверждения: ").lower().strip()
    
    if response == 'yes':
        try:
            graph_path.unlink()
            print(f"✅ Граф удалён: {graph_path}")
        except Exception as e:
            print(f"❌ Ошибка удаления: {e}")
    else:
        print("❌ Удаление отменено")

def backup_graph(graph_file="longevity_knowledge_graph.graphml"):
    """Создаёт резервную копию графа."""
    graph_path = Path(graph_file)
    
    if not graph_path.exists():
        print(f"❌ Граф не найден: {graph_path}")
        return
    
    # Создаём имя резервной копии с временной меткой
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{graph_path.stem}_backup_{timestamp}.graphml"
    backup_path = graph_path.parent / backup_name
    
    try:
        # Копируем файл
        import shutil
        shutil.copy2(graph_path, backup_path)
        print(f"✅ Резервная копия создана: {backup_path}")
    except Exception as e:
        print(f"❌ Ошибка создания резервной копии: {e}")

def main():
    """Главное меню утилиты."""
    if len(sys.argv) < 2:
        print("🔧 УТИЛИТА УПРАВЛЕНИЯ ГРАФАМИ ЗНАНИЙ")
        print("\nИспользование:")
        print("  python graph_manager.py info [файл.graphml]     - информация о графе")
        print("  python graph_manager.py list                   - список всех графов")
        print("  python graph_manager.py delete [файл.graphml]  - удалить граф")
        print("  python graph_manager.py backup [файл.graphml]  - создать резервную копию")
        print("\nЕсли файл не указан, используется: longevity_knowledge_graph.graphml")
        return
    
    command = sys.argv[1].lower()
    graph_file = sys.argv[2] if len(sys.argv) > 2 else "longevity_knowledge_graph.graphml"
    
    if command == "info":
        show_graph_info(graph_file)
    elif command == "list":
        list_graph_files()
    elif command == "delete":
        delete_graph(graph_file)
    elif command == "backup":
        backup_graph(graph_file)
    else:
        print(f"❌ Неизвестная команда: {command}")
        print("Доступные команды: info, list, delete, backup")

if __name__ == "__main__":
    main() 