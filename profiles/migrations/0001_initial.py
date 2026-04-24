from django.db import migrations, models
import profiles.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.UUIDField(
                    default=profiles.models.generate_uuid_v7,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('name', models.CharField(max_length=255, unique=True)),
                ('gender', models.CharField(
                    choices=[('male', 'Male'), ('female', 'Female')],
                    max_length=10,
                )),
                ('gender_probability', models.FloatField()),
                ('age', models.IntegerField()),
                ('age_group', models.CharField(
                    choices=[
                        ('child', 'Child'),
                        ('teenager', 'Teenager'),
                        ('adult', 'Adult'),
                        ('senior', 'Senior'),
                    ],
                    max_length=20,
                )),
                ('country_id', models.CharField(max_length=2)),
                ('country_name', models.CharField(max_length=100)),
                ('country_probability', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'profiles',
            },
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['gender'], name='profiles_gender_idx'),
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['age_group'], name='profiles_age_group_idx'),
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['country_id'], name='profiles_country_id_idx'),
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['age'], name='profiles_age_idx'),
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['gender_probability'], name='profiles_gender_prob_idx'),
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['country_probability'], name='profiles_country_prob_idx'),
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['created_at'], name='profiles_created_at_idx'),
        ),
    ]
