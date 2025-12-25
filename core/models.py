from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from ckeditor.fields import RichTextField
import jdatetime
from core.abstract_models import BaseModel
from core.utils import upload_to_dynamic
from django.utils.translation import gettext_lazy as _


class About(BaseModel):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    image = models.ImageField(upload_to=upload_to_dynamic, null=True, blank=True, verbose_name=_("Image"))
    content = RichTextField(verbose_name=_("Content"))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("About us")
        verbose_name_plural = _("About us")


class Term(BaseModel):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    content = RichTextField(verbose_name=_("Content"))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Terms & Conditions")
        verbose_name_plural = _("Terms & Conditions")


class Privacy(BaseModel):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    content = RichTextField(verbose_name=_("Content"))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Privacy Policy")
        verbose_name_plural = _("Privacy Policy")


class Contact(BaseModel):
    CHOICES = [
        ('email', _("Email")),
        ('phone', _("Phone")),
        ('sms', _("Notification number")),
        ('address', _("Address")),
        ('instagram', _("Instagram")),
        ('telegram', _("Telegram")),
        ('youtube', _("YouTube")),
        ('spotify', _("Spotify")),
    ]
    
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    link = models.CharField(null=True, blank=True, max_length=255, verbose_name=_("Link"))
    value = models.CharField(max_length=255, verbose_name=_("Value"))
    type = models.CharField(max_length=255, choices=CHOICES, default="phone", verbose_name=_("Type"))

    def __str__(self): 
        return self.title 

    class Meta:
        verbose_name = _("Contact Method")
        verbose_name_plural = _("Contact Methods")


class ContactMessage(BaseModel):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    phone = PhoneNumberField(region="IR", verbose_name=_("Phone number"))
    subject = models.CharField(max_length=255, verbose_name=_("Subject"))
    message = models.TextField(verbose_name=_("Message"))

    def __str__(self):
        return f"{self.name} - {self.subject}"

    class Meta:
        verbose_name = _("Contact message")
        verbose_name_plural = _("Contact messages")


class Article(BaseModel):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    image = models.ImageField(upload_to=upload_to_dynamic, verbose_name=_("Image"))
    short_description = models.TextField(null=True, blank=True, verbose_name=_("Short description"))
    content = RichTextField(verbose_name=_("Content"))
    
    def created_at_display(self):
        return jdatetime.datetime.fromgregorian(datetime=self.created_at).strftime('%Y-%m-%d')
    created_at_display.short_description = _("Created at")
    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")


class FAQ(BaseModel):
    question = models.CharField(max_length=255, verbose_name=_("Question"))
    answer = models.TextField(verbose_name=_("Answer"))
    is_active = models.BooleanField(default=True, verbose_name=_("Display status"))

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQs")


class Banner(BaseModel):

    PLACEMENT_CHOICES = [
        ('home', _("Home page")),
        ('app_home', _("App home")),
    ]

    title = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Title"))
    sub_title = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Subtitle"))
    image = models.ImageField(upload_to=upload_to_dynamic, verbose_name=_("Image"))
    link = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Link"), help_text=_("Example: https://example.com"))
    placement = models.CharField(max_length=50, choices=PLACEMENT_CHOICES, default='home', verbose_name=_("Placement"))
    sort = models.IntegerField(default=0, verbose_name=_("Display order"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    def __str__(self):
        return f"{self.title}"
    
    @property
    def is_valid_now(self):
        if not self.is_active:
            return False
        return True
    
    class Meta:
        verbose_name = _("Banner")
        verbose_name_plural = _("Banners")
