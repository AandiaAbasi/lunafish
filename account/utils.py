"""
Utility functions for SMS and phone number processing
Based on alolebas pattern
"""
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_sms(phone_number, code):
    """Send OTP SMS to user"""
    url = "https://api.sms.ir/v1/send/verify"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": settings.SMSIR_API_KEY
    }
    data = {
        "mobile": phone_number,
        "templateId": "134611",  # Your SMS.ir template ID
        "parameters": [{"name": "CODE", "value": code}]
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        return response.json()
    except Exception as e:
        print(f"SMS Error: {e}")
        return {"status": "error", "message": str(e)}


def send_teacher_sms(phone_number, code):
    """Send OTP SMS to teacher"""
    url = "https://api.sms.ir/v1/send/verify"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": settings.SMSIR_API_KEY
    }
    data = {
        "mobile": phone_number,
        "templateId": "134611",  # Your SMS.ir template ID for teachers
        "parameters": [{"name": "CODE", "value": code}]
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        return response.json()
    except Exception as e:
        print(f"SMS Error: {e}")
        return {"status": "error", "message": str(e)}


def send_sms_general(phone_number, template_id, parameters):
    """Send SMS with custom template and parameters
    
    Args:
        phone_number: The mobile number to send SMS to
        template_id: The SMS.ir template ID
        parameters: List of dicts with 'name' and 'value' keys
                   Example: [{'name': 'NAME', 'value': 'John'}, {'name': 'CODE', 'value': '123456'}]
    
    Returns:
        Response from SMS.ir API
    """
    url = "https://api.sms.ir/v1/send/verify"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": settings.SMSIR_API_KEY
    }
    data = {
        "mobile": phone_number,
        "templateId": str(template_id),
        "parameters": parameters
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        return response.json()
    except Exception as e:
        print(f"SMS Error: {e}")
        return {"status": "error", "message": str(e)}


PERSIAN_TO_ENGLISH = {
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
    '٫': '.', '؛': ';', '؟': '?', '،': ',', '‌': '', 'ـ': ''
}


def convert_persian_to_english(phone_number):
    """Convert Persian/Arabic digits to English"""
    return ''.join(PERSIAN_TO_ENGLISH.get(char, char) for char in phone_number)


def format_phone_display(phone_number):
    """
    Convert phone number from +98 format to 09 format for display
    Examples:
        +989123456789 -> 09123456789
        +98 912 345 6789 -> 09123456789
        989123456789 -> 09123456789
    """
    if not phone_number:
        return ""
    
    # Remove all spaces and dashes
    cleaned = phone_number.replace(" ", "").replace("-", "").strip()
    
    # If starts with +98, replace with 0
    if cleaned.startswith("+98"):
        return "0" + cleaned[3:]
    
    # If starts with 98 (without +), replace with 0
    if cleaned.startswith("98") and len(cleaned) >= 12:
        return "0" + cleaned[2:]
    
    # If already starts with 0, return as is
    if cleaned.startswith("0"):
        return cleaned
    
    # Otherwise, add 0 at the beginning
    return "0" + cleaned


def send_email_otp(email, otp_code, user_type='user'):
    """
    Send OTP code to email address
    
    Args:
        email (str): Recipient email address
        otp_code (str): 6-digit OTP code
        user_type (str): 'user' or 'teacher'
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = 'Your Fofofish Verification Code'
        
        # Prepare email context
        context = {
            'otp_code': otp_code,
            'user_type': user_type,
            'app_name': 'Fofofish'
        }
        
        # Render HTML email
        html_message = render_to_string('emails/verify_email.html', context)
        plain_message = render_to_string('emails/verify_email.txt', context)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"[OK] Email OTP sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to send email OTP to {email}: {str(e)}")
        return False
