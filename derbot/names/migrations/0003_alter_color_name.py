# Generated by Django 3.2.12 on 2022-02-17 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('names', '0002_auto_20220217_1208'),
    ]

    operations = [
        migrations.AlterField(
            model_name='color',
            name='name',
            field=models.CharField(max_length=64),
        ),
    ]
