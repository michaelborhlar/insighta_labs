import time
import uuid
import os
from django.db import models


def generate_uuid_v7():
    """
    Generate a UUID version 7 (time-ordered).
    Format: 48-bit unix_ts_ms | 4-bit ver(7) | 12-bit rand_a | 2-bit var | 62-bit rand_b
    """
    timestamp_ms = int(time.time() * 1000)

    # 48 bits of millisecond timestamp
    ts_hex = f'{timestamp_ms:012x}'

    # 12 bits of random data for rand_a (after version nibble)
    rand_a = os.urandom(2)
    rand_a_int = int.from_bytes(rand_a, 'big') & 0x0FFF  # 12 bits

    # 62 bits of random data for rand_b (after variant bits)
    rand_b = os.urandom(8)
    rand_b_int = int.from_bytes(rand_b, 'big')
    # Set variant bits: top 2 bits = 10
    rand_b_int = (rand_b_int & 0x3FFFFFFFFFFFFFFF) | 0x8000000000000000

    # Assemble: 48-bit ts | 0111 (ver=7) | 12-bit rand_a | variant+rand_b
    uuid_int = (
        (timestamp_ms << 80) |
        (0x7 << 76) |
        (rand_a_int << 64) |
        rand_b_int
    )

    return uuid.UUID(int=uuid_int)


class Profile(models.Model):
    AGE_GROUP_CHOICES = [
        ('child', 'Child'),
        ('teenager', 'Teenager'),
        ('adult', 'Adult'),
        ('senior', 'Senior'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=generate_uuid_v7,
        editable=False
    )
    name = models.CharField(max_length=255, unique=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    gender_probability = models.FloatField()
    age = models.IntegerField()
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES)
    country_id = models.CharField(max_length=2)
    country_name = models.CharField(max_length=100)
    country_probability = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'profiles'
        indexes = [
            models.Index(fields=['gender']),
            models.Index(fields=['age_group']),
            models.Index(fields=['country_id']),
            models.Index(fields=['age']),
            models.Index(fields=['gender_probability']),
            models.Index(fields=['country_probability']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.name} ({self.gender}, {self.age})'
