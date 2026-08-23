from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from classroom.models import Course
from .models import Article, FAQ, About, Term, Privacy, Contact, Banner
from .services import HomePageService, get_all_articles, get_active_faqs, get_about_info, get_all_terms, get_all_privacy, get_contacts
from .forms import ContactMessageForm
from django.views.i18n import set_language as django_set_language
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
import requests
from django.urls import reverse
from django.conf import settings
from django.http import StreamingHttpResponse, HttpResponse

def custom_set_language(request):
    """
    Custom set_language view that handles language switching.
    
    Supports both GET (for simple links) and POST (Django's standard mechanism).
    Does NOT add language prefix to URLs since this project doesn't use i18n_patterns.
    The LocaleMiddleware reads the language cookie to determine the active language.
    """
    if request.method == 'GET':
        next_url = request.GET.get('next', '/')
        language = request.GET.get('language', settings.LANGUAGE_CODE)
        
        # Validate the language code
        valid_languages = [code for code, _ in settings.LANGUAGES]
        if language not in valid_languages:
            language = settings.LANGUAGE_CODE
        
        # Strip any accidental language prefix from next_url
        # (in case old bookmarks or cached links have them)
        for lang_code in valid_languages:
            if next_url.startswith(f'/{lang_code}/'):
                next_url = next_url[len(f'/{lang_code}'):]
                if not next_url.startswith('/'):
                    next_url = '/' + next_url
                break
        
        response = HttpResponseRedirect(next_url)
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            language,
            max_age=getattr(settings, 'LANGUAGE_COOKIE_AGE', None),
            path=getattr(settings, 'LANGUAGE_COOKIE_PATH', '/'),
            secure=getattr(settings, 'LANGUAGE_COOKIE_SECURE', False),
            httponly=getattr(settings, 'LANGUAGE_COOKIE_HTTPONLY', False),
            samesite=getattr(settings, 'LANGUAGE_COOKIE_SAMESITE', 'Lax'),
        )
        return response
    else:
        # For POST requests, delegate to Django's built-in set_language view
        return django_set_language(request)



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
    """Public LunaFish application landing page."""

    recent_courses = Course.objects.filter(
        is_active=True,
        status='approved',
        subject__teacher__is_teacher_verified=True
    ).select_related(
        'subject__teacher'
    ).order_by(
        '-created_at'
    )[:10]


    if request.GET.get("success"):
        messages.success(
            request,
            "پرداخت دوره با موفقیت انجام شد."
        )


    return render(
        request,
        'core/home.html',
        {
            'recent_courses': recent_courses
        }
    )

def course_payment(request, course_id):

    from classroom.models import Course
    from django.conf import settings
    import requests


    course = get_object_or_404(
        Course,
        id=course_id,
        is_active=True,
        status="approved",
        subject__teacher__is_teacher_verified=True
    )


    payload = {
        "merchant": settings.ZIBAL_MERCHANT_ID,
        "amount": int(course.final_price * 10),
        "callbackUrl": request.build_absolute_uri("/"),
        "description": f"خرید دوره {course.title}",
        "orderId": str(course.id),
    }


    response = requests.post(
        settings.ZIBAL_REQUEST_URL,
        json=payload,
        timeout=10
    )


    result = response.json()


    if result.get("result") == 100:

        track_id = result.get("trackId")

        return redirect(
            f"https://gateway.zibal.ir/start/{track_id}"
        )


    return HttpResponse(
        result
    )

def course_payment_verify(request, enrollment_id):

    from classroom.models import CourseEnrollment
    from django.conf import settings
    from django.utils import timezone
    import requests


    enrollment = get_object_or_404(
        CourseEnrollment,
        id=enrollment_id
    )


    track_id = request.GET.get("trackId")


    if not track_id:
        messages.error(
            request,
            "پرداخت ناموفق بود"
        )
        return redirect("/")


    payload = {
        "merchant": settings.ZIBAL_MERCHANT_ID,
        "trackId": track_id
    }


    response = requests.post(
        settings.ZIBAL_VERIFY_URL,
        json=payload,
        timeout=10
    )


    result = response.json()


    if result.get("result") == 100:


        enrollment.payment_status = "paid"
        enrollment.payment_ref = track_id
        enrollment.paid_at = timezone.now()
        enrollment.save()


        # ساخت جلسات
        enrollment.confirm_payment(
            track_id
        )


        messages.success(
            request,
            "دوره با موفقیت خریداری شد"
        )

        return redirect("/")


    enrollment.payment_status = "failed"
    enrollment.payment_ref = track_id
    enrollment.save()


    messages.error(
        request,
        "تایید پرداخت انجام نشد"
    )

    return redirect("/")


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