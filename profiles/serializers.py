from rest_framework import serializers
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ')

    class Meta:
        model = Profile
        fields = [
            'id',
            'name',
            'gender',
            'gender_probability',
            'age',
            'age_group',
            'country_id',
            'country_name',
            'country_probability',
            'created_at',
        ]
