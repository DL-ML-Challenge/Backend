# Generated by Django 4.1.7 on 2023-06-23 16:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0006_groupsubmit_error'),
    ]

    operations = [
        migrations.CreateModel(
            name='MLSubmission',
            fields=[
            ],
            options={
                'verbose_name': 'ML Submissions',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('challenge.groupsubmit',),
        ),
    ]
