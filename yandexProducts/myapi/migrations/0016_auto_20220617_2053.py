# Generated by Django 3.2.13 on 2022-06-17 20:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0015_categoryprice_items_price_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceCalculation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category_items_count', models.IntegerField(default=0)),
                ('items_price_count', models.IntegerField(default=0)),
            ],
        ),
        migrations.DeleteModel(
            name='CategoryPrice',
        ),
        migrations.AddField(
            model_name='itemmodel',
            name='price_info',
            field=models.OneToOneField(auto_created=True, default=None, on_delete=django.db.models.deletion.CASCADE, to='myapi.pricecalculation'),
            preserve_default=False,
        ),
    ]