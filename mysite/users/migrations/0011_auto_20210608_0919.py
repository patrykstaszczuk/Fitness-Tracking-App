# Generated by Django 3.1.7 on 2021-06-08 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_auto_20210526_1110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='gender',
            field=models.CharField(choices=[('Male', 'Mężczyzna'), ('Female', 'Kobieta')], default='Male', max_length=6),
        ),
    ]
