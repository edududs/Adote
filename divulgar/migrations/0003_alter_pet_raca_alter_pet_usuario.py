# Generated by Django 4.1.7 on 2023-04-06 15:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('divulgar', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pet',
            name='raca',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='divulgar.raca'),
        ),
        migrations.AlterField(
            model_name='pet',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
