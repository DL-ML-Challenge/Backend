# Generated by Django 4.1.7 on 2023-06-03 03:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0003_alter_challengeuser_user'),
        ('challenge', '0003_challengephase_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupsubmit',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='groups.challengeuser'),
        ),
    ]