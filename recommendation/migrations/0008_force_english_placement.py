from django.db import migrations, models


def force_english_placement(apps, schema_editor):
    PsychologicalTest = apps.get_model('recommendation', 'PsychologicalTest')
    PsychologicalTest.objects.exclude(
        test_type='english_placement'
    ).update(
        test_type='english_placement'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('recommendation', '0007_english_placement_admin'),
    ]

    operations = [
        migrations.RunPython(
            force_english_placement,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='psychologicaltest',
            name='test_type',
            field=models.CharField(
                choices=[
                    ('register', 'Register'),
                    ('regular', 'Regular'),
                    ('english_placement', 'English placement'),
                ],
                default='english_placement',
                editable=False,
                max_length=50,
                verbose_name='Type',
            ),
        ),
    ]
