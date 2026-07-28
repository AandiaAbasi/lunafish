from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import HttpResponseNotFound
from recommendation.forms import PsychologicalTestForm, QuestionFormSet, ScaleFormSet, TestScale, ScaleInterpretation, InterpretationFormSet, ScaleInterpretationForm
from recommendation.models import PsychologicalTest
from recommendation.services.test_service import TestService
from recommendation.selectors import list_tests, get_test_detail_queryset
from recommendation.repository import delete_test
from recommendation.dto import SaveWeightsDTO, WeightItem
from django.forms import inlineformset_factory
import logging
logger = logging.getLogger(__name__)

def test_list_view(request):

    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')

    tests = list_tests(search_query, status_filter)

    context = {
        "tests": tests,
        "search_query": search_query,
        "status_filter": status_filter
    }

    return render(request, "recommendation/list.html", context)



def test_create_view(request):

    if request.method == "POST":
        
        form = PsychologicalTestForm(request.POST)
        question_formset = QuestionFormSet(request.POST)
        scale_formset = ScaleFormSet(request.POST)

        if form.is_valid() and question_formset.is_valid() and scale_formset.is_valid():

            try:

                test = TestService.create_test(
                    form,
                    question_formset,
                    scale_formset,
                    request.POST
                )

                messages.success(request, _("Test created successfully"))

                return redirect("recommendation:test_detail", test_id=test.id)

            except Exception as e:

                messages.error(request, str(e))

    else:

        form = PsychologicalTestForm()
        question_formset = QuestionFormSet()
        scale_formset = ScaleFormSet()

    context = {
        "form": form,
        "question_formset": question_formset,
        "scale_formset": scale_formset,
        "is_create": True
    }

    return render(request, "recommendation/create.html", context)



def test_detail_view(request, test_id):

    test = get_object_or_404(get_test_detail_queryset(), id=test_id)
    scales = test.scales.all()
    questions_with_options = test.questions.filter(
        question_type='multiple_choice',
        options__isnull=False
    ).distinct().count()
    
    total_mc_questions = test.questions.filter(question_type='multiple_choice').count()
    can_assign_weights = scales.exists() and (questions_with_options == total_mc_questions)


    context = {
        "test": test,
        "scales": scales,
        'can_assign_weights': can_assign_weights,

    }

    return render(request, "recommendation/detail.html", context)



def test_edit_view(request, test_id):

    test = get_object_or_404(PsychologicalTest, id=test_id)

    if request.method == "POST":

        form = PsychologicalTestForm(request.POST, instance=test)
        question_formset = QuestionFormSet(request.POST, instance=test)
        scale_formset = ScaleFormSet(request.POST, instance=test)
        
        if form.is_valid() and question_formset.is_valid() and scale_formset.is_valid():

            try:

                TestService.update_test(
                    test,
                    form,
                    question_formset,
                    scale_formset,
                    request.POST
                )

                messages.success(request, _("Test updated successfully"))

                return redirect("recommendation:test_detail", test_id=test.id)

            except Exception as e:

                messages.error(request, str(e))

    else:

        form = PsychologicalTestForm(instance=test)
        question_formset = QuestionFormSet(instance=test)
        scale_formset = ScaleFormSet(instance=test)
        
    context = {
        "test": test,
        "form": form,
        "question_formset": question_formset,
        "scale_formset": scale_formset,
        "is_create": False
    }

    return render(request, "recommendation/create.html", context)



def test_delete_view(request, test_id):

    success = delete_test(test_id)

    if not success:
        return HttpResponseNotFound("Test not found")

    messages.success(request, _("Test deleted successfully"))

    return redirect("recommendation:test_list")



