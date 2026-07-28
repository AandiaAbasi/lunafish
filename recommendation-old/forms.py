from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from .form_settings import show_translation_fields
from .models import (
    PsychologicalTest, TestQuestion, QuestionOption,
    TestScale, OptionScaleWeight, ScaleInterpretation
)


class PhoneLoginForm(forms.Form):
    """Phone number login form for OTP-based authentication."""
    
    phone = forms.CharField(
        label=_('شماره تماس'),
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^09\d{9}$',
                message=_('شماره تماس باید ۱۱ رقم و با ۰۹ شروع شود'),
            )
        ],
        widget=forms.TextInput(attrs={
            'placeholder': '۰۹۱۲۳۴۵۶۷۸۹',
            'class': 'form-control',
            'maxlength': '11',
            'dir': 'ltr',
        })
    )


class UsernameLoginForm(forms.Form):
    """Username/password login form."""
    
    username = forms.CharField(
        label=_('شماره تماس یا کد ملی'),
        max_length=11,
        widget=forms.TextInput(attrs={
            'placeholder': 'شماره تماس یا کد ملی',
            'class': 'form-control',
            'dir': 'ltr',
        })
    )
    
    password = forms.CharField(
        label=_('رمز عبور'),
        widget=forms.PasswordInput(attrs={
            'placeholder': 'رمز عبور',
            'class': 'form-control',
        })
    )
    
    remember_me = forms.BooleanField(
        label=_('مرا به خاطر بسپار'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )


class OTPVerifyForm(forms.Form):
    """OTP verification form."""
    
    otp1 = forms.CharField(max_length=1, required=False)
    otp2 = forms.CharField(max_length=1, required=False)
    otp3 = forms.CharField(max_length=1, required=False)
    otp4 = forms.CharField(max_length=1, required=False)
    otp5 = forms.CharField(max_length=1, required=False)


class SetPasswordForm(forms.Form):
    """Password reset form."""
    
    password = forms.CharField(
        label=_('رمز عبور جدید'),
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'رمز عبور جدید',
            'class': 'form-control',
        })
    )
    
    confirm_password = forms.CharField(
        label=_('تایید رمز عبور'),
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'تایید رمز عبور',
            'class': 'form-control',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError(_('رمز عبور و تایید آن مطابقت ندارند'))
        
        return cleaned_data


class TranslationFieldVisibilityMixin:
    """Keep translated values in POST while hiding secondary-language controls."""

    secondary_language_suffixes = ("_en",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if show_translation_fields():
            return

        for field_name, field in self.fields.items():
            if field_name.endswith(self.secondary_language_suffixes):
                field.required = False
                field.widget = forms.HiddenInput()


# Psychological Test Forms
class PsychologicalTestForm(TranslationFieldVisibilityMixin, forms.ModelForm):
    """Form for creating/editing psychological tests with multilingual fields."""
    
    class Meta:
        model = PsychologicalTest
        fields = [
            'title_fa', 'title_en',
            'description_fa', 'description_en',
            'is_active',
        ]
        widgets = {
            'title_fa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان (فارسی)',
            }),
            'title_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Title (English)',
            }),

            'description_fa': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'توضیحات (فارسی)',
            }),
            'description_en': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description (English)',
            }),
             

            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }


class TestQuestionForm(TranslationFieldVisibilityMixin, forms.ModelForm):
    """Form for individual test questions."""
    
    class Meta:
        model = TestQuestion
        fields = [
            'question_text_fa', 'question_text_en',
            'question_type', 'order', 'is_required','icon'
        ]
        widgets = {
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'آیکون',
            }),
            'question_text_fa': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'متن سؤال (فارسی)',
            }),
            'question_text_en': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Question text (English)',
            }),
            'question_type': forms.Select(attrs={
                'class': 'form-select question-type-select',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control order-field',
                'min': 1,
            }),
            'is_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }


class QuestionOptionForm(TranslationFieldVisibilityMixin, forms.ModelForm):
    """Form for question options (multiple choice)."""
    
    class Meta:
        model = QuestionOption
        fields = [
            'option_text_fa', 'option_text_en',
            'order', 'icon'
        ]
        widgets = {
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'آیکون',
            }),
            'option_text_fa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'گزینه (فارسی)',
            }),
            'option_text_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option (English)',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
            }),
        }


