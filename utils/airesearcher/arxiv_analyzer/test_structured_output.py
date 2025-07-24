#!/usr/bin/env python3
"""
Тест structured output для Gemini API
"""

import asyncio
from openai import OpenAI
from models import SimplePaperAnalysis, FlatPaperAnalysis
from config import GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL


async def test_simple_structured_output():
    """Тестирует простой structured output"""
    print("🧪 Тест простого structured output с Gemini API...")
    
    client = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url=GEMINI_BASE_URL
    )
    
    test_paper_text = """
    Название: "Multi-Agent Systems for Scientific Discovery"
    Абстракт: "This paper presents a framework where multiple AI agents collaborate to analyze scientific literature and identify research gaps."
    """
    
    prompt = f"""
    Проанализируй следующую научную статью и оцени её релевантность для задачи создания автономных исследовательских агентов:
    
    {test_paper_text}
    
    Дай оценку от 0.0 до 1.0 и выдели ключевые инсайты.
    """
    
    try:
        response = client.beta.chat.completions.parse(
            model=GEMINI_MODEL,
            temperature=0.1,
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format=SimplePaperAnalysis
        )
        
        result = response.choices[0].message.parsed
        
        print("✅ Простой structured output работает!")
        print(f"📄 Название: {result.title}")
        print(f"📊 Оценка: {result.overall_score}")
        print(f"💡 Инсайты: {result.key_insights}")
        print(f"🎯 Релевантность: {result.relevance_explanation}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка простого structured output: {e}")
        return False


async def test_flat_analysis():
    """Тестирует FlatPaperAnalysis модель"""
    print("\n🧪 Тест FlatPaperAnalysis с критериями из чек-листа...")
    
    client = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url=GEMINI_BASE_URL
    )
    
    test_paper_text = """
    Название: "Multi-Agent Systems for Scientific Discovery"
    Абстракт: "This paper presents a framework where multiple AI agents collaborate to analyze scientific literature and identify research gaps using LLM-based reasoning."
    """
    
    prompt = f"""
    Проанализируй следующую научную статью по критериям из чек-листа для автономных исследовательских агентов:
    
    {test_paper_text}
    
    Оцени статью по всем критериям из чек-листа от 1 до 5, где:
    1 - не раскрыто
    2 - плохо раскрыто  
    3 - частично раскрыто
    4 - хорошо раскрыто
    5 - отлично раскрыто
    
    Итоговая оценка от 0.0 до 1.0.
    """
    
    try:
        response = client.beta.chat.completions.parse(
            model=GEMINI_MODEL,
            temperature=0.1,
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format=FlatPaperAnalysis
        )
        
        result = response.choices[0].message.parsed
        
        print("✅ FlatPaperAnalysis работает!")
        print(f"📊 Общая оценка: {result.overall_score}")
        print(f"💡 Инсайты: {result.key_insights}")
        print(f"🎯 Релевантность: {result.relevance_to_task}")
        
        # Показываем несколько критериев
        print(f"🔍 Алгоритм поиска: {result.algorithm_search_score}/5")
        print(f"📈 Обоснование релевантности: {result.relevance_justification_score}/5")
        print(f"🏗️ Архитектура агентов: {result.roles_and_sops_score}/5")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка FlatPaperAnalysis: {e}")
        return False


async def main():
    """Запускает все тесты"""
    print("=" * 50)
    print("🧪 ТЕСТЫ STRUCTURED OUTPUT")
    print("=" * 50)
    
    simple_ok = await test_simple_structured_output()
    flat_ok = await test_flat_analysis()
    
    print("\n" + "=" * 50)
    if simple_ok and flat_ok:
        print("✅ Все тесты прошли успешно!")
    else:
        print("❌ Некоторые тесты не прошли")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main()) 