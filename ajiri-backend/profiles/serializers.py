"""In Django, a serializer converts complex data like querysets or model instances
into native Python datatypes that can easily be rendered into JSON, XML, or other content types"""

from rest_framework import serializers
from .models import Profile, Skill
from .upload_validation import validate_cv_upload


class SkillSerializer(serializers.ModelSerializer):
    """  Converts a Skill model instance into simple JSON like {"id": 1, "name": "Python"}."""
    class Meta:
        model = Skill
        fields = ('id', 'name')


class ProfileSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    skill_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False
    )
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)

    class Meta:
        model = Profile
        fields = (
            'headline', 'bio', 'location', 'years_of_experience',
            'skills', 'skill_names', 'cv_file', 'updated_at', 'email',
            'full_name', 'phone_number',
            'notify_email', 'notify_in_app',
            'privacy_consented_at', 'privacy_policy_version',
        )
        read_only_fields = ('updated_at', 'privacy_consented_at', 'privacy_policy_version')

    def to_representation(self, instance):
        """
        full_name/phone_number actually live on the related User model, not
        Profile. Declaring them as plain CharFields above (no `source=`) lets
        write-side validation work simply, but means we have to manually pull
        their DISPLAY values from instance.user here for read/GET responses.
        """
        data = super().to_representation(instance)
        data['full_name'] = instance.user.full_name
        data['phone_number'] = instance.user.phone_number
        return data

    def validate_cv_file(self, value):
        return validate_cv_upload(value) if value else value

    def update(self, instance, validated_data):
        skill_names = validated_data.pop('skill_names', None)
        full_name = validated_data.pop('full_name', None)
        phone_number = validated_data.pop('phone_number', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if full_name is not None or phone_number is not None:
            if full_name is not None:
                instance.user.full_name = full_name
            if phone_number is not None:
                instance.user.phone_number = phone_number
            instance.user.save()

        if skill_names is not None:
            skills = []
            for name in skill_names:
                skill, _ = Skill.objects.get_or_create(name=name.strip())
                skills.append(skill)
            instance.skills.set(skills)

        return instance
