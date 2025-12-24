from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    #home page
    path('', views.home_view, name='home'),
    path('index/', views.IndexView.as_view(), name='index'),
    
    #articles
    path('articles/', views.article_list_view, name='article_list'),
    path('article/<int:pk>/', views.article_detail_view, name='article_detail'),
    
    path('faqs/', views.faq_list_view, name='faq_list'),
    path('about/', views.about_view, name='about'),
    path('terms/', views.term_list_view, name='terms'),
    path('privacy/', views.privacy_list_view, name='privacy'),
    path('contact/', views.contact_view, name='contact'),

    path('set-language/', views.custom_set_language, name='set_language'),
]
