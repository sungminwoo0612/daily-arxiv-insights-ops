import json
import os
from datetime import datetime
from typing import List
from src.schemas import ArxivPaper

class DataLake:
    def __init__(self, base_path: str = "data/raw"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def save_to_json(self, papers: List[ArxivPaper], prefix: str = "arxiv_batch"):
        """
        수집된 논문 리스트를 JSON 파일로 저장합니다.
        파일명 포맷: {prefix}_{YYYYMMDD_HHMMSS}.json
        """
        if not papers:
            print("⚠️ No papers to save.")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.json"
        filepath = os.path.join(self.base_path, filename)

        # Pydantic -> Dict -> JSON 변환
        data_dicts = [paper.model_dump(mode='json') for paper in papers]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data_dicts, f, ensure_ascii=False, indent=4)
        
        print(f"💾 [Raw Data] Saved {len(papers)} papers to {filepath}")
        return filepath