# Generated by Django 5.1.6 on 2025-05-12 05:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='ransaction_code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
