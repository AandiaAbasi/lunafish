import os
import uuid
from django.utils import timezone
from django.utils.translation import get_language
import jdatetime


def upload_to_dynamic(instance, filename):
    from .models import About, Article, Banner
    from account.models import User
    from classroom.models import TeachingSubject
    """Dynamic upload path for user images"""
    name, ext = os.path.splitext(filename)
    filename = f"{uuid.uuid4().hex}{ext}"
    folder = "users"
    if isinstance(instance, About):  
        folder = "about"
    elif isinstance(instance, Article): 
        folder = "articles"
    elif isinstance(instance, Banner):
        folder = "banners"
    elif isinstance(instance, User):
        folder = "users"
    elif isinstance(instance, TeachingSubject):
        folder = "teacher_subjects"
    else:
        folder = "others"
    
    return os.path.join(folder, filename)
    
    
def format_datetime_display(dt):
    """Format datetime based on current language (Jalali for Persian, Gregorian for English)"""
    if not dt:
        return "-"
    
    try:
        dt = timezone.localtime(dt)
    except Exception:
        pass
    
    lang = get_language()
    
    if lang and lang.startswith("fa"):
        return jdatetime.datetime.fromgregorian(datetime=dt).strftime('%Y/%m/%d %H:%M')
    else:
        return dt.strftime('%Y-%m-%d %H:%M')    
