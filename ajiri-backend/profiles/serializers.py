"""In Django, a serializer converts complex data like querysets or model instances
into native Python datatypes that can easily be rendered into JSON, XML, or other content types"""

from rest_framework import serializers
from .models import Profile, Skill
import os


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
    full_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Profile
        fields = (
            'headline', 'bio', 'location', 'years_of_experience',
            'skills', 'skill_names', 'cv_file', 'updated_at', 'email',
            'full_name', 'phone_number',
        )
        read_only_fields = ('updated_at',)

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
        if value:
            allowed_extensions = ['.pdf', '.doc', '.docx']
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_extensions)}"
                )

            max_size_mb = 5
            if value.size > max_size_mb * 1024 * 1024:
                raise serializers.ValidationError(
                    f"File too large ({value.size / 1024 / 1024:.1f}MB). Max size: {max_size_mb}MB"
                )
        return value

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