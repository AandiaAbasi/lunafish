from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recommendation', '0006_remove_psychologicaltest_description_ar_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='psychologicaltest',
            name='test_type',
            field=models.CharField(
                choices=[
                    ('register', 'Register'),
                    ('regular', 'Regular'),
                    ('english_placement', 'English placement'),
                ],
                default='regular',
                max_length=50,
                verbose_name='Type',
            ),
        ),
        migrations.AddField(
            model_name='testscale',
            name='pass_score',
            field=models.FloatField(
                default=70,
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)],
                help_text='حداقل امتیاز لازم برای عبور از این سطح',
                verbose_name='حداقل امتیاز قبولی',
            ),
        ),
        migrations.AddField(
            model_name='testscale',
            name='rank',
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text='برای سطح‌ها: A1=1، A2=2، B1=3، B2=4، C1=5',
                null=True,
                verbose_name='ترتیب سطح',
            ),
        ),
        migrations.AddField(
            model_name='testscale',
            name='scale_type',
            field=models.CharField(
                choices=[
                    ('general', 'عمومی'),
                    ('level', 'سطح زبان'),
                    ('skill', 'مهارت زبان'),
                ],
                db_index=True,
                default='general',
                max_length=20,
                verbose_name='نوع مقیاس',
            ),
        ),
        migrations.CreateModel(
            name='EnglishPlacementAssessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Updated at')),
                ('suggested_level', models.CharField(blank=True, choices=[('pre_a1', 'Pre-A1'), ('a1', 'A1 - Beginner'), ('a2', 'A2 - Elementary'), ('b1', 'B1 - Intermediate'), ('b2', 'B2 - Upper Intermediate'), ('c1', 'C1 - Advanced'), ('c2', 'C2 - Proficient')], db_index=True, max_length=10, null=True, verbose_name='سطح پیشنهادی سیستم')),
                ('final_level', models.CharField(blank=True, choices=[('pre_a1', 'Pre-A1'), ('a1', 'A1 - Beginner'), ('a2', 'A2 - Elementary'), ('b1', 'B1 - Intermediate'), ('b2', 'B2 - Upper Intermediate'), ('c1', 'C1 - Advanced'), ('c2', 'C2 - Proficient')], db_index=True, max_length=10, null=True, verbose_name='سطح نهایی')),
                ('source', models.CharField(choices=[('test', 'آزمون تعیین سطح'), ('admin', 'تعیین دستی ادمین'), ('teacher', 'تعیین دستی مدرس')], default='test', max_length=20, verbose_name='روش تعیین سطح')),
                ('status', models.CharField(choices=[('pending', 'در انتظار بررسی'), ('confirmed', 'تأیید شده'), ('overridden', 'تغییر داده شده توسط ارزیاب')], db_index=True, default='pending', max_length=20, verbose_name='وضعیت بررسی')),
                ('assessed_at', models.DateTimeField(blank=True, null=True, verbose_name='زمان بررسی نهایی')),
                ('response_completed_at', models.DateTimeField(blank=True, null=True, verbose_name='زمان ثبت این نوبت آزمون')),
                ('raw_scores_snapshot', models.JSONField(blank=True, default=dict, verbose_name='تصویر امتیازهای آزمون')),
                ('result_summary_snapshot', models.JSONField(blank=True, default=dict, verbose_name='تصویر خلاصه نتیجه')),
                ('note', models.TextField(blank=True, verbose_name='یادداشت ارزیاب')),
                ('assessed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='performed_english_assessments', to=settings.AUTH_USER_MODEL, verbose_name='بررسی شده توسط')),
                ('response', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='placement_assessments', to='recommendation.studenttestresponse', verbose_name='پاسخ آزمون')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='english_placement_assessments', to=settings.AUTH_USER_MODEL, verbose_name='دانش‌آموز')),
                ('test', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='placement_assessments', to='recommendation.psychologicaltest', verbose_name='آزمون')),
            ],
            options={
                'verbose_name': 'تعیین سطح زبان',
                'verbose_name_plural': 'تاریخچه تعیین سطح زبان',
                'ordering': ['-created_at'],
            },
        ),
    ]
