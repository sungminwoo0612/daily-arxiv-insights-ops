import torch
from sentence_transformers import SentenceTransformer
from google import genai
from supabase import create_client
import os

# 초기화
device = "cuda" if torch.cuda.is_available() else "cpu"
embed_model = SentenceTransformer('BAAI/bge-m3', device=device) #
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

def get_rag_answer(user_query):
    # 1. 질문 임베딩 생성
    with torch.no_grad():
        query_vector = embed_model.encode(user_query, normalize_embeddings=True).tolist()

    # 2. Supabase에서 관련 논문 검색
    rpc_res = supabase.rpc("match_papers", {
        "query_embedding": query_vector,
        "match_threshold": 0.5,
        "match_count": 3
    }).execute()
    
    contexts = [item['content'] for item in rpc_res.data]
    context_text = "\n\n".join(contexts)

    # 3. Gemini에게 답변 요청
    prompt = f"""
    아래 제공된 최신 논문 정보들을 바탕으로 사용자의 질문에 답변하세요. 
    정보가 부족하다면 모른다고 답하고, 가능한 구체적인 논문 내용을 언급해 주세요.

    [검색된 논문 컨텍스트]
    {context_text}

    [사용자 질문]
    {user_query}
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text