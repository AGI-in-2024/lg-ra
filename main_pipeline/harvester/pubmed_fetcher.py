import os
import json
from Bio import Entrez
from tqdm import tqdm
from datetime import datetime
import time

# Настройки для API NCBI
Entrez.email = os.getenv("NCBI_EMAIL", "your_email@example.com")
API_KEY = os.getenv("NCBI_API_KEY", None)
if API_KEY:
    Entrez.api_key = API_KEY

def parse_pubmed_article(article):
    """Извлекает нужные поля из одной статьи PubMed."""
    try:
        medline_citation = article['MedlineCitation']
        pmid = str(medline_citation['PMID'])
        
        # Извлекаем заголовок
        article_data = medline_citation['Article']
        title = str(article_data['ArticleTitle'])
        
        # Извлекаем аннотацию
        abstract_parts = article_data.get('Abstract', {}).get('AbstractText', [])
        if isinstance(abstract_parts, list):
            abstract = ' '.join(str(part) for part in abstract_parts)
        else:
            abstract = str(abstract_parts)
        
        # Извлекаем год публикации
        pub_date = article_data.get('ArticleDate', [])
        if pub_date:
            year = int(pub_date[0]['Year'])
        else:
            journal_issue = article_data.get('Journal', {}).get('JournalIssue', {})
            pub_date_info = journal_issue.get('PubDate', {})
            year_str = pub_date_info.get('Year', '')
            if year_str:
                year = int(year_str)
            else:
                year = 2024  # Значение по умолчанию
        
        # Генерируем ссылки
        pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        pmc_url = None
        
        # Проверяем есть ли PMC ID для PDF ссылки
        other_ids = medline_citation.get('OtherID', [])
        for other_id in other_ids:
            if str(other_id).startswith('PMC'):
                pmc_id = str(other_id).replace('PMC', '')
                pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"
                break
        
        if pmid and title and abstract:
            return pmid, {
                "title": title,
                "abstract": abstract,
                "year": year,
                "pubmed_url": pubmed_url,
                "pdf_url": pmc_url,
                "source": "pubmed"
            }
    except Exception:
        pass
    
    return None, None

def search_pubmed_ids(query, start_date, end_date, max_results=200):
    """Выполняет поиск статей в PubMed и возвращает список ID."""
    try:
        handle = Entrez.esearch(
            db="pubmed",
            term=query,
            mindate=start_date,
            maxdate=end_date,
            retmax=max_results,
            usehistory="y"
        )
        search_results = Entrez.read(handle)
        handle.close()
        
        return search_results["WebEnv"], search_results["QueryKey"], int(search_results["Count"])
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return None, None, 0

def fetch_pubmed_articles(webenv, query_key, count, max_results=200):
    """Загружает полные данные статей по найденным ID."""
    documents = {}
    batch_size = 100
    
    for start in tqdm(range(0, min(count, max_results), batch_size), desc="Загрузка статей"):
        try:
            handle = Entrez.efetch(
                db="pubmed",
                rettype="xml",
                retmode="xml",
                retstart=start,
                retmax=batch_size,
                webenv=webenv,
                query_key=query_key
            )
            records = Entrez.read(handle)
            handle.close()
            
            for article in records['PubmedArticle']:
                pmid, data = parse_pubmed_article(article)
                if pmid and data:
                    documents[f"PMID:{pmid}"] = data
            
            time.sleep(0.3)  # Пауза для API
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            continue
    
    return documents

def search_and_fetch_pubmed(query, start_date, end_date, max_results=200):
    """Основная функция: поиск и загрузка статей из PubMed."""
    print(f"Поиск: {query}")
    
    webenv, query_key, count = search_pubmed_ids(query, start_date, end_date, max_results)
    if not webenv:
        return {}
    
    print(f"Найдено {count} статей, загружаю до {max_results}")
    
    if count == 0:
        return {}
    
    return fetch_pubmed_articles(webenv, query_key, count, max_results)

def collect_pubmed_corpus(queries, start_date, end_date, max_results_per_query=250):
    """Собирает корпус статей по списку запросов."""
    all_documents = {}
    
    for query in queries:
        results = search_and_fetch_pubmed(query, start_date, end_date, max_results_per_query)
        all_documents.update(results)
    
    return all_documents

if __name__ == '__main__':
    # Настройки сбора данных
    END_DATE = "2019/12/31"
    START_DATE = "2000/01/01"
    
    # Запросы для поиска
    SEARCH_QUERIES = [
        "(semaglutide[Title/Abstract] OR liraglutide[Title/Abstract]) AND (human[Filter])",
        "(\"GLP-1 receptor agonist\"[Title/Abstract]) AND (mechanism[Title/Abstract]) AND (human[Filter])",
        "(\"cardiovascular aging\"[Title/Abstract]) AND (inflammation[Title/Abstract]) AND (human[Filter])",
        "(\"neurodegeneration\"[Title/Abstract]) AND (metabolism[Title/Abstract]) AND (human[Filter])",
        "(\"longevity pathways\"[Title/Abstract] OR \"healthspan\"[Title/Abstract]) AND (human[Filter])"
    ]
    
    # Сбор корпуса
    corpus = collect_pubmed_corpus(SEARCH_QUERIES, START_DATE, END_DATE, max_results_per_query=250)
    
    print(f"Собрано {len(corpus)} уникальных статей")
    
    # Сохранение
    output_filename = "pubmed_corpus.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)
    
    print(f"Корпус сохранен в {output_filename}") 