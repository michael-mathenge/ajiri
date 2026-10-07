from django.contrib import admin
from .models import Profile, Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'headline', 'location', 'years_of_experience', 'updated_at')
    search_fields = ('user__email', 'headline', 'location')
    filter_horizontal = ('skills',)