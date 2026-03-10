"""
개인 연구 고도화에 맞춘 핵심 서비스
- 최신 논문 수집
- 구조화된 연구 노트 생성
- 일일 다이제스트 생성
- 로컬 연구 메모 기반 질의응답
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.collector import fetch_latest_papers
from src.config import settings
from src.research_memory import ResearchMemoryStore
from src.schemas import ArxivPaper, DailyDigest, DigestEntry, PaperNote, ResearchProfile
from src.storage import DataLake
from src.vector_store import VectorDB

try:
    from langchain_community.tools import DuckDuckGoSearchRun
except ImportError:
    DuckDuckGoSearchRun = None


class ResearchNoteBuilder:
    def __init__(self):
        self._llm: Optional[ChatOpenAI] = None
        if settings.OPENAI_API_KEY and settings.USE_LLM_NOTE_ENRICHMENT:
            self._llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                temperature=0,
                timeout=settings.LLM_TIMEOUT,
                max_retries=settings.LLM_MAX_RETRIES,
            )

    def build(self, paper: ArxivPaper, profile: ResearchProfile) -> PaperNote:
        if self._llm:
            note = self._build_with_llm(paper, profile)
            if note:
                return note
        return self._build_heuristic(paper, profile)

    def _build_with_llm(self, paper: ArxivPaper, profile: ResearchProfile) -> Optional[PaperNote]:
        prompt = ChatPromptTemplate.from_template(
            """
You are building a structured research note for a personal AI research copilot.
Return strict JSON with keys:
problem, method, key_findings, limitations, why_it_matters, relation_to_interests, read_next, topics, relevance_score.

Research focus:
{focus_areas}

Research program:
{research_program}

Paper title:
{title}

Paper abstract:
{summary}

