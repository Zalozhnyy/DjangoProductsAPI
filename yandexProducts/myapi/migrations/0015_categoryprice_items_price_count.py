# Generated by Django 3.2.13 on 2022-06-17 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0014_auto_20220617_0719'),
    ]

    operations = [
        migrations.AddField(
            model_name='categoryprice',
            name='items_price_count',
            field=models.IntegerField(default=0),
        ),
    ]
