from django.contrib.auth.base_user import BaseUserManager

# WHY THIS FILE EXISTS:
# Django's default User model creation logic expects a `username` field.
# Since our User uses email instead (no username at all), we can't rely on
# Django's built-in manager — we have to tell it manually how to build a User:
# normalize the email, hash the password, and save it. This is the "recipe"
# Django follows every time a user is created, whether through the API,
# the admin panel, or `createsuperuser` in the terminal.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)