# Generated by Django 3.2.12 on 2022-02-16 20:25

import colorfield.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DerbyName',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('registered', models.BooleanField(default=False)),
                ('cleared', models.BooleanField(default=False)),
                ('archived', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('meta', models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='DerbyNumber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=64, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('meta', models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='Toot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('toot_id', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('date', models.DateTimeField(blank=True, default=None, null=True)),
                ('reblogs_count', models.IntegerField(default=0)),
                ('favourites_count', models.IntegerField(default=0)),
                ('meta', models.JSONField()),
                ('name', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='names.derbyname')),
            ],
        ),
        migrations.CreateModel(
            name='Jersey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fg_color', colorfield.fields.ColorField(default='#FFFFFF', image_field=None, max_length=18, samples=None)),
                ('bg_color', colorfield.fields.ColorField(default='#000000', image_field=None, max_length=18, samples=None)),
                ('image', models.ImageField(blank=True, null=True, upload_to='jerseys/')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('meta', models.JSONField()),
                ('name', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='names.derbyname')),
            ],
        ),
        migrations.AddField(
            model_name='derbyname',
            name='number',
            field=models.ManyToManyField(blank=True, to='names.DerbyNumber'),
        ),
    ]