# Formsets for nested forms
QuestionFormSet = inlineformset_factory(
    PsychologicalTest,
    TestQuestion,
    form=TestQuestionForm,
    extra=0,  # No extra blank forms - use JS to add questions
    can_delete=True,
    min_num=1,
    validate_min=True,
)

OptionFormSet = inlineformset_factory(
    TestQuestion,
    QuestionOption,
    form=QuestionOptionForm,
    extra=2,
    can_delete=True,
    min_num=0,
)



# ===== Scale and Interpretation Forms =====

class TestScaleForm(TranslationFieldVisibilityMixin, forms.ModelForm):
    """Form for defining psychological scales/factors."""
    
    class Meta:
        model = TestScale
        fields = [
            'code',
            'title_fa', 'title_en',
            'description_fa', 'description_en',
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: R, I, A',
                'maxlength': '20',
            }),
            'title_fa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: واقع‌گرا، پژوهشگر',
            }),
            'title_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Realistic, Investigative',
            }),
            'description_fa': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'توضیحات مقیاس (اختیاری)',
            }),
            'description_en': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Scale description (optional)',
            }), 
        }
        labels = {
            'code': _('کد مقیاس'),
            'title_fa': _('عنوان مقیاس (فارسی)'),
            'title_en': _('عنوان مقیاس (انگلیسی)'),
            'description_fa': _('توضیحات (فارسی)'),
            'description_en': _('توضیحات (انگلیسی)'), 
        }


class ScaleInterpretationForm(TranslationFieldVisibilityMixin, forms.ModelForm):
    """Form for defining interpretation ranges for scales."""
    
    class Meta:
        model = ScaleInterpretation
        fields = [
            'min_score', 'max_score',
            'title_fa', 'title_en',
            'description_fa', 'description_en',
            'order',
        ]
        widgets = {
            'min_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'مثال: 0',
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'مثال: 20',
            }),
            'title_fa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: رغبت پایین، رغبت متوسط، رغبت بالا',
            }),
            'title_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Low interest, Medium interest, High interest',
            }),
            'description_fa': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'تفسیر روانشناختی این بازه نمره',
            }),
            'description_en': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Psychological interpretation of this score range',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
            }),
        }
        labels = {
            'min_score': _('حداقل امتیاز'),
            'max_score': _('حداکثر امتیاز'),
            'title_fa': _('عنوان تفسیر (فارسی)'),
            'title_en': _('عنوان تفسیر (انگلیسی)'),
            'description_fa': _('توضیحات تفسیر (فارسی)'),
            'description_en': _('توضیحات تفسیر (انگلیسی)'),
            'order': _('ترتیب'),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        
        if min_score is not None and max_score is not None:
            if min_score > max_score:
                raise forms.ValidationError(_('حداقل امتیاز نمی‌تواند بزرگتر از حداکثر امتیاز باشد'))
        
        return cleaned_data
        
        
class OptionScaleWeightForm(forms.ModelForm):
    """Form for assigning weights to options for specific scales."""
    
    class Meta:
        model = OptionScaleWeight
        fields = ['scale', 'weight']
        widgets = {
            'scale': forms.Select(attrs={
                'class': 'form-select',
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': '0',
            }),
        }
        labels = {
            'scale': _('مقیاس'),
            'weight': _('وزن'),
        }


# Formsets for scales and interpretations
ScaleFormSet = inlineformset_factory(
    PsychologicalTest,
    TestScale,
    form=TestScaleForm,
    extra=0,  # No extra blank forms - use JS to add scales
    can_delete=True,
    can_delete_extra=False,
    min_num=0,
    validate_min=False,
)

InterpretationFormSet = inlineformset_factory(
    TestScale,
    ScaleInterpretation,
    form=ScaleInterpretationForm,
    extra=0,  # No extra blank forms - use JS button to add new interpretations
    can_delete=True,
    min_num=0,  # No minimum required - interpretations are optional
    validate_min=False,
)

WeightFormSet = inlineformset_factory(
    QuestionOption,
    OptionScaleWeight,
    form=OptionScaleWeightForm,
    extra=0,
    can_delete=True,
    min_num=0,
    validate_min=False,
)
