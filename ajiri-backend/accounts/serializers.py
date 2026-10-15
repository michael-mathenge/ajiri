from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ('email', 'password', 'full_name', 'phone_number')

    def validate_password(self, value):
        # Field validation still runs when another field (e.g. duplicate email) fails.
        # see docs/CONCEPTS.md#password-validation
        identity = {key: self.initial_data.get(key, '') for key in ('email', 'full_name')}
        candidate = User(**{key: item if isinstance(item, str) else '' for key, item in identity.items()})
        try:
            validate_password(value, candidate)
        except ValidationError as error:
            raise serializers.ValidationError(error.messages)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)