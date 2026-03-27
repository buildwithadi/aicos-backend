from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    school_subdomain = serializers.CharField(source='school.subdomain', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'school', 'school_name', 'school_subdomain', 'is_staff']
        read_only_fields = ['id', 'school', 'is_staff']