# Generated migration for adding new attorney choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('makgetha_appointment_system', '0003_alter_appointment_service_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='attorney',
            field=models.CharField(
                choices=[
                    ('M. Makgetha', 'M. Makgetha'),
                    ('M. Mbhalati', 'M. Mbhalati'),
                    ('M. Tshitshiba', 'M. Tshitshiba'),
                ],
                default='M. Makgetha',
                max_length=100
            ),
        ),
    ]
