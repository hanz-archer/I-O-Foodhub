# Generated by Django 5.1.4 on 2025-01-16 06:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TriadApp', '0004_item_itemsupply'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='item_id',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name='item',
            unique_together={('item_id', 'stall')},
        ),
    ]
