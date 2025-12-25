"""
Service layer for authentication and user management
Based on django-project pattern with Google/Apple login support
"""
import random
import hashlib
import bcrypt
import secrets
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from django.contrib.auth import get_user_model
from .models import OTP, VerificationToken
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from .utils import send_sms, send_teacher_sms, convert_persian_to_english

# Try to import email function, fallback if not available (for backward compatibility)
try:
    from .utils import send_email_otp
except ImportError:
    send_email_otp = None
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

OTP_EXPIRE_MINUTES = 2
OTP_COOLDOWN_MINUTES = 2
TOKEN_EXPIRE_MINUTES = 30  # Verification token expires in 30 minutes


def _hash_code(raw_code: str) -> str:
    """Hash the OTP code using bcrypt for storage"""
    return bcrypt.hashpw(raw_code.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_otp_code(user_input: str, hashed_otp: str) -> bool:
    """Verify OTP using constant-time comparison with bcrypt"""
    try:
        logger.info(f"Verifying OTP: input='{user_input}' (len={len(user_input)}), hash='{hashed_otp[:50]}...'")
        result = bcrypt.checkpw(user_input.encode('utf-8'), hashed_otp.encode('utf-8'))
        logger.info(f"bcrypt.checkpw result: {result}")
        return result
    except Exception as e:
        logger.error(f"OTP verification error: {e}")
        return False


def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def can_send_otp(phone_or_email: str, purpose: str = 'login') -> tuple:
    """Check if OTP can be sent (cooldown period)"""
    last = OTP.objects.filter(
        phone=phone_or_email,
        purpose=purpose
    ).order_by("-created_at").first()
    
    if not last:
        # Try email
        last = OTP.objects.filter(
            email=phone_or_email,
            purpose=purpose
        ).order_by("-created_at").first()
    
    if last:
        cutoff = timezone.now() - timedelta(minutes=OTP_COOLDOWN_MINUTES)
        if last.created_at > cutoff:
            return False, _("OTP has already been sent. Please try again in a few minutes.")
    return True, ""


def generate_and_send_otp(phone_or_email: str, purpose='login', user=None, is_teacher=False):
    """Generate OTP and send via SMS or Email"""
    if not phone_or_email:
        raise ValueError(_("Phone number or email cannot be empty"))
    
    logger.info(f"Generating OTP for: {phone_or_email}, purpose: {purpose}, is_teacher: {is_teacher}")
    
    # Convert Persian/Arabic digits to English
    phone_or_email = convert_persian_to_english(phone_or_email)
    
    # Normalize phone to +98 format if it's a phone number
    import phonenumbers
    is_phone = phone_or_email.startswith('09') or phone_or_email.startswith('+98')
    normalized_phone = phone_or_email
    
    if is_phone:
        try:
            if phone_or_email.startswith('09'):
                # Convert 09xxxxxxxxx to +989xxxxxxxxx
                phone_obj = phonenumbers.parse(phone_or_email, "IR")
                normalized_phone = phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)
            elif phone_or_email.startswith('+98'):
                # Already in +98 format
                normalized_phone = phone_or_email
            
            logger.info(f"Normalized phone from {phone_or_email} to {normalized_phone}")
        except Exception as e:
            logger.error(f"Phone normalization error: {e}")
            normalized_phone = phone_or_email
    
    # Normalize phone to multiple formats for deletion
    phones_to_delete = [normalized_phone]
    if phone_or_email.startswith('09'):
        try:
            phone_obj = phonenumbers.parse(phone_or_email, "IR")
            e164_phone = phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)
            phones_to_delete.append(e164_phone)
        except Exception as e:
            logger.error(f"Phone parsing error: {e}")
    elif phone_or_email.startswith('+98'):
        try:
            phone_obj = phonenumbers.parse(phone_or_email, None)
            local_phone = '0' + str(phone_obj.national_number)
            phones_to_delete.append(local_phone)
        except Exception as e:
            logger.error(f"Phone parsing error: {e}")
    
    # Delete old OTPs for all phone formats
    for phone in phones_to_delete:
        deleted_count = OTP.objects.filter(phone=phone, purpose=purpose).count()
        OTP.objects.filter(phone=phone, purpose=purpose).delete()
        logger.info(f"Deleted {deleted_count} old OTPs for phone: {phone}")
    OTP.objects.filter(email=phone_or_email, purpose=purpose).delete()

    # Generate new OTP
    raw_code = generate_otp()
    hashed = _hash_code(raw_code)
    
    logger.info(f"Generated OTP code: {raw_code} (will be hashed and stored)")
    
    otp = OTP.objects.create(
        user=user,
        phone=normalized_phone if is_phone else None,
        email=phone_or_email if not is_phone else None,
        code=hashed,
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRE_MINUTES),
        purpose=purpose
    )
    
    logger.info(f"Created OTP with phone={otp.phone}, email={otp.email}, expires_at={otp.expires_at}")

    # Send SMS using utils.py functions
    if is_phone:
        sms_phone = normalized_phone
        if normalized_phone.startswith('+98'):
            try:
                phone_obj = phonenumbers.parse(normalized_phone, None)
                sms_phone = '0' + str(phone_obj.national_number)
            except Exception as e:
                logger.error(f"Phone conversion error: {e}")
        
        if is_teacher:
            send_teacher_sms(sms_phone, raw_code)
        else:
            send_sms(sms_phone, raw_code)
        logger.info(f"SMS sent to {sms_phone} with code {raw_code}")
    else:
        # Send email OTP
        if send_email_otp:
            send_email_otp(phone_or_email, raw_code, user_type='teacher' if is_teacher else 'user')
            logger.info(f"Email OTP sent to {phone_or_email} with code {raw_code}")
        else:
            logger.warning(f"Email OTP function not available. Code: {raw_code}")
    
    return raw_code