Paper categories:
{categories}
            """
        )

        chain = prompt | self._llm
        try:
            response = chain.invoke(
                {
                    "focus_areas": ", ".join(profile.focus_areas),
                    "research_program": profile.research_program or "N/A",
                    "title": paper.title,
                    "summary": paper.summary,
                    "categories": ", ".join(paper.categories),
                }
            )
            payload = json.loads(response.content)
            return PaperNote(
                paper_id=paper.paper_id,
                title=paper.title,
                source_url=paper.pdf_url,
                published_date=paper.published_date,
                authors=paper.authors,
                summary=paper.summary,
                problem=payload.get("problem", paper.summary[:180]),
                method=payload.get("method", "Abstract 기반으로 추정 필요"),
                key_findings=self._ensure_list(payload.get("key_findings")),
                limitations=self._ensure_list(payload.get("limitations")),
                why_it_matters=payload.get("why_it_matters", "개인 연구 맥락에서 추가 검토 필요"),
                relation_to_interests=payload.get("relation_to_interests", "연구 관심사와의 연결 검토 필요"),
                read_next=payload.get("read_next", "원문 읽기"),
                topics=self._ensure_list(payload.get("topics")) or self._derive_topics(paper, profile),
                relevance_score=float(payload.get("relevance_score", self._score_relevance(paper, profile))),
            )
        except Exception:
            return None

    def _build_heuristic(self, paper: ArxivPaper, profile: ResearchProfile) -> PaperNote:
        sentences = [sentence.strip() for sentence in paper.summary.split(". ") if sentence.strip()]
        problem = sentences[0] if sentences else paper.summary[:180]
        method = sentences[1] if len(sentences) > 1 else "초록 기반으로만 추정 가능"
        key_findings = sentences[2:4] if len(sentences) > 2 else sentences[:2]
        limitations = [
            "초록만 수집되어 있어 실험 세부사항과 한계는 원문 확인이 필요함.",
        ]
        topics = self._derive_topics(paper, profile)
        relevance_score = self._score_relevance(paper, profile)

        return PaperNote(
            paper_id=paper.paper_id,
            title=paper.title,
            source_url=paper.pdf_url,
            published_date=paper.published_date,
            authors=paper.authors,
            summary=paper.summary,
            problem=problem,
            method=method,
            key_findings=key_findings or [paper.summary[:200]],
            limitations=limitations,
            why_it_matters=self._build_why_it_matters(paper, topics),
            relation_to_interests=self._build_relation_to_interests(paper, profile, topics),
            read_next=self._build_read_next(paper, topics),
            topics=topics,
            relevance_score=relevance_score,
        )

    def _derive_topics(self, paper: ArxivPaper, profile: ResearchProfile) -> List[str]:
        lowered_summary = paper.summary.lower()
        lowered_title = paper.title.lower()
        topics = list(dict.fromkeys(paper.categories))
        for interest in profile.focus_areas:
            if interest.lower() in lowered_summary or interest.lower() in lowered_title:
                topics.append(interest)
        return topics[:8]

    def _score_relevance(self, paper: ArxivPaper, profile: ResearchProfile) -> float:
        lowered_text = f"{paper.title} {paper.summary}".lower()
        positive_hits = sum(1 for interest in profile.focus_areas if interest.lower() in lowered_text)
        negative_hits = sum(1 for topic in profile.exclude_topics if topic.lower() in lowered_text)
        base_score = min(1.0, 0.35 + positive_hits * 0.18)
        penalty = min(0.3, negative_hits * 0.15)
        return max(0.0, round(base_score - penalty, 3))

    def _build_why_it_matters(self, paper: ArxivPaper, topics: List[str]) -> str:
        topic_text = ", ".join(topics[:3]) if topics else "핵심 AI 연구"
        return f"{paper.title}는 {topic_text} 관점에서 바로 비교 읽기 가능한 후보입니다."

    def _build_relation_to_interests(
        self, paper: ArxivPaper, profile: ResearchProfile, topics: List[str]
    ) -> str:
        matched = [interest for interest in profile.focus_areas if interest in topics]
        if matched:
            return f"관심 주제 {', '.join(matched[:3])}와 직접 연결됩니다."
        return "관심 주제와의 직접 연결은 약하지만 탐색용으로 검토할 가치가 있습니다."

    def _build_read_next(self, paper: ArxivPaper, topics: List[str]) -> str:
        if topics:
            return f"{topics[0]} 관련 기존 메모와 함께 원문 실험 섹션을 확인하세요."
        return "원문 실험과 limitation 섹션을 우선 확인하세요."

    @staticmethod
    def _ensure_list(value) -> List[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        if value is None:
            return []
        return [str(value)]


class ResearchService:
    def __init__(self):
        self.data_lake = DataLake(base_path=settings.DATA_LAKE_BASE_PATH)
        self.vector_db = VectorDB(
            db_path=settings.VECTOR_DB_PATH,
            collection_name=settings.VECTOR_DB_COLLECTION_NAME,
            enable_reranker=settings.ENABLE_RERANKER,
        )
        self.memory = ResearchMemoryStore(base_path=settings.RESEARCH_MEMORY_PATH)
        self.note_builder = ResearchNoteBuilder()
        self.web_search = DuckDuckGoSearchRun() if (DuckDuckGoSearchRun and settings.ENABLE_WEB_FALLBACK) else None
        self.answer_llm: Optional[ChatOpenAI] = None
        if settings.OPENAI_API_KEY:
            self.answer_llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                timeout=settings.LLM_TIMEOUT,
                max_retries=settings.LLM_MAX_RETRIES,
            )

    def get_profile(self) -> ResearchProfile:
        stored = self.memory.load_profile()
        if stored:
            return stored

        program_text = ""
        program_path = Path(settings.RESEARCH_PROGRAM_PATH)
        if not program_path.exists():
            repo_root_program = Path(__file__).resolve().parents[2] / settings.RESEARCH_PROGRAM_PATH
            if repo_root_program.exists():
                program_path = repo_root_program
        if program_path.exists():
            program_text = program_path.read_text(encoding="utf-8").strip()

        profile = ResearchProfile(
            focus_areas=settings.RESEARCH_FOCUS_AREAS,
            exclude_topics=settings.RESEARCH_EXCLUDE_TOPICS,
            preferred_queries=[settings.ARXIV_QUERY],
            research_program=program_text,
        )
        self.memory.save_profile(profile)
        return profile

    def refresh_library(self) -> Dict:
        profile = self.get_profile()
        papers = fetch_latest_papers(query=settings.ARXIV_QUERY, max_results=settings.ARXIV_MAX_RESULTS)
        known_ids = self.memory.known_paper_ids()
        new_papers = [paper for paper in papers if paper.paper_id not in known_ids]

        if new_papers:
            self.data_lake.save_to_json(new_papers, prefix="research_batch")
            notes = [self.note_builder.build(paper, profile) for paper in new_papers]
            notes_by_id = {note.paper_id: note for note in notes}
            self.memory.save_notes(notes)
            self.vector_db.upsert_papers(new_papers, notes_by_id=notes_by_id)
        else:
            notes = []

        digest = self.generate_digest()
        return {
            "fetched": len(papers),
            "new_papers": len(new_papers),
            "notes_created": len(notes),
            "digest_entries": len(digest.entries),
            "digest_date": digest.date,
        }

    def generate_digest(self) -> DailyDigest:
        profile = self.get_profile()
        notes = self.memory.list_notes()
        ranked_notes = sorted(notes, key=lambda note: (note.relevance_score, note.published_date), reverse=True)
        entries = [
            DigestEntry(
                paper_id=note.paper_id,
                title=note.title,
                source_url=note.source_url,
                published_date=note.published_date,
                score=note.relevance_score,
                why_it_matters=note.why_it_matters,
                relation_to_interests=note.relation_to_interests,
                read_next=note.read_next,
                topics=note.topics,
            )
            for note in ranked_notes[: settings.DIGEST_MAX_ITEMS]
        ]

        summary = self._build_digest_summary(entries, profile)
        digest = DailyDigest(
            date=datetime.now().date().isoformat(),
            summary=summary,
            entries=entries,
            profile_focus=profile.focus_areas,
        )
        self.memory.save_digest(digest)
        return digest

    def get_latest_digest(self) -> DailyDigest:
        digest = self.memory.load_latest_digest()
        if digest:
            return digest
        return self.generate_digest()

    def list_recent_notes(self, limit: int = 8) -> List[PaperNote]:
        return self.memory.list_notes()[:limit]

    def search_library(self, query: str, n_results: int = 5) -> List[Dict]:
        results = self.vector_db.search(query, n_results=n_results, use_reranker=settings.ENABLE_RERANKER)
        return results

    def answer_query(self, query: str, use_web_search: bool = False) -> tuple[str, List[Dict], Dict]:
        results = self.search_library(query, n_results=settings.RAG_N_RESULTS)
        avg_score = sum(item["score"] for item in results) / len(results) if results else 0.0
        metadata = {
            "strategy": "local_memory",
            "confidence": round(avg_score, 3),
            "web_search_used": False,
        }

        if not results:
            return "저장된 연구 메모에서 관련 논문을 찾지 못했습니다. 먼저 라이브러리를 새로고침하세요.", [], metadata

        if use_web_search and self.web_search and avg_score < settings.LOCAL_CONFIDENCE_THRESHOLD:
            web_context = self._search_web(query)
            if web_context:
                metadata["strategy"] = "local_plus_web"
                metadata["web_search_used"] = True
                answer = self._generate_answer(query, results, web_context=web_context)
                return answer, results, metadata

        answer = self._generate_answer(query, results)
        return answer, results, metadata

    def _generate_answer(self, query: str, results: List[Dict], web_context: str = "") -> str:
        local_context = "\n\n".join(
            [
                "\n".join(
                    [
                        f"Title: {item['metadata'].get('title', 'Unknown')}",
                        f"Published: {item['metadata'].get('date', '')}",
                        f"Topics: {item['metadata'].get('topics', '')}",
                        f"Why It Matters: {item['metadata'].get('why_it_matters', '')}",
                        f"Relation To Interests: {item['metadata'].get('relation_to_interests', '')}",
                        f"Note: {item['content']}",
                    ]
                )
                for item in results
            ]
        )

        if not self.answer_llm:
            top_titles = ", ".join(item["metadata"].get("title", "Unknown") for item in results[:3])
            return (
                f"로컬 연구 메모 기준으로 관련성이 높은 논문은 {top_titles} 입니다. "
                "LLM 응답이 비활성화되어 있어 구조화된 메모 원문을 그대로 확인하는 것을 권장합니다."
            )

        prompt = ChatPromptTemplate.from_template(
            """
