import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Product


class Command(BaseCommand):
    help = 'Import products from data/ingredients.json.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default=None,
            help='Path to JSON file. Defaults to data/ingredients.json.',
        )

    def handle(self, *args, **options):
        path = options['path']
        if path is None:
            path = settings.BASE_DIR / 'data' / 'ingredients.json'

        try:
            with open(path, encoding='utf-8') as file:
                products = json.load(file)
        except FileNotFoundError as error:
            raise CommandError(f'File not found: {path}') from error
        except json.JSONDecodeError as error:
            raise CommandError(f'Invalid JSON: {path}') from error

        created = 0
        updated = 0
        for item in products:
            fields = item.get('fields', item)
            name = fields.get('name')
            measurement_unit = fields.get('measurement_unit')

            if not name or not measurement_unit:
                self.stderr.write(f'Skipped invalid product: {item}')
                continue

            _, was_created = Product.objects.update_or_create(
                name=name,
                measurement_unit=measurement_unit,
                defaults={
                    'name': name,
                    'measurement_unit': measurement_unit,
                },
            )
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f'Products import finished. Created: {created}. '
                f'Updated: {updated}.'
            )
        )