def validate_otp(phone_or_email: str, raw_code: str, purpose='login'):
    """Validate OTP and return user or create if registration"""
    import phonenumbers
    
    # Convert Persian/Arabic digits to English
    phone_or_email = convert_persian_to_english(phone_or_email)
    raw_code = convert_persian_to_english(raw_code)
    
    logger.info(f"Validating OTP for: {phone_or_email}, purpose: {purpose}")
    
    # Normalize phone to +98 format if it's a phone number
    is_phone = phone_or_email.startswith('09') or phone_or_email.startswith('+98')
    normalized_phone = phone_or_email
    
    if is_phone:
        try:
            if phone_or_email.startswith('09'):
                # Convert 09xxxxxxxxx to +989xxxxxxxxx
                phone_obj = phonenumbers.parse(phone_or_email, "IR")
                normalized_phone = phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)
            elif phone_or_email.startswith('+98'):
                # Already in +98 format
                normalized_phone = phone_or_email
            
            logger.info(f"Normalized phone from {phone_or_email} to {normalized_phone}")
        except Exception as e:
            logger.error(f"Phone normalization error: {e}")
            normalized_phone = phone_or_email
    
    phone_formats = [normalized_phone]
    
    if phone_or_email.startswith('09'):
        try:
            phone_obj = phonenumbers.parse(phone_or_email, "IR")
            e164_phone = phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)
            phone_formats.append(e164_phone)
        except Exception as e:
            logger.error(f"Phone parsing error: {e}")
    elif phone_or_email.startswith('+98'):
        try:
            phone_obj = phonenumbers.parse(phone_or_email, None)
            local_phone = '0' + str(phone_obj.national_number)
            phone_formats.append(local_phone)
        except Exception as e:
            logger.error(f"Phone parsing error: {e}")
    
    otp = None
    for phone_format in phone_formats:
        otp = OTP.objects.filter(
            phone=phone_format,
            purpose=purpose,
            is_used=False
        ).order_by('-created_at').first()
        if otp:
            break
    
    if not otp:
        otp = OTP.objects.filter(
            email=phone_or_email,
            purpose=purpose,
            is_used=False
        ).order_by('-created_at').first()
    
    if not otp:
        return False, _("No OTP found for this phone/email.")
    
    if otp.expires_at < timezone.now():
        otp.delete()
        return False, _("OTP has expired. Please request a new one.")
    
    verification_result = verify_otp_code(raw_code, otp.code)
    
    if verification_result:
        otp.is_used = True
        otp.save()
        
        if purpose == 'registration':
            token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
            
            # Normalize phone for storage
            stored_phone = otp.phone
            if stored_phone and stored_phone.startswith('09'):
                try:
                    phone_obj = phonenumbers.parse(stored_phone, "IR")
                    stored_phone = phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)
                except Exception as e:
                    logger.error(f"Phone normalization error: {e}")
            
            VerificationToken.objects.create(
                token=token,
                phone=stored_phone,
                email=otp.email,
                expires_at=expires_at
            )
            
            return True, {'verification_token': token, 'phone': stored_phone, 'email': otp.email}
        
        if otp.user:
            user = otp.user
        else:
            if otp.phone:
                # Use normalized +98 format for phone in database
                stored_phone = otp.phone
                if stored_phone.startswith('09'):
                    try:
                        phone_obj = phonenumbers.parse(stored_phone, "IR")
                        stored_phone = phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)
                    except Exception as e:
                        logger.error(f"Phone normalization error: {e}")
                
                username = f"user_{stored_phone.replace('+', '').replace(' ', '')}"
                user, created = User.objects.get_or_create(
                    phone=stored_phone,
                    defaults={'username': username, 'role': 'user'}
                )
            else:
                username = otp.email.split('@')[0]
                user, created = User.objects.get_or_create(
                    email=otp.email,
                    defaults={'username': username, 'role': 'user'}
                )
        
        return True, user
    
    return False, _("OTP code is incorrect.")


