from datetime import datetime

from src.research_memory import ResearchMemoryStore
from src.research_service import ResearchNoteBuilder, ResearchService
from src.schemas import ArxivPaper, DailyDigest, DigestEntry, ResearchProfile


def make_paper() -> ArxivPaper:
    return ArxivPaper(
        paper_id="2501.00001",
        title="Agentic Retrieval for Reliable Research Assistants",
        authors=["Alice", "Bob"],
        summary=(
            "This paper studies retrieval augmented generation for research assistants. "
            "It introduces an agentic retrieval planner for adaptive evidence collection. "
            "Experiments show improved grounded answer accuracy and citation faithfulness."
        ),
        published_date=datetime(2025, 1, 5, 12, 0, 0),
        categories=["cs.AI", "cs.IR"],
        pdf_url="https://arxiv.org/pdf/2501.00001",
    )


def make_profile() -> ResearchProfile:
    return ResearchProfile(
        focus_areas=["retrieval augmented generation", "agentic workflows"],
        exclude_topics=["vision only"],
        preferred_queries=['cat:cs.AI AND ("RAG" OR "Agents")'],
        research_program="Prioritize grounded synthesis and minimal-ops research workflows.",
    )


def test_note_builder_creates_structured_note():
    builder = ResearchNoteBuilder()
    note = builder.build(make_paper(), make_profile())

    assert note.paper_id == "2501.00001"
    assert note.relevance_score > 0.3
    assert "retrieval augmented generation" in note.to_retrieval_text().lower()
    assert note.topics


def test_memory_store_roundtrip(tmp_path):
    store = ResearchMemoryStore(base_path=str(tmp_path))
    note = ResearchNoteBuilder().build(make_paper(), make_profile())
    store.save_note(note)

    digest = DailyDigest(
        date="2026-03-10",
        summary="test digest",
        profile_focus=["retrieval augmented generation"],
        entries=[
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
        ],
    )
    store.save_digest(digest)

    loaded_note = store.get_note(note.paper_id)
    loaded_digest = store.load_latest_digest()

    assert loaded_note is not None
    assert loaded_note.title == note.title
    assert loaded_digest is not None
    assert loaded_digest.entries[0].paper_id == note.paper_id


def test_digest_summary_reflects_titles_and_focus():
    entry = DigestEntry(
        paper_id="2501.00001",
        title="Agentic Retrieval for Reliable Research Assistants",
        source_url="https://arxiv.org/pdf/2501.00001",
        published_date=datetime(2025, 1, 5, 12, 0, 0),
        score=0.91,
        why_it_matters="Improves grounded answer quality.",
        relation_to_interests="Directly tied to agentic workflows.",
        read_next="Compare planner design with prior RAG memory systems.",
        topics=["retrieval augmented generation", "agentic workflows"],
    )

    summary = ResearchService._build_digest_summary([entry], make_profile())

    assert "Agentic Retrieval for Reliable Research Assistants" in summary
    assert "retrieval augmented generation" in summary
