# Generated by Django 3.1.7 on 2021-09-01 06:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0021_stravatokens_valid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='StravaTokens',
            name='expires_at',
            field=models.PositiveIntegerField(default=0, null=True),
        ),
    ]