@transaction.atomic
def complete_registration(verification_token: str, username: str, password: str, 
                         name: str = None, expo_push_token: str = None):
    """Complete registration with username/password"""
    import phonenumbers
    
    token = VerificationToken.objects.filter(token=verification_token, is_used=False).first()
    
    if not token:
        return False, _("Invalid token")
    
    if token.expires_at < timezone.now():
        token.delete()
        return False, _("Token expired. Please register again.")
    
    if User.objects.filter(username=username).exists():
        return False, _("Username already exists")
    
    try:
        # Normalize phone to +98 format if needed
        stored_phone = token.phone
        if stored_phone and stored_phone.startswith('09'):
            try:
                phone_obj = phonenumbers.parse(stored_phone, "IR")
                stored_phone = phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)
            except Exception as e:
                logger.error(f"Phone normalization error: {e}")
        
        user = User.objects.create(
            username=username,
            phone=stored_phone,
            email=token.email,
            role='user',
            name=name or username  # Use provided name or fallback to username
        )
        user.set_password(password)
        user.phone_verified_at = timezone.now() if stored_phone else None
        user.email_verified_at = timezone.now() if token.email else None
        user.save()
    
        if expo_push_token:
            pass  # handle push token if needed
        
        token.is_used = True
        token.save()
        
        return True, user
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return False, f"Registration error: {str(e)}"


def complete_teacher_registration(verification_token: str, username: str, password: str, 
                                  name: str = None, bio: str = None, expo_push_token: str = None):
    """Complete teacher registration with username/password"""
    import phonenumbers
    
    token = VerificationToken.objects.filter(token=verification_token, is_used=False).first()
    
    if not token:
        return False, _("Invalid token")
    
    if token.expires_at < timezone.now():
        token.delete()
        return False, _("Token expired. Please register again.")
    
    if User.objects.filter(username=username).exists():
        return False, _("Username already exists")
    
    try:
        # Normalize phone to +98 format if needed
        stored_phone = token.phone
        if stored_phone and stored_phone.startswith('09'):
            try:
                phone_obj = phonenumbers.parse(stored_phone, "IR")
                stored_phone = phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)
            except Exception as e:
                logger.error(f"Phone normalization error: {e}")
        
        user = User.objects.create(
            username=username,
            phone=stored_phone,
            email=token.email,
            role='teacher',
            name=name or username,  # Use provided name or fallback to username
            bio=bio or ""  # Add bio for teacher profile
        )
        user.set_password(password)
        user.phone_verified_at = timezone.now() if stored_phone else None
        user.email_verified_at = timezone.now() if token.email else None
        user.save()
    
        if expo_push_token:
            pass  # handle push token if needed
        
        token.is_used = True
        token.save()
        
        return True, user
    except Exception as e:
        logger.error(f"Teacher registration error: {e}")
        return False, f"Teacher registration error: {str(e)}"


def update_user_profile(user, data, files=None):
    """Update user profile"""
    if 'bio' in data:
        user.bio = data['bio']
    if 'gender' in data:
        user.gender = data['gender']
    if 'birth_date' in data:
        user.birth_date = data['birth_date']
    if files and 'profile_photo_path' in files:
        user.profile_photo_path = files['profile_photo_path']
    
    user.save()
    return True, None


def change_user_password(user, new_password):
    """Change user password with validation"""
    try:
        validate_password(new_password, user=user)
    except ValidationError as exc:
        raise ValidationError(exc)

    user.set_password(new_password)
    user.save()
    return True


def promote_to_teacher(user):
    """Promote user to teacher role"""
    if user.role == 'teacher':
        return False, _("User is already a teacher")
    
    user.role = 'teacher'
    user.teacher_verification_requested_at = timezone.now()
    user.save()
    
    return True, _("Teacher promotion request submitted and awaiting approval")


def verify_teacher(user, verified=True):
    """Verify or reject teacher. Only admin can call this."""
    if user.role != 'teacher':
        return False, _("User is not a teacher")
    
    user.is_teacher_verified = verified
    user.save()
    
    if verified:
        return True, _("Teacher verified")
    else:
        return True, _("Teacher verification revoked")