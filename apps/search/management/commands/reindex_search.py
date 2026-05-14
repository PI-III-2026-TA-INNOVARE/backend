from django.core.management.base import BaseCommand

from apps.search.services import reindex_all, upsert_research_index, upsert_researcher_index


class Command(BaseCommand):
    help = 'Reindexa busca hibrida de pesquisadores e pesquisas'

    def add_arguments(self, parser):
        parser.add_argument('--researcher-id', type=int, help='Reindexar um pesquisador especifico')
        parser.add_argument('--research-id', type=int, help='Reindexar uma pesquisa especifica')

    def handle(self, *args, **options):
        researcher_id = options.get('researcher_id')
        research_id = options.get('research_id')

        if researcher_id:
            upsert_researcher_index(researcher_id)
            self.stdout.write(self.style.SUCCESS(f'Pesquisador {researcher_id} reindexado.'))
            return

        if research_id:
            upsert_research_index(research_id)
            self.stdout.write(self.style.SUCCESS(f'Pesquisa {research_id} reindexada.'))
            return

        reindex_all()
        self.stdout.write(self.style.SUCCESS('Reindexacao completa finalizada.'))
