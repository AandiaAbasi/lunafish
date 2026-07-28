from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _

from recommendation.selectors.scale_selectors import (
    get_test_by_id,
    get_scale_by_id,
)
from recommendation.services.scale_service import (
    create_interpretation_formset,
    save_interpretation_formset,
)


def scale_interpretations_manage_view(request, test_id, scale_id):
    """
    Manage interpretations for a scale.
    (مدیریت بازه‌های تفسیری برای یک مقیاس)
    """

    test = get_test_by_id(test_id)
    if not test:
        messages.error(request, _('تست یافت نشد'))
        return redirect('recommendation:test_list')

    scale = get_scale_by_id(scale_id, test)
    if not scale:
        messages.error(request, _('مقیاس یافت نشد'))
        return redirect('recommendation:test_detail', test_id=test_id)

    if request.method == "POST":
        formset = create_interpretation_formset(scale)
        formset = formset.__class__(request.POST, instance=scale)  # بازسازی با داده POST

        if save_interpretation_formset(scale, formset):
            messages.success(request, _('بازه‌های تفسیری با موفقیت ذخیره شد'))
            return redirect('recommendation:test_detail', test_id=test_id)
        else:
            messages.error(request, _('لطفاً خطاهای فرم را برطرف کنید'))

    else:
        formset = create_interpretation_formset(scale)

    context = {
        "test": test,
        "scale": scale,
        "formset": formset,
    }

    return render(request, "recommendation/scale_interpretations.html", context)
