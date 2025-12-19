import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.vector_store import VectorDB
from dotenv import load_dotenv

load_dotenv()

class RAGEngine:
    def __init__(self):
        self.vector_db = VectorDB()
        # LangChain의 ChatOpenAI 사용 (자동으로 LangSmith와 연동됨)
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

    def get_answer(self, query: str):
        # 1. [Retrieve]
        related_papers = self.vector_db.search(query, n_results=3)
        context_text = "\n\n".join([p['content'] for p in related_papers])

        # 2. [Prompt]
        prompt = ChatPromptTemplate.from_template("""
        아래 논문 내용을 바탕으로 질문에 답변하세요:
        {context}
        
        질문: {question}
        """)

        # 3. [Generate] - LangChain Chain 구성
        chain = prompt | self.llm
        
        # 실행 (이 호출이 자동으로 LangSmith에 기록됩니다)
        response = chain.invoke({"context": context_text, "question": query})
        
        return response.content, related_papers