from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('jobs', '0006_notification')]
    operations = [
        migrations.AddField(
            model_name='notification', name='in_app',
            field=models.BooleanField(default=True),
        ),
    ]
