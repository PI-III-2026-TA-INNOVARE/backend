from django.core.management.base import BaseCommand

from apps.research.models import Research
from apps.research_candidates.services import run_match_for_research, run_match_for_researcher
from apps.researchers.models import Researcher


class Command(BaseCommand):
    help = 'Executa o match por IA (fase 1) para desafios e pesquisadores.'

    def add_arguments(self, parser):
        parser.add_argument('--research-id', type=int, help='Executa para um desafio especifico.')
        parser.add_argument('--researcher-id', type=int, help='Executa para um pesquisador especifico.')

    def handle(self, *args, **options):
        research_id = options.get('research_id')
        researcher_id = options.get('researcher_id')

        if research_id:
            result = run_match_for_research(research_id)
            self.stdout.write(
                self.style.SUCCESS(
                    f"research={research_id} ok={result.get('ok')} updated={result.get('updated', 0)} removed={result.get('removed', 0)}"
                )
            )
            return

        if researcher_id:
            result = run_match_for_researcher(researcher_id)
            self.stdout.write(
                self.style.SUCCESS(
                    f"researcher={researcher_id} ok={result.get('ok')} updated={result.get('updated', 0)} removed={result.get('removed', 0)}"
                )
            )
            return

        total_research = 0
        total_researcher = 0
        for research in Research.objects.values_list('id_research', flat=True):
            run_match_for_research(research)
            total_research += 1

        for researcher in Researcher.objects.values_list('id_researcher', flat=True):
            run_match_for_researcher(researcher)
            total_researcher += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Match IA executado para {total_research} desafios e {total_researcher} pesquisadores.'
            )
        )
