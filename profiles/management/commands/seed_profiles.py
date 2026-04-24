"""
Usage:
    python manage.py seed_profiles --file path/to/profiles.json

The JSON file should be a list of profile objects, each containing:
  name, gender, gender_probability, age, age_group,
  country_id, country_name, country_probability

Re-running is safe — existing names are skipped (no duplicates created).
"""
import json
import sys
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from profiles.models import Profile


def determine_age_group(age: int) -> str:
    if age < 13:
        return 'child'
    elif age < 18:
        return 'teenager'
    elif age < 65:
        return 'adult'
    else:
        return 'senior'


class Command(BaseCommand):
    help = 'Seed the database with profiles from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to the JSON file containing profiles',
        )

    def handle(self, *args, **options):
        filepath = options['file']

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'File not found: {filepath}')
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON: {e}')

        if not isinstance(data, list):
            raise CommandError('JSON file must contain a list of profile objects')

        self.stdout.write(f'Loaded {len(data)} records from file.')

        # Fetch all existing names in one query to avoid N+1
        existing_names = set(
            Profile.objects.values_list('name', flat=True)
        )
        self.stdout.write(f'Existing records in DB: {len(existing_names)}')

        to_create = []
        skipped = 0
        errors = 0

        for i, record in enumerate(data):
            try:
                name = str(record.get('name', '')).strip().lower()
                if not name:
                    self.stdout.write(self.style.WARNING(f'Row {i}: missing name, skipping'))
                    errors += 1
                    continue

                if name in existing_names:
                    skipped += 1
                    continue

                gender = str(record.get('gender', '')).lower()
                if gender not in ('male', 'female'):
                    self.stdout.write(self.style.WARNING(f'Row {i}: invalid gender "{gender}", skipping'))
                    errors += 1
                    continue

                age = record.get('age')
                if age is None:
                    self.stdout.write(self.style.WARNING(f'Row {i}: missing age, skipping'))
                    errors += 1
                    continue
                age = int(age)

                # age_group: use from data if valid, otherwise derive from age
                age_group = str(record.get('age_group', '')).lower()
                if age_group not in ('child', 'teenager', 'adult', 'senior'):
                    age_group = determine_age_group(age)

                country_id = str(record.get('country_id', '')).upper()[:2]
                country_name = str(record.get('country_name', ''))
                gender_probability = float(record.get('gender_probability', 0.0))
                country_probability = float(record.get('country_probability', 0.0))

                profile = Profile(
                    name=name,
                    gender=gender,
                    gender_probability=gender_probability,
                    age=age,
                    age_group=age_group,
                    country_id=country_id,
                    country_name=country_name,
                    country_probability=country_probability,
                )
                to_create.append(profile)
                existing_names.add(name)  # prevent dups within the file itself

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Row {i}: error — {e}, skipping'))
                errors += 1

        if to_create:
            with transaction.atomic():
                # bulk_create with ignore_conflicts as final safety net
                created = Profile.objects.bulk_create(to_create, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(
                f'Done. Created: {len(created)} | Skipped (already exist): {skipped} | Errors: {errors}'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Nothing to insert. Skipped: {skipped} | Errors: {errors}'
            ))
