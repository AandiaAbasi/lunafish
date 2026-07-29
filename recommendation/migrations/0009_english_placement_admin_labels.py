from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('recommendation', '0008_force_english_placement'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='psychologicaltest',
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'آزمون تعیین سطح زبان انگلیسی',
                'verbose_name_plural': 'آزمون‌های تعیین سطح زبان انگلیسی',
            },
        ),
        migrations.AlterModelOptions(
            name='testquestion',
            options={
                'ordering': ['test', 'order'],
                'verbose_name': 'سؤال آزمون تعیین سطح',
                'verbose_name_plural': 'سؤال‌های آزمون تعیین سطح',
            },
        ),
        migrations.AlterModelOptions(
            name='studenttestresponse',
            options={
                'ordering': ['-completed_at'],
                'verbose_name': 'پاسخ دانش‌آموز به آزمون تعیین سطح',
                'verbose_name_plural': 'پاسخ‌های دانش‌آموزان به آزمون تعیین سطح',
            },
        ),
        migrations.AlterModelOptions(
            name='testscale',
            options={
                'ordering': ['test', 'code'],
                'verbose_name': 'مقیاس تعیین سطح',
                'verbose_name_plural': 'مقیاس‌های تعیین سطح',
            },
        ),
        migrations.AlterModelOptions(
            name='testresult',
            options={
                'ordering': ['-calculated_at'],
                'verbose_name': 'نتیجه آزمون تعیین سطح',
                'verbose_name_plural': 'نتایج آزمون‌های تعیین سطح',
            },
        ),
        migrations.AlterField(
            model_name='psychologicaltest',
            name='title',
            field=models.CharField(
                help_text='مثال: آزمون تعیین سطح زبان انگلیسی',
                max_length=255,
                verbose_name='عنوان آزمون تعیین سطح',
            ),
        ),
        migrations.AlterField(
            model_name='psychologicaltest',
            name='description',
            field=models.TextField(
                blank=True,
                help_text='توضیحات کلی درباره آزمون تعیین سطح زبان انگلیسی',
                verbose_name='توضیحات',
            ),
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
                verbose_name='نوع آزمون',
            ),
        ),
        migrations.AlterField(
            model_name='testquestion',
            name='test',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='questions',
                to='recommendation.psychologicaltest',
                verbose_name='آزمون تعیین سطح',
            ),
        ),
        migrations.AlterField(
            model_name='testquestion',
            name='order',
            field=models.PositiveIntegerField(
                default=0,
                help_text='ترتیب نمایش سؤال در آزمون تعیین سطح',
                verbose_name='ترتیب',
            ),
        ),
        migrations.AlterField(
            model_name='studenttestresponse',
            name='test',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='student_responses',
                to='recommendation.psychologicaltest',
                verbose_name='آزمون تعیین سطح',
            ),
        ),
        migrations.AlterField(
            model_name='testscale',
            name='test',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='scales',
                to='recommendation.psychologicaltest',
                verbose_name='آزمون تعیین سطح',
            ),
        ),
        migrations.AlterField(
            model_name='testscale',
            name='code',
            field=models.CharField(
                help_text='مثال سطح: A1، A2، B1؛ مثال مهارت: GRAM، VOCAB، READ، USE',
                max_length=20,
                verbose_name='کد مقیاس',
            ),
        ),
        migrations.AlterField(
            model_name='testscale',
            name='title',
            field=models.CharField(
                help_text='مثال: سطح متوسط B1 یا مهارت گرامر',
                max_length=255,
                verbose_name='عنوان مقیاس',
            ),
        ),
        migrations.AlterField(
            model_name='optionscaleweight',
            name='weight',
            field=models.FloatField(
                help_text='امتیاز این گزینه برای سطح یا مهارت انتخاب‌شده',
                verbose_name='وزن',
            ),
        ),
        migrations.AlterField(
            model_name='scaleinterpretation',
            name='title',
            field=models.CharField(
                help_text='مثال: تسلط قوی، قابل قبول، نیازمند تقویت',
                max_length=255,
                verbose_name='عنوان تفسیر',
            ),
        ),
        migrations.AlterField(
            model_name='scaleinterpretation',
            name='description',
            field=models.TextField(
                help_text='توضیح آموزشی نتیجه در این بازه امتیاز',
                verbose_name='توضیحات تفسیر',
            ),
        ),
    ]
