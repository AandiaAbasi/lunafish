from django.forms import inlineformset_factory
from recommendation.forms import InterpretationFormSet, ScaleInterpretationForm
from recommendation.models import TestScale, ScaleInterpretation
from recommendation.repository.scale_repository import ScaleInterpretationRepository


def create_interpretation_formset(scale):
    """
    تصمیم بگیر که کدام formset ساخته شود (extra=1 در صورت نداشتن Interpretation)
    """

    has_existing = scale.interpretations.exists()

    if not has_existing:
        DynamicFormSet = inlineformset_factory(
            TestScale,
            ScaleInterpretation,
            form=ScaleInterpretationForm,
            extra=1,
            can_delete=True,
            min_num=0,
            validate_min=False,
        )
        return DynamicFormSet(instance=scale)

    return InterpretationFormSet(instance=scale)


def save_interpretation_formset(scale, formset):
    """
    ذخیره تفسیرها بدون استفاده از formset.save()
    → داده‌های فرمست را استخراج می‌کنیم و به Repository می‌دهیم.
    """

    if not formset.is_valid():
        return False

    # استخراج دیتا (cleaned_data)
    interpretations_data = []
    for form in formset.forms:
        if not form.cleaned_data.get("DELETE", False):
            interpretations_data.append({
                "title_fa": form.cleaned_data.get("title_fa", ""),
                "title_en": form.cleaned_data.get("title_en", ""), 
                "description_fa": form.cleaned_data.get("description_fa", ""),
                "description_en": form.cleaned_data.get("description_en", ""), 
                "order": form.cleaned_data["order"],
                "min_score": form.cleaned_data["min_score"],
                "max_score": form.cleaned_data["max_score"],
            })

    # نوشتن در Repository
    ScaleInterpretationRepository.replace_scale_interpretations(
        scale,
        interpretations_data
    )

    return True
