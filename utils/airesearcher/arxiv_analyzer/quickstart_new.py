#!/usr/bin/env python3
"""
Быстрый старт для анализа PDF файлов из указанной папки
"""

import asyncio
from main import ArxivAnalyzer, analyze_pdf_folder

async def main():
    """Простой пример анализа PDF файлов"""
    
    # Способ 1: Быстрый анализ с помощью функции
    print("🚀 Способ 1: Быстрый анализ")
    results1 = await analyze_pdf_folder("lcgr/downloaded_pdfs/references_dlya_statiy_2025")
    
    print("\n" + "="*60)
    
    # Способ 2: Создание analyzer с кастомной папкой
    print("🚀 Способ 2: Создание analyzer")
    analyzer = ArxivAnalyzer(
        pdf_directory="lcgr/downloaded_pdfs/references_dlya_statiy_2025"
    )
    
    results2 = await analyzer.run_pdf_analysis(
        max_papers=15,
        use_llm_ranking=True
    )
    
    # Показать прогресс
    analyzer.print_progress()

if __name__ == "__main__":
    asyncio.run(main()) 