from django.db import models

class Ingredients(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название ингредиента'
    )
    unit = models.CharField(
        max_length=100,
        verbose_name='Единица измерения'
    )
    
    def __str__(self):
        return self.name


