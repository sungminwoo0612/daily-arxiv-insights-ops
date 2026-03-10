"""
구조화된 연구 메모와 다이제스트를 파일 기반으로 저장하는 모듈
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

from src.schemas import DailyDigest, PaperNote, ResearchProfile


class ResearchMemoryStore:
    def __init__(self, base_path: str = "data/research"):
        self.base_path = Path(base_path)
        self.notes_path = self.base_path / "notes"
        self.digests_path = self.base_path / "digests"
        self.profile_path = self.base_path / "profile.json"

        self.notes_path.mkdir(parents=True, exist_ok=True)
        self.digests_path.mkdir(parents=True, exist_ok=True)

    def save_profile(self, profile: ResearchProfile) -> None:
        self.profile_path.write_text(
            json.dumps(profile.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_profile(self) -> Optional[ResearchProfile]:
        if not self.profile_path.exists():
            return None
        return ResearchProfile.model_validate_json(self.profile_path.read_text(encoding="utf-8"))

    def save_note(self, note: PaperNote) -> None:
        note_path = self.notes_path / f"{self._safe_name(note.paper_id)}.json"
        note_path.write_text(
            json.dumps(note.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def save_notes(self, notes: Iterable[PaperNote]) -> None:
        for note in notes:
            self.save_note(note)

    def list_notes(self) -> List[PaperNote]:
        notes: List[PaperNote] = []
        for note_file in sorted(self.notes_path.glob("*.json")):
            try:
                notes.append(PaperNote.model_validate_json(note_file.read_text(encoding="utf-8")))
            except Exception:
                continue
        notes.sort(key=lambda note: note.published_date, reverse=True)
        return notes

    def get_note(self, paper_id: str) -> Optional[PaperNote]:
        note_path = self.notes_path / f"{self._safe_name(paper_id)}.json"
        if not note_path.exists():
            return None
        return PaperNote.model_validate_json(note_path.read_text(encoding="utf-8"))

    def save_digest(self, digest: DailyDigest) -> None:
        digest_path = self.digests_path / f"{digest.date}.json"
        digest_path.write_text(
            json.dumps(digest.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_latest_digest(self) -> Optional[DailyDigest]:
        digests = sorted(self.digests_path.glob("*.json"))
        if not digests:
            return None
        return DailyDigest.model_validate_json(digests[-1].read_text(encoding="utf-8"))

    def known_paper_ids(self) -> set[str]:
        return {note.paper_id for note in self.list_notes()}

    @staticmethod
    def _safe_name(value: str) -> str:
        return value.replace("/", "_")
