import json
from datetime import datetime

def convert_json_to_md(json_file_path, output_file_path):
    """
    Конвертирует JSON файл в Markdown
    """
    # Читаем JSON файл
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Создаем содержимое Markdown
    markdown_content = []
    
    # Заголовок и общая информация
    markdown_content.append("# Research Report")
    markdown_content.append("")
    markdown_content.append(f"**Generated:** {data['timestamp']}")
    markdown_content.append(f"**Total Programs:** {data['total_programs']}")
    markdown_content.append("")
    
    # Проходим по каждой программе
    for program in data['programs']:
        markdown_content.append(f"## {program['program_title']}")
        markdown_content.append("")
        markdown_content.append(program['program_summary'])
        markdown_content.append("")
        
        # Проходим по подгруппам
        for subgroup in program['subgroups']:
            markdown_content.append(f"### {subgroup['subgroup_type']}")
            markdown_content.append("")
            markdown_content.append(subgroup['subgroup_description'])
            markdown_content.append("")
            
            # Проходим по направлениям
            for direction in subgroup['directions']:
                markdown_content.append(f"#### {direction['rank']}. {direction['title']}")
                markdown_content.append("")
                markdown_content.append("**Description:**")
                markdown_content.append(direction['description'])
                markdown_content.append("")
                
                # Критика и оценки
                critique = direction['critique']
                markdown_content.append("**Critique:**")
                markdown_content.append("")
                markdown_content.append(f"- **Interesting:** {critique['is_interesting']}")
                markdown_content.append(f"- **Novelty Score:** {critique['novelty_score']}")
                markdown_content.append(f"- **Impact Score:** {critique['impact_score']}")
                markdown_content.append(f"- **Feasibility Score:** {critique['feasibility_score']}")
                markdown_content.append(f"- **Final Score:** {critique['final_score']}")
                markdown_content.append(f"- **Recommendation:** {critique['recommendation']}")
                markdown_content.append("")
                
                # Сильные стороны
                if critique['strengths']:
                    markdown_content.append("**Strengths:**")
                    for strength in critique['strengths']:
                        markdown_content.append(f"- {strength}")
                    markdown_content.append("")
                
                # Слабые стороны
                if critique['weaknesses']:
                    markdown_content.append("**Weaknesses:**")
                    for weakness in critique['weaknesses']:
                        markdown_content.append(f"- {weakness}")
                    markdown_content.append("")
                
                # Поддерживающие статьи
                if direction['supporting_papers']:
                    markdown_content.append("**Supporting Papers:**")
                    for paper in direction['supporting_papers']:
                        markdown_content.append(f"- {paper}")
                    markdown_content.append("")
                
                # Тип исследования
                markdown_content.append(f"**Research Type:** {direction['research_type']}")
                markdown_content.append("")
                markdown_content.append("---")
                markdown_content.append("")
    
    # Записываем в файл
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write('\n'.join(markdown_content))
    
    print(f"Конвертация завершена! Markdown файл сохранен как: {output_file_path}")

# Использование скрипта
if __name__ == "__main__":
    # Путь к JSON файлу
    json_file = "public/dataset1/hierarchical_research_report.json"
    
    # Путь для выходного MD файла
    output_file = "research_report.md"
    
    # Конвертируем
    convert_json_to_md(json_file, output_file) 