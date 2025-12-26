"""
Bilingual API Response Helper
Provides utilities for returning content in both languages (English and Persian)
"""
from django.utils.translation import gettext as _, activate, get_language
from django.conf import settings


class BilingualResponse:
    """Helper class for creating bilingual responses"""
    
    @staticmethod
    def get_language_from_request(request):
        """Get language from request header or settings"""
        lang = request.META.get('HTTP_ACCEPT_LANGUAGE', settings.LANGUAGE_CODE)
        if lang.startswith('fa'):
            return 'fa'
        return 'en'
    
    @staticmethod
    def activate_language(lang):
        """Activate a specific language"""
        if lang in ['fa', 'en']:
            activate(lang)
    
    @staticmethod
    def translate_text(text, to_lang='en'):
        """Translate text to specific language"""
        current_lang = get_language()
        try:
            BilingualResponse.activate_language(to_lang)
            translated = _(text)
            BilingualResponse.activate_language(current_lang)
            return translated
        except:
            return text
    
    @staticmethod
    def success_response(data=None, message=None, status_code=200, request=None):
        """Create a success response with optional message translation"""
        lang = BilingualResponse.get_language_from_request(request) if request else 'en'
        
        response = {
            'success': True,
            'message': message or _('Operation successful'),
            'data': data
        }
        return response
    
    @staticmethod
    def error_response(message, data=None, status_code=400, request=None):
        """Create an error response with message translation"""
        lang = BilingualResponse.get_language_from_request(request) if request else 'en'
        
        response = {
            'success': False,
            'message': message or _('An error occurred'),
            'data': data
        }
        return response


def get_bilingual_content(obj, lang='en'):
    """
    Extract bilingual content from an object
    Returns both 'en' and 'fa' versions
    """
    bilingual_data = {}
    
    for field in obj._meta.get_fields():
        field_name = field.name
        
        # Skip special fields
        if field_name in ['id', 'created_at', 'updated_at', 'is_deleted', 'deleted_at']:
            continue
        
        # Check for translation fields
        if field_name.endswith('_en') or field_name.endswith('_fa'):
            continue
        
        # Get base field value
        base_value = getattr(obj, field_name, None)
        
        # Check for translation variants
        en_value = getattr(obj, f'{field_name}_en', base_value)
        fa_value = getattr(obj, f'{field_name}_fa', base_value)
        
        # Add to response if has variants
        if en_value or fa_value or base_value:
            bilingual_data[field_name] = {
                'en': en_value or base_value,
                'fa': fa_value or base_value
            }
        else:
            bilingual_data[field_name] = base_value
    
    return bilingual_data
