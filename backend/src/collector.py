import arxiv
from typing import List
from src.schemas import ArxivPaper

def fetch_latest_papers(query: str, max_results: int = 5) -> List[ArxivPaper]:
    """
    Arxiv API를 통해 최신 논문을 수집하고 Pydantic 모델 리스트로 반환
    """
    print(f"🔍 Searching ArXiv for: '{query}' (Limit: {max_results})")
    
    # ArXiv 클라이언트 설정
    client = arxiv.Client()
    
    # 검색 객체 설정 (Sort by Submitted Date to get latest)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    papers_data = []
    
    try:
        results = client.results(search)
        
        for r in results:
            # Pydantic 모델로 변환 (Data Validation)
            paper = ArxivPaper(
                paper_id=r.get_short_id(),
                title=r.title,
                authors=[author.name for author in r.authors],
                summary=r.summary.replace("\n", " "), # 줄바꿈 제거 등 간단한 전처리
                published_date=r.published,
                categories=r.categories,
                pdf_url=r.pdf_url
            )
            papers_data.append(paper)
            
        print(f"✅ Successfully fetched {len(papers_data)} papers.")
        return papers_data

    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return []

# --- PoC 테스트 실행 ---
if __name__ == "__main__":
    # LLM, RAG, MLOps 관련 최신 논문 검색 쿼리
    search_keywords = 'cat:cs.AI AND ("Large Language Models" OR "RAG" OR "MLOps")'
    
    papers = fetch_latest_papers(query=search_keywords, max_results=3)
    
    for p in papers:
        print(f"\n[Title] {p.title}")
        print(f"[Date] {p.published_date.strftime('%Y-%m-%d')}")
        print(f"[Link] {p.pdf_url}")
        print("-" * 50)