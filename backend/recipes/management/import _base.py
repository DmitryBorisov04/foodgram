import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class BaseImportCommand(BaseCommand):
    model = None
    fixture_name = None
    fixture_verbose_name = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default=settings.BASE_DIR / 'data' / self.fixture_name,
            help=f'Path to {self.fixture_name}.',
        )

    def get_fields(self, item):
        return item.get('fields', item)

    def handle(self, *args, **options):
        try:
            with open(options['path'], encoding='utf-8') as file:
                old_count = self.model.objects.count()
                self.model.objects.bulk_create(
                    self.model(**self.get_fields(item))
                    for item in json.load(file)
                )
                created = self.model.objects.count() - old_count

            self.stdout.write(
                self.style.SUCCESS(
                    f'Fixture {self.fixture_name} imported. '
                    f'Created: {created}.'
                )
            )
        except Exception as error:
            raise CommandError(
                f'Import fixture {self.fixture_name} failed: {error}'
            ) from error
