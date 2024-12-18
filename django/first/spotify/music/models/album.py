from django.db import models

class Album(models.Model):
    title = models.CharField(max_length=150, blank=False, null=False)
    cover = models.URLField(blank=True)
    