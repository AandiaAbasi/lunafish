import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassMessage',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Updated at')),
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('is_private', models.BooleanField(default=False)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Class Message',
                'verbose_name_plural': 'Class Messages',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='OnlineClass',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Updated at')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('scheduled_start', models.DateTimeField(verbose_name='Scheduled start')),
                ('scheduled_end', models.DateTimeField(verbose_name='Scheduled end')),
                ('actual_start', models.DateTimeField(blank=True, null=True, verbose_name='Actual start')),
                ('actual_end', models.DateTimeField(blank=True, null=True, verbose_name='Actual end')),
                ('room_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='RTC room ID')),
                ('max_students', models.PositiveIntegerField(default=100, verbose_name='Max students')),
                ('allow_student_chat', models.BooleanField(default=True, verbose_name='Allow student chat')),
                ('allow_student_reactions', models.BooleanField(default=True, verbose_name='Allow student reactions')),
                ('require_approval_to_join', models.BooleanField(default=False, verbose_name='Require approval to join')),
                ('enable_recording', models.BooleanField(default=False, verbose_name='Enable recording')),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('active', 'Active'), ('ended', 'Ended'), ('cancelled', 'Cancelled')], db_index=True, default='scheduled', max_length=20, verbose_name='Status')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='classes_teaching', to=settings.AUTH_USER_MODEL, verbose_name='Teacher')),
            ],
            options={
                'verbose_name': 'Online Class',
                'verbose_name_plural': 'Online Classes',
                'ordering': ['-scheduled_start'],
            },
        ),
        migrations.CreateModel(
            name='ClassEnrollment',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Updated at')),
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_unmute', models.BooleanField(default=False, verbose_name='Can unmute')),
                ('can_share_video', models.BooleanField(default=True, verbose_name='Can share video')),
                ('can_share_screen', models.BooleanField(default=False, verbose_name='Can share screen')),
                ('is_moderator', models.BooleanField(default=False, verbose_name='Is moderator')),
                ('enrolled_at', models.DateTimeField(auto_now_add=True, verbose_name='Enrolled at')),
                ('joined_at', models.DateTimeField(blank=True, null=True, verbose_name='Joined at')),
                ('left_at', models.DateTimeField(blank=True, null=True, verbose_name='Left at')),
                ('class_session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='classes.onlineclass', verbose_name='Class session')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrolled_classes', to=settings.AUTH_USER_MODEL, verbose_name='Student')),
            ],
            options={
                'verbose_name': 'Class Enrollment',
                'verbose_name_plural': 'Class Enrollments',
                'ordering': ['enrolled_at'],
                'unique_together': {('class_session', 'student')},
            },
        ),
        migrations.CreateModel(
            name='HandRaise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raised_at', models.DateTimeField(auto_now_add=True)),
                ('lowered_at', models.DateTimeField(blank=True, null=True)),
                ('acknowledged_at', models.DateTimeField(blank=True, null=True)),
                ('acknowledged_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acknowledged_hands', to=settings.AUTH_USER_MODEL)),
                ('class_session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='raised_hands', to='classes.onlineclass')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hand_raises', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Hand Raise',
                'verbose_name_plural': 'Hand Raises',
                'ordering': ['raised_at'],
            },
        ),
        migrations.AddField(
            model_name='classmessage',
            name='class_session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='classes.onlineclass'),
        ),
        migrations.AddField(
            model_name='classmessage',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_class_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='classmessage',
            name='recipient',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='class_messages_received', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='classmessage',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_messages_sent', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='ClassReaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('emoji', models.CharField(choices=[('👍', 'Thumbs Up'), ('❤️', 'Heart'), ('👏', 'Clap'), ('🎉', 'Party'), ('🤔', 'Thinking'), ('😮', 'Surprised')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('class_session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='classes.onlineclass')),
                ('message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='classes.classmessage')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_reactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Class Reaction',
                'verbose_name_plural': 'Class Reactions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='onlineclass',
            index=models.Index(fields=['teacher', 'status'], name='classes_onl_teacher_183a48_idx'),
        ),
        migrations.AddIndex(
            model_name='onlineclass',
            index=models.Index(fields=['scheduled_start', 'status'], name='classes_onl_schedul_0b3097_idx'),
        ),
        migrations.AddIndex(
            model_name='classenrollment',
            index=models.Index(fields=['student', 'left_at'], name='classes_cla_student_b1a7ad_idx'),
        ),
        migrations.AddIndex(
            model_name='classenrollment',
            index=models.Index(fields=['class_session', 'left_at'], name='classes_cla_class_s_2adcf6_idx'),
        ),
        migrations.AddIndex(
            model_name='handraise',
            index=models.Index(fields=['class_session', 'lowered_at'], name='classes_han_class_s_ba49dd_idx'),
        ),
        migrations.AddIndex(
            model_name='handraise',
            index=models.Index(fields=['student', 'raised_at'], name='classes_han_student_d39f2b_idx'),
        ),
        migrations.AddIndex(
            model_name='classmessage',
            index=models.Index(fields=['class_session', 'created_at'], name='classes_cla_class_s_23eb30_idx'),
        ),
        migrations.AddIndex(
            model_name='classmessage',
            index=models.Index(fields=['sender', 'created_at'], name='classes_cla_sender__f83f35_idx'),
        ),
        migrations.AddIndex(
            model_name='classmessage',
            index=models.Index(fields=['is_deleted', 'created_at'], name='classes_cla_is_dele_71dc86_idx'),
        ),
        migrations.AddIndex(
            model_name='classreaction',
            index=models.Index(fields=['class_session', 'created_at'], name='classes_cla_class_s_81f18c_idx'),
        ),
        migrations.AddIndex(
            model_name='classreaction',
            index=models.Index(fields=['student', 'created_at'], name='classes_cla_student_2ce8b1_idx'),
        ),
    ]

