from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse

from .models import Article, FAQ, About, Term, Privacy, Contact, Banner
from .services import HomePageService, get_all_articles, get_active_faqs, get_about_info, get_all_terms, get_all_privacy, get_contacts
from .forms import ContactMessageForm
from django.views.i18n import set_language as django_set_language
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _


def custom_set_language(request):
    """Custom set_language view that handles language switching with i18n_patterns"""
    next_url = request.GET.get('next', '/')
    language = request.GET.get('language', settings.LANGUAGE_CODE)
    
    # Call Django's set_language to set the cookie
    response = django_set_language(request)
    
    # If next_url doesn't start with language prefix, add the new language prefix
    if next_url:
        # Remove any existing language prefix
        for lang_code, _ in settings.LANGUAGES:
            if next_url.startswith(f'/{lang_code}/'):
                next_url = next_url[len(f'/{lang_code}'):]
                break
        
        # Add the new language prefix
        next_url = f'/{language}{next_url}'
        
        response = HttpResponseRedirect(next_url)
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            language,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path='/',
            secure=settings.LANGUAGE_COOKIE_SECURE,
            httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )
    
    return response



class IndexView(ListView):
    """Home Page"""
    template_name = 'core/index.html'
    context_object_name = 'items'
    
    def get_queryset(self):
        return []
    
    def get_context_data(self, **kwargs):
        from django.db.models import Count, Q, Prefetch
        from django.contrib.contenttypes.models import ContentType
        from core.models import Banner
        from django.utils import timezone
        
        context = super().get_context_data(**kwargs)
        home_data = HomePageService.get_home_page_data()
        context.update(home_data)
        
        # Banners for home page
        now = timezone.now()
        context['banners'] = Banner.objects.filter(
            placement='home',
            is_active=True
        ).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=now)
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        ).order_by('sort', '-created_at')[:5]
  
        return context


def home_view(request):
    """Simple Home Page"""
    context = HomePageService.get_home_page_data()
    return render(request, 'core/home.html', context)


def article_list_view(request):
    """Article List"""
    articles = get_all_articles()
    
    # Pagination
    paginator = Paginator(articles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, "core/articles.html", {
        "articles": page_obj,
        "page_obj": page_obj
    })


def article_detail_view(request, pk):
    """Article Detail"""
    article = get_object_or_404(Article, pk=pk)
    recent_articles = Article.objects.exclude(id=pk).order_by('-created_at')[:5]
    
    return render(request, "core/article.html", {
        "article": article,
        "recent_articles": recent_articles
    })


def faq_list_view(request):
    """FAQ List"""
    faqs = get_active_faqs()
    return render(request, "core/faqs.html", {"faq_list": faqs})


def about_view(request):
    """About Us page"""
    about = get_about_info()
    return render(request, "core/about.html", {"about": about})


def term_list_view(request):
    """Terms and Conditions"""
    terms = get_all_terms()
    return render(request, "core/terms.html", {"term_list": terms})


def privacy_list_view(request):
    """Privacy Policy"""
    privacy = get_all_privacy()
    return render(request, "core/privacy.html", {"privacy_list": privacy})


def contact_view(request):
    """Contact Us page"""
    contact = get_contacts()
    form = ContactMessageForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()

            messages.success(
                request,
                _("Your message has been sent successfully.")
            )

            next_url = (
                request.POST.get("next")
                or request.GET.get("next")
                or "core:contact"
            )

            return redirect(next_url)

        else:
            messages.error(
                request,
                _("Please correct the errors in the form.")
            )

    return render(
        request,
        "core/contact.html",
        {
            "contact": contact,
            "form": form,
        }
    )