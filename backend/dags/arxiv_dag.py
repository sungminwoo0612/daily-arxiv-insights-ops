import sys
import os

# /opt/airflow/dags/src 폴더를 직접 참조할 수 있도록 설정
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# src 폴더를 경로에 추가하여 기존 로직 임포트
sys.path.append('/opt/airflow/dags')
from src.collector import fetch_latest_papers
from src.storage import DataLake
from src.vector_store import VectorDB

def run_arxiv_pipeline():
    """기존에 만든 수집-저장-임베딩 로직 실행"""
    QUERY = 'cat:cs.AI AND ("Large Language Models" OR "RAG")'
    
    # 1. 수집
    papers = fetch_latest_papers(query=QUERY, max_results=5)
    if not papers:
        return "No new papers"

    # 2. Raw 저장
    lake = DataLake(base_path="/opt/airflow/data/raw")
    lake.save_to_json(papers)

    # 3. Vector DB 적재
    vdb = VectorDB(db_path="/opt/airflow/data/vectordb")
    vdb.upsert_papers(papers)
    
    return f"Successfully processed {len(papers)} papers"

# DAG 기본 설정
default_args = {
    'owner': 'sungmin',
    'depends_on_past': False,
    'start_date': datetime(2023, 12, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'arxiv_daily_collector',
    default_args=default_args,
    description='매일 최신 논문을 수집하여 Vector DB에 반영합니다',
    schedule_interval='@daily', # 매일 00:00 실행
    catchup=False
) as dag:

    collect_task = PythonOperator(
        task_id='fetch_and_index_papers',
        python_callable=run_arxiv_pipeline,
    )