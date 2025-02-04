# Generated by Django 5.1.4 on 2024-12-20 11:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0002_album_artist_song_album'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='listened',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='song',
            name='album',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='music.album'),
        ),
    ]
