# Generated by Django 4.2.1 on 2023-05-12 05:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Challenge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='ChallengePhase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.challenge')),
            ],
        ),
        migrations.CreateModel(
            name='GroupSubmit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.DecimalField(decimal_places=20, max_digits=50)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='groups.challengegroup')),
                ('phase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.challengephase')),
            ],
        ),
        migrations.CreateModel(
            name='GroupParticipation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='groups.challengegroup')),
                ('phase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.challengephase')),
            ],
        ),
    ]
