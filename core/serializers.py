"""
Serializers for Core app - Articles, FAQs, Static Pages, Banners
"""
from rest_framework import serializers
from django.utils.translation import get_language
import jdatetime
from .models import Article, FAQ, About, Term, Privacy, Contact, Banner


class ArticleListSerializer(serializers.ModelSerializer):
    """Serializer for article list"""
    created_at_jalali = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'image', 'short_description', 'created_at', 'created_at_jalali']
    
    def get_created_at_jalali(self, obj):
        lang = get_language()
        if lang == 'fa':
            # Persian: Jalali (Shamsi) date
            return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime('%Y-%m-%d')
        else:
            # English: Gregorian date
            return obj.created_at.strftime('%Y-%m-%d')


class ArticleDetailSerializer(serializers.ModelSerializer):
    """Serializer for article detail"""
    created_at_jalali = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'image', 'short_description', 'content', 'created_at', 'created_at_jalali']
    
    def get_created_at_jalali(self, obj):
        lang = get_language()
        if lang == 'fa':
            # Persian: Jalali (Shamsi) date
            return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime('%Y-%m-%d')
        else:
            # English: Gregorian date
            return obj.created_at.strftime('%Y-%m-%d')


class FAQSerializer(serializers.ModelSerializer):
    """Serializer for FAQ"""
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer']


class AboutSerializer(serializers.ModelSerializer):
    """Serializer for About page"""
    class Meta:
        model = About
        fields = ['id', 'title', 'image', 'content']


class TermSerializer(serializers.ModelSerializer):
    """Serializer for Terms page"""
    class Meta:
        model = Term
        fields = ['id', 'title', 'content']


class PrivacySerializer(serializers.ModelSerializer):
    """Serializer for Privacy page"""
    class Meta:
        model = Privacy
        fields = ['id', 'title', 'content']


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact info"""
    class Meta:
        model = Contact
        fields = ['id', 'title', 'type', 'value', 'link']


class BannerSerializer(serializers.ModelSerializer):
    """Serializer for Banner"""
    class Meta:
        model = Banner
        fields = ['id', 'title', 'sub_title', 'image', 'link', 'sort']
