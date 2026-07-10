import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Tag


class Command(BaseCommand):
    help = 'Import tags from data/tags.json.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default=None,
            help='Path to JSON file. Defaults to data/tags.json.',
        )

    def handle(self, *args, **options):
        path = options['path']
        if path is None:
            path = settings.BASE_DIR / 'data' / 'tags.json'

        try:
            with open(path, encoding='utf-8') as file:
                tags = json.load(file)
        except FileNotFoundError as error:
            raise CommandError(f'File not found: {path}') from error
        except json.JSONDecodeError as error:
            raise CommandError(f'Invalid JSON: {path}') from error

        created = 0
        updated = 0
        for item in tags:
            fields = item.get('fields', item)
            name = fields.get('name')
            slug = fields.get('slug')

            if not name or not slug:
                self.stderr.write(f'Skipped invalid tag: {item}')
                continue

            _, was_created = Tag.objects.update_or_create(
                slug=slug,
                defaults={'name': name},
            )
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f'Tags import finished. Created: {created}. '
                f'Updated: {updated}.'
            )
        )
