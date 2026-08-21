"""In Django, a serializer converts complex data like querysets or model instances
into native Python datatypes that can easily be rendered into JSON, XML, or other content types"""

from rest_framework import serializers
from .models import Profile, Skill

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

    class Meta:
        model = Profile
        fields = (
            'headline', 'bio', 'location', 'years_of_experience',
            'skills', 'skill_names', 'cv_file', 'updated_at', 'email',
        )
        read_only_fields = ('updated_at',)

    # WHY WE OVERRIDE update(): DRF's default ModelSerializer.update() only knows
    # how to set plain model fields directly. `skill_names` isn't a real field on
    # Profile (skills is a many-to-many, handled differently) — so we manually
    # pop it out, save the normal fields first, then use get_or_create() to either
    # find existing skills or create new ones, and .set() to replace the full list.
    # This lets the API accept simple strings ["Python", "Django"] as input, while
    # still returning rich {id, name} objects in the response.
    def update(self, instance, validated_data):
        skill_names = validated_data.pop('skill_names', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if skill_names is not None:
            skills = []
            for name in skill_names:
                skill, _ = Skill.objects.get_or_create(name=name.strip())
                skills.append(skill)
            instance.skills.set(skills)

        return instance