# Generated by Django 2.2 on 2019-06-05 16:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tom_targets', '0008_merge_20190520_1645'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='targetextra',
            unique_together={('target', 'key')},
        ),
    ]
