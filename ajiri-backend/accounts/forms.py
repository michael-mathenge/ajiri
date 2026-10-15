from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from .models import User


class AccountCreationForm(AdminUserCreationForm):
    # Django's form validates configured policy against the populated custom user.
    # see docs/CONCEPTS.md#password-validation
    class Meta(AdminUserCreationForm.Meta):
        model = User
        fields = ('email', 'full_name', 'phone_number')


class AccountChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'
