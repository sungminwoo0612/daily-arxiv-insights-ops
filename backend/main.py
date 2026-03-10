from src.research_service import ResearchService

def run_pipeline():
    service = ResearchService()
    result = service.refresh_library()
    print(f"\n✅ Research refresh finished: {result}")

if __name__ == "__main__":
    run_pipeline()
