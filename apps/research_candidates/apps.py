from django.apps import AppConfig

class ResearchCandidatesConfig(AppConfig):
    name = 'apps.research_candidates'

    def ready(self):
        from apps.research_candidates import signals  # noqa: F401
