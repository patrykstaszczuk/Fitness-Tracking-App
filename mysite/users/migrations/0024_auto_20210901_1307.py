# Generated by Django 3.1.7 on 2021-09-01 13:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0023_remove_stravatokens_valid'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='StravaTokens',
            new_name='StravaApi',
        ),
    ]
