# Generated by Django 4.1.7 on 2023-06-03 11:15

import challenge.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0004_groupsubmit_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groupsubmit',
            name='user',
        ),
        migrations.AlterField(
            model_name='groupsubmit',
            name='file',
            field=models.FileField(upload_to=challenge.models.get_submit_file_name),
        ),
    ]
