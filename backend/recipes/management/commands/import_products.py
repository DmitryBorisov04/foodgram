from recipes.management.import_base import BaseImportCommand
from recipes.models import Product


class Command(BaseImportCommand):
    help = 'Import products from fixture.'

    model = Product
    fixture_name = 'ingredients.json'
    fixture_verbose_name = 'products'
