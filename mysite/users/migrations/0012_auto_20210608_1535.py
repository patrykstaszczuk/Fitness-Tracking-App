# Generated by Django 3.1.7 on 2021-06-08 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_auto_20210608_0919'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='sex',
            field=models.CharField(choices=[('Male', 'Mężczyzna'), ('Female', 'Kobieta')], max_length=6),
        ),
    ]