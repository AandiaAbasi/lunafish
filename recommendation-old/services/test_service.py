from django.db.models import Count, Q
from recommendation.models import PsychologicalTest, QuestionOption, TestScale, OptionScaleWeight
from recommendation.repository import save_weight_items
from recommendation.dto import SaveWeightsDTO, WeightItem

class TestService:



    @staticmethod
    def create_test(form, question_formset, scale_formset, post_data):
    
        test = form.save()
    
        questions = question_formset.save(commit=False)
    
        for index, question in enumerate(questions):
            question.test = test
            question.save()
            
            option_index = 0
            
            while True:
            
                icon = post_data.get(f'options-{index}-{option_index}-icon', '').strip()
                fa = post_data.get(f'options-{index}-{option_index}-option_text_fa', '').strip()
                en = post_data.get(f'options-{index}-{option_index}-option_text_en', '').strip()
            
                if not fa and not en:
                    break
            
                QuestionOption.objects.create(
                    question=question,
                    icon=icon,
                    option_text_fa=fa,
                    option_text_en=en,
                    order=option_index + 1
                )
            
                option_index += 1
    
    
        for obj in question_formset.deleted_objects:
            obj.delete()
    
        scales = scale_formset.save(commit=False)
    
        for scale in scales:
            scale.test = test
            scale.save()
    
        for obj in scale_formset.deleted_objects:
            obj.delete()
    
        return test
    
    
    @staticmethod
    def update_test(test, form, question_formset, scale_formset, post_data):
        
    
        form.save()
    
        question_formset.save()
    
        all_questions = test.questions.all().order_by('order')
    
        for idx, question in enumerate(all_questions):
    
            question.options.all().delete()
            
            option_index = 0
            
            while True:
            
                icon = post_data.get(f'options-{idx}-{option_index}-icon', '').strip()
                fa = post_data.get(f'options-{idx}-{option_index}-option_text_fa', '').strip()
                en = post_data.get(f'options-{idx}-{option_index}-option_text_en', '').strip()
                
                if not fa and not en:
                    break
                
                QuestionOption.objects.create(
                    question=question,
                    icon=icon,
                    option_text_fa=fa,
                    option_text_en=en,
                    order=option_index + 1
                )
            
                option_index += 1
    
    
        for obj in question_formset.deleted_objects:
            obj.delete()
    
        scales = scale_formset.save(commit=False)
    
        for scale in scales:
            scale.test = test
            scale.save()
        
    
        for obj in scale_formset.deleted_objects:
            obj.delete()
    
        return test


    @staticmethod
    def save_weights(dto: SaveWeightsDTO):

        if not dto.items:
            return 0

        # Business rules / validation
        for item in dto.items:
            if item.weight < 0:
                raise ValueError("Weight cannot be negative")

        # call repository
        return save_weight_items(dto.items)
