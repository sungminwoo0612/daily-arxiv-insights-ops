from src.collector import fetch_latest_papers
from src.storage import DataLake
from src.vector_store import VectorDB

def run_pipeline():
    # 1. 설정
    QUERY = 'cat:cs.AI AND ("Large Language Models" OR "RAG")'
    MAX_RESULTS = 3
    
    # 2. [Extract] 데이터 수집
    papers = fetch_latest_papers(query=QUERY, max_results=MAX_RESULTS)
    if not papers:
        print("No new papers found. Exiting.")
        return

    # 3. [Load - Raw] 원본 데이터 저장 (Data Lake)
    lake = DataLake()
    raw_filepath = lake.save_to_json(papers)

    # 4. [Transform & Load - Vector] 임베딩 및 벡터 DB 저장 (Feature Store)
    # 실제 운영에선 raw_filepath에서 다시 읽어오는 것이 안전하지만, PoC에선 바로 넘깁니다.
    vdb = VectorDB()
    vdb.upsert_papers(papers)
    
    print("\n✅ Pipeline Finished Successfully!")

if __name__ == "__main__":
    run_pipeline()