def test_weights_view(request, test_id):

    from recommendation.models import PsychologicalTest, TestScale, QuestionOption, OptionScaleWeight
    
    try:
        test = PsychologicalTest.objects.prefetch_related(
            'scales',
            'questions__options'
        ).get(
            id=test_id,  
        )
    except PsychologicalTest.DoesNotExist:
        messages.error(request, _('تست یافت نشد'))
        return redirect('recommendation:test_list')
    
    # Get scales
    scales = test.scales.all().order_by('code')
    
    if not scales.exists():
        messages.warning(request, _('ابتدا باید مقیاس‌ها را تعریف کنید'))
        return redirect('recommendation:test_edit', test_id=test.id)
    
    # Get all multiple choice questions with their options
    questions = test.questions.filter(question_type='multiple_choice').prefetch_related('options').order_by('order')
    
    if not questions.exists():
        messages.warning(request, _('این تست سوال چند گزینه‌ای ندارد'))
        return redirect('recommendation:test_detail', test_id=test.id)
    
    # Check if any question has no options
    questions_without_options = [q for q in questions if not q.options.exists()]
    if questions_without_options:
        messages.warning(request, _('برخی سوالات هنوز گزینه ندارند. لطفاً ابتدا گزینه‌ها را اضافه کنید'))
        return redirect('recommendation:test_edit', test_id=test.id)
    
    if request.method == 'POST':
        try:
            # Parse submitted weights
            # Format: weight_option_{option_id}_scale_{scale_id} = weight_value
            saved_count = 0
            
            for key, value in request.POST.items():
                if key.startswith('weight_option_'):
                    parts = key.split('_')
                    if len(parts) >= 5:  # weight_option_{id}_scale_{id}
                        option_id = int(parts[2])
                        scale_id = int(parts[4])
                        
                        try:
                            weight_value = float(value) if value.strip() else 0.0
                        except ValueError:
                            continue
                        
                        # Get or create weight
                        option = QuestionOption.objects.get(id=option_id)
                        scale = TestScale.objects.get(id=scale_id)
                        
                        if weight_value == 0.0:
                            # Delete if exists
                            OptionScaleWeight.objects.filter(
                                option=option,
                                scale=scale
                            ).delete()
                        else:
                            # Create or update
                            OptionScaleWeight.objects.update_or_create(
                                option=option,
                                scale=scale,
                                defaults={'weight': weight_value}
                            )
                            saved_count += 1
            
            messages.success(request, _(f'وزن‌ها با موفقیت ذخیره شد ({saved_count} مورد)'))
            return redirect('recommendation:test_detail', test_id=test.id)
            
        except Exception as e:
            messages.error(request, _(f'خطا در ذخیره وزن‌ها: {str(e)}'))
    
    # Prepare weight matrix data
    # Get existing weights
    existing_weights = {}
    for weight_obj in OptionScaleWeight.objects.filter(
        option__question__test=test,
        scale__test=test
    ).select_related('option', 'scale'):
        key = f"{weight_obj.option.id}_{weight_obj.scale.id}"
        existing_weights[key] = weight_obj.weight
    
    # Build matrix data structure
    matrix_data = []
    for question in questions:
        question_data = {
            'question': question,
            'options': []
        }
        for option in question.options.all().order_by('order'):
            option_data = {
                'option': option,
                'weights': {}
            }
            for scale in scales:
                key = f"{option.id}_{scale.id}"
                option_data['weights'][scale.code] = existing_weights.get(key, 0.0)
            question_data['options'].append(option_data)
        matrix_data.append(question_data)
    
    context = {
        'test': test,
        'scales': scales,
        'matrix_data': matrix_data,
    }
    

    return render(request, "recommendation/weights_matrix.html", context)



def scale_interpretations_manage_view(request, test_id, scale_id):
    """
    Manage interpretations for a scale.
    مدیریت بازه‌های تفسیری برای یک مقیاس
    """  
    
     
    try:
        test = PsychologicalTest.objects.get(
            id=test_id, 
        )
    except PsychologicalTest.DoesNotExist:
        messages.error(request, _('تست یافت نشد'))
        return redirect('recommendation:test_list')
    
    # Get scale
    try:
        scale = TestScale.objects.get(id=scale_id, test=test)
    except TestScale.DoesNotExist:
        messages.error(request, _('مقیاس یافت نشد'))
        return redirect('recommendation:test_detail', test_id=test_id)
    
    if request.method == 'POST':
        formset = InterpretationFormSet(request.POST, instance=scale)
        
        if formset.is_valid():
            formset.save()
            messages.success(request, _('بازه‌های تفسیری با موفقیت ذخیره شد'))
            return redirect('recommendation:test_detail', test_id=test_id)
        else:
            messages.error(request, _('لطفاً خطاهای فرم را برطرف کنید'))
    else:
        # Check if scale has existing interpretations
        has_existing = scale.interpretations.exists()
        
        # If no existing interpretations, create formset with 1 extra form
        if not has_existing:
             
            
            DynamicInterpretationFormSet = inlineformset_factory(
                TestScale,
                ScaleInterpretation,
                form=ScaleInterpretationForm,
                extra=1,  # Show 1 blank form when no existing data
                can_delete=True,
                min_num=0,
                validate_min=False,
            )
            formset = DynamicInterpretationFormSet(instance=scale)
        else:
            # Use the default formset (extra=0)
            formset = InterpretationFormSet(instance=scale)
    
    context = {
        'test': test,
        'scale': scale,
        'formset': formset,
    }
    
    return render(request, 'recommendation/scale_interpretations.html', context)