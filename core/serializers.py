"""
Serializers for Core app - Articles, FAQs, Static Pages, Banners
Supports bilingual (English/Persian) content
"""
from rest_framework import serializers
from django.utils.translation import get_language
import jdatetime
from .models import Article, FAQ, About, Term, Privacy, Contact, Banner


def get_bilingual_field(obj, field_name):
    """Helper to get bilingual field content"""
    en_value = getattr(obj, f'{field_name}_en', None)
    fa_value = getattr(obj, f'{field_name}_fa', None)
    return {
        'en': en_value or '',
        'fa': fa_value or ''
    }


class ArticleListSerializer(serializers.ModelSerializer):
    """Serializer for article list"""
    created_at_display = serializers.SerializerMethodField()
    title_bilingual = serializers.SerializerMethodField()
    short_description_bilingual = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'title_bilingual', 'image', 'short_description', 'short_description_bilingual', 'created_at', 'created_at_display']
    
    def get_title_bilingual(self, obj):
        return get_bilingual_field(obj, 'title')
    
    def get_short_description_bilingual(self, obj):
        return get_bilingual_field(obj, 'short_description')
    
    def get_created_at_display(self, obj):
        lang = get_language()
        if lang == 'fa':
            # Persian: Jalali (Shamsi) date
            return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime('%Y-%m-%d')
        else:
            # English: Gregorian date
            return obj.created_at.strftime('%Y-%m-%d')


class ArticleDetailSerializer(serializers.ModelSerializer):
    """Serializer for article detail"""
    created_at_display = serializers.SerializerMethodField()
    title_bilingual = serializers.SerializerMethodField()
    short_description_bilingual = serializers.SerializerMethodField()
    content_bilingual = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'title_bilingual', 'image', 'short_description', 'short_description_bilingual', 'content', 'content_bilingual', 'created_at', 'created_at_display']
    
    def get_title_bilingual(self, obj):
        return get_bilingual_field(obj, 'title')
    
    def get_short_description_bilingual(self, obj):
        return get_bilingual_field(obj, 'short_description')
    
    def get_content_bilingual(self, obj):
        return get_bilingual_field(obj, 'content')
    
    def get_created_at_display(self, obj):
        lang = get_language()
        if lang == 'fa':
            # Persian: Jalali (Shamsi) date
            return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime('%Y-%m-%d')
        else:
            # English: Gregorian date
            return obj.created_at.strftime('%Y-%m-%d')


class FAQSerializer(serializers.ModelSerializer):
    """Serializer for FAQ"""
    question_bilingual = serializers.SerializerMethodField()
    answer_bilingual = serializers.SerializerMethodField()
    
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'question_bilingual', 'answer', 'answer_bilingual', 'is_active']
    
    def get_question_bilingual(self, obj):
        return get_bilingual_field(obj, 'question')
    
    def get_answer_bilingual(self, obj):
        return get_bilingual_field(obj, 'answer')


class AboutSerializer(serializers.ModelSerializer):
    """Serializer for About page"""
    title_bilingual = serializers.SerializerMethodField()
    content_bilingual = serializers.SerializerMethodField()
    
    class Meta:
        model = About
        fields = ['id', 'title', 'title_bilingual', 'image', 'content', 'content_bilingual']
    
    def get_title_bilingual(self, obj):
        return get_bilingual_field(obj, 'title')
    
    def get_content_bilingual(self, obj):
        return get_bilingual_field(obj, 'content')


class TermSerializer(serializers.ModelSerializer):
    """Serializer for Terms page"""
    title_bilingual = serializers.SerializerMethodField()
    content_bilingual = serializers.SerializerMethodField()
    
    class Meta:
        model = Term
        fields = ['id', 'title', 'title_bilingual', 'content', 'content_bilingual']
    
    def get_title_bilingual(self, obj):
        return get_bilingual_field(obj, 'title')
    
    def get_content_bilingual(self, obj):
        return get_bilingual_field(obj, 'content')


class PrivacySerializer(serializers.ModelSerializer):
    """Serializer for Privacy page"""
    title_bilingual = serializers.SerializerMethodField()
    content_bilingual = serializers.SerializerMethodField()
    
    class Meta:
        model = Privacy
        fields = ['id', 'title', 'title_bilingual', 'content', 'content_bilingual']
    
    def get_title_bilingual(self, obj):
        return get_bilingual_field(obj, 'title')
    
    def get_content_bilingual(self, obj):
        return get_bilingual_field(obj, 'content')


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact info"""
    title_bilingual = serializers.SerializerMethodField()
    value_bilingual = serializers.SerializerMethodField()
    
    class Meta:
        model = Contact
        fields = ['id', 'title', 'title_bilingual', 'type', 'value', 'value_bilingual', 'link']
    
    def get_title_bilingual(self, obj):
        return get_bilingual_field(obj, 'title')
    
    def get_value_bilingual(self, obj):
        return get_bilingual_field(obj, 'value')


class BannerSerializer(serializers.ModelSerializer):
    """Serializer for Banner"""
    title_bilingual = serializers.SerializerMethodField()
    sub_title_bilingual = serializers.SerializerMethodField()
    
    class Meta:
        model = Banner
        fields = ['id', 'title', 'title_bilingual', 'sub_title', 'sub_title_bilingual', 'image', 'link', 'sort']
    
    def get_title_bilingual(self, obj):
        return get_bilingual_field(obj, 'title')
    
    def get_sub_title_bilingual(self, obj):
        return get_bilingual_field(obj, 'sub_title')
