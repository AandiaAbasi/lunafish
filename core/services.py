from core.models import *
from django.db.models import Count, Q, Avg


# ========== articles ==========

def get_all_articles():
    return Article.objects.all().order_by('-created_at')


def get_article_detail(article_id):
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        return None
    return article


def get_recent_articles(limit=5, exclude_id=None):
    qs = Article.objects.order_by('-created_at')
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    return qs[:limit]


# ========== FAQ services ==========

def get_active_faqs():
    """Get active FAQs"""
    return FAQ.objects.filter(is_active=True).order_by('-created_at')


# ========== about ==========

def get_about_info():
    """Get about information"""
    return About.objects.all().order_by('-created_at')


# ========== terms ==========

def get_all_terms():
    return Term.objects.all().order_by('-created_at')


def get_all_privacy():
    """Get all privacy policies"""
    return Privacy.objects.all().order_by('-created_at')


# ========== contact services ==========

def get_contacts():
    """Get contact information"""
    return Contact.objects.all().order_by('title')


def save_contact_message_form(form):
    """Save contact message"""
    return form.save()


# ========== Home Page Services ==========

class HomePageService:
    """Home Page Service"""
    
    @staticmethod
    def get_home_page_data():
        """Get home page data"""
        return {
            'banners': Banner.objects.filter(is_active=True).order_by('sort', '-created_at')[:5],
            'recent_articles': Article.objects.order_by('-created_at')[:3],
        }


# ========== Banner Services ==========

def get_active_banners():
    """Get active banners"""
    return Banner.objects.filter(is_active=True).order_by('sort', '-created_at')
