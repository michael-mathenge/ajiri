from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('profiles', '0005_cv_workspace_approval')]
    operations = [
        migrations.AddField(model_name='profile', name='privacy_consented_at',
            field=models.DateTimeField(blank=True, default=None, null=True)),
        migrations.AddField(model_name='profile', name='privacy_policy_version',
            field=models.CharField(blank=True, default='', max_length=40)),
    ]
