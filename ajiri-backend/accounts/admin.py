from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import AccountCreationForm, AccountChangeForm


class CustomUserAdmin(UserAdmin):
    model = User
    add_form = AccountCreationForm
    form = AccountChangeForm
    list_display = ('email', 'full_name', 'phone_number', 'is_staff', 'is_active')
    ordering = ('email',)
    search_fields = ('email', 'full_name', 'phone_number')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )


admin.site.register(User, CustomUserAdmin)
