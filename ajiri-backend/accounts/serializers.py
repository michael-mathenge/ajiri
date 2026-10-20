from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

PRIVACY_POLICY_VERSION = 'privacy-draft-v1'


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    privacy_consent = serializers.BooleanField(write_only=True, required=True)
    privacy_policy_version = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'full_name', 'phone_number', 'privacy_consent', 'privacy_policy_version')

    def validate_privacy_consent(self, value):
        if value is not True:
            raise serializers.ValidationError('Read the privacy notice and confirm before creating an account.')
        return value

    def validate_privacy_policy_version(self, value):
        if value != PRIVACY_POLICY_VERSION:
            raise serializers.ValidationError('Reload and review the current privacy notice.')
        return value

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

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('privacy_consent')
        policy = validated_data.pop('privacy_policy_version')
        user = User.objects.create_user(**validated_data)
        profile = user.profile
        profile.privacy_consented_at = timezone.now()
        profile.privacy_policy_version = policy
        profile.save(update_fields=['privacy_consented_at', 'privacy_policy_version'])
        return user
