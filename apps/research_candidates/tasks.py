from celery import shared_task
from apps.research_candidates.services import run_match_for_research, run_match_for_researcher

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def run_match_for_research_task(self, research_id):
    return run_match_for_research(research_id)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def run_match_for_researcher_task(self, researcher_id):
    return run_match_for_researcher(researcher_id)
