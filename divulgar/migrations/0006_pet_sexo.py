# Generated by Django 4.1.7 on 2023-04-08 23:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('divulgar', '0005_rename_telefone_pet_tel'),
    ]

    operations = [
        migrations.AddField(
            model_name='pet',
            name='sexo',
            field=models.CharField(choices=[('M', 'Masculino'), ('F', 'Feminino')], default='M', max_length=1),
            preserve_default=False,
        ),
    ]