You are a personal AI research copilot.
Answer from the local research memory first. If web context is provided, use it only to supplement recency gaps.
Be explicit when a claim comes from local paper notes versus web context.

Research program:
{research_program}

Local research memory:
{local_context}

Web context:
{web_context}

Question:
{question}
            """
        )
        chain = prompt | self.answer_llm
        response = chain.invoke(
            {
                "research_program": self.get_profile().research_program or "N/A",
                "local_context": local_context,
                "web_context": web_context or "N/A",
                "question": query,
            }
        )
        return response.content

    def _search_web(self, query: str) -> str:
        if not self.web_search:
            return ""
        try:
            return self.web_search.run(query)
        except Exception:
            return ""

    @staticmethod
    def _build_digest_summary(entries: List[DigestEntry], profile: ResearchProfile) -> str:
        if not entries:
            return "아직 저장된 연구 메모가 없습니다. 라이브러리를 새로고침해 최신 논문을 가져오세요."
        titles = ", ".join(entry.title for entry in entries[:3])
        focus = ", ".join(profile.focus_areas[:3]) if profile.focus_areas else "핵심 연구 주제"
        return f"오늘의 우선 읽기 논문은 {titles} 입니다. 현재 다이제스트는 {focus} 축에 맞춰 정렬되었습니다."
