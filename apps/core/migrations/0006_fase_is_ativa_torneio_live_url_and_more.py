from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_fase_regra'),
    ]

    operations = [
        migrations.AddField(
            model_name='fase',
            name='is_ativa',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='torneio',
            name='live_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='torneio',
            name='polling_interval',
            field=models.IntegerField(default=10),
        ),
    ]
