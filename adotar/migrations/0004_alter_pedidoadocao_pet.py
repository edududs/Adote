# Generated by Django 4.1.7 on 2023-04-06 16:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('divulgar', '0004_alter_pet_raca_alter_pet_usuario'),
        ('adotar', '0003_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedidoadocao',
            name='pet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='divulgar.pet'),
        ),
    ]
