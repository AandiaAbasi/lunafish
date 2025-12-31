#!/usr/bin/env python
"""
Script to add teacher ratings from students
اسکریپت برای اضافه کردن امتیاز معلمان از دانش‌آموزان
"""
import os
import sys
import django
import random

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fofofish.settings')
django.setup()

from account.models import User, TeacherRating


def main():
    """Add teacher ratings from students"""
    
    # Get all students and teachers
    students = list(User.objects.filter(role='student'))
    teachers = list(User.objects.filter(role='teacher', is_teacher_verified=True))
    
    if not students:
        print('❌ هیچ دانش‌آموزی در دیتابیس وجود ندارد')
        return
    
    if not teachers:
        print('❌ هیچ معلم تایید‌شده‌ای در دیتابیس وجود ندارد')
        return
    
    print(f'✓ شروع اضافه کردن امتیاز...')
    print(f'  تعداد دانش‌آموزان: {len(students)}')
    print(f'  تعداد معلمان: {len(teachers)}\n')
    
    sample_comments = [
        'معلم بسیار خوب و توضیح‌دهنده است',
        'کلاس خیلی جالب و آموزنده بود',
        'معلم صبور و مهربان است',
        'روش تدریس بسیار مؤثر است',
        'توصیه می‌کنم برای دیگران',
        'کلاس خیلی سازمان‌یافته بود',
        'معلم خیلی متخصص است',
        'کلاس برای سطح من مناسب بود',
        'معلم به سؤالات من پاسخ داد',
        'بهتر می‌تواند باشد',
        'کلاس مفید بود',
        'معلم خیلی حرفه‌ای است',
        'من از این کلاس راضی هستم',
        'توصیه این معلم را می‌کنم',
        'کلاس ارزشمند بود',
    ]
    
    created_count = 0
    skipped_count = 0
    
    # Create ratings
    for i, student in enumerate(students):
        # Random number of teachers each student rates (1-5 teachers)
        num_teachers = random.randint(1, min(5, len(teachers)))
        selected_teachers = random.sample(teachers, num_teachers)
        
        for teacher in selected_teachers:
            try:
                # Generate random rating
                stars = random.randint(1, 5)
                comment = random.choice(sample_comments)
                rater_type = random.choice(['student', 'parent'])
                
                # Create or get rating
                rating, created = TeacherRating.objects.get_or_create(
                    teacher=teacher,
                    rater=student,
                    defaults={
                        'stars': stars,
                        'comment': comment,
                        'rater_type': rater_type,
                        'is_anonymous': False,
                        'is_verified': True,
                    }
                )
                
                if created:
                    created_count += 1
                    print(f'[{i+1}/{len(students)}] ✓ {student.name} → {teacher.name}: {stars}⭐')
                else:
                    skipped_count += 1
                    # print(f'[{i+1}/{len(students)}] ⊘ قبلاً موجود: {student.name} → {teacher.name}')
                    
            except Exception as e:
                print(f'❌ خطا برای {student.name} → {teacher.name}: {str(e)}')
                continue
    
    print(f'\n✓ تکمیل شد!')
    print(f'  ایجاد شده: {created_count}')
    print(f'  رد شده (قبلاً موجود): {skipped_count}')


if __name__ == '__main__':
    main()
