import sys
import os

# backend 디렉토리를 sys.path에 추가
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from src.reranker import RerankerFactory
from src.config import settings
import time

def test_all_rerankers():
    """모든 reranker 테스트"""
    
    # 더미 문서
    docs = [
        {
            "content": "RAG combines retrieval with generation for better LLM outputs",
            "metadata": {"title": "RAG Overview"},
            "score": 0.8
        },
        {
            "content": "Vector databases store embeddings for similarity search",
            "metadata": {"title": "Vector DB"},
            "score": 0.6
        },
        {
            "content": "Transformers revolutionized natural language processing",
            "metadata": {"title": "Transformers"},
            "score": 0.7
        }
    ]
    
    query = "What is retrieval augmented generation?"
    
    # 테스트할 reranker 목록
    strategies = ["hybrid", "cohere", "bge"]
    
    results = {}
    
    for strategy in strategies:
        print(f"\n{'='*50}")
        print(f"Testing: {strategy.upper()}")
        print('='*50)
        
        try:
            reranker = RerankerFactory.create(strategy)
            
            start = time.time()
            reranked = reranker.rerank(query, docs, top_k=3)
            duration = time.time() - start
            
            results[strategy] = {
                "success": True,
                "duration": duration,
                "top_result": reranked[0].metadata["title"]
            }
            
            print(f"✅ Success ({duration:.3f}s)")
            for i, r in enumerate(reranked):
                print(f"  [{i+1}] Score: {r.score:.3f} - {r.metadata['title']}")
        
        except Exception as e:
            results[strategy] = {"success": False, "error": str(e)}
            print(f"❌ Failed: {e}")
    
    # 요약
    print(f"\n{'='*50}")
    print("SUMMARY")
    print('='*50)
    for strategy, result in results.items():
        if result["success"]:
            print(f"{strategy:10} ✅ {result['duration']:.3f}s - {result['top_result']}")
        else:
            print(f"{strategy:10} ❌ {result['error']}")

if __name__ == "__main__":
    test_all_rerankers()