from recipes.management.import_base import BaseImportCommand
from recipes.models import Tag


class Command(BaseImportCommand):
    help = 'Import tags from fixture.'

    model = Tag
    fixture_name = 'tags.json'
    fixture_verbose_name = 'tags'
