"""
Service layer for authentication and user management
Based on django-project pattern with Google/Apple login support
"""
import bcrypt
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import OTP, VerificationToken
from .utils import send_sms, send_teacher_sms, convert_persian_to_english

try:
    from .utils import send_email_otp
except ImportError:
    send_email_otp = None

logger = logging.getLogger(__name__)
User = get_user_model()

OTP_EXPIRE_MINUTES = 2
OTP_COOLDOWN_MINUTES = 2
TOKEN_EXPIRE_MINUTES = 30


class OTPDeliveryError(RuntimeError):
    """Raised when the OTP provider fails after an OTP was generated."""


def _hash_code(raw_code: str) -> str:
    return bcrypt.hashpw(raw_code.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_otp_code(user_input: str, hashed_otp: str) -> bool:
    """Verify OTP without logging the secret value."""
    try:
        return bcrypt.checkpw(user_input.encode('utf-8'), hashed_otp.encode('utf-8'))
    except (ValueError, TypeError) as exc:
        logger.warning("OTP hash verification failed: %s", exc)
        return False


def generate_otp():
    """Generate a cryptographically secure 6-digit OTP."""
    return ''.join(str(secrets.randbelow(10)) for _ in range(6))


def normalize_auth_target(phone_or_email: str) -> str:
    """Return canonical lower-case email or E.164 Iranian mobile number."""
    import phonenumbers

    if phone_or_email is None:
        raise ValueError(_("Phone number or email cannot be empty"))

    value = convert_persian_to_english(str(phone_or_email)).strip()
    if not value:
        raise ValueError(_("Phone number or email cannot be empty"))

    if '@' in value:
        return value.lower()

    compact = value.replace(' ', '').replace('-', '')
    if compact.startswith('0098'):
        compact = '+' + compact[2:]
    elif compact.startswith('98') and not compact.startswith('+98'):
        compact = '+' + compact

    try:
        parsed = phonenumbers.parse(compact, 'IR')
    except phonenumbers.NumberParseException as exc:
        raise ValueError(_("Invalid phone number")) from exc

    if (
        not phonenumbers.is_valid_number(parsed)
        or phonenumbers.region_code_for_number(parsed) != 'IR'
        or not str(parsed.national_number).startswith('9')
    ):
        raise ValueError(_("Invalid phone number"))

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def _phone_lookup_formats(canonical_phone: str):
    """Include legacy local format so OTPs created before this change still verify."""
    formats = {canonical_phone}
    if canonical_phone.startswith('+98'):
        formats.add('0' + canonical_phone[3:])
    return list(formats)


def _find_unique_user_for_email(email: str):
    users = list(User.objects.filter(email__iexact=email).order_by('id')[:2])
    if len(users) > 1:
        return None, _("Multiple accounts use this email. Please contact support or log in with username.")
    if not users:
        return None, None
    return users[0], None


def can_send_otp(phone_or_email: str, purpose: str = 'login') -> tuple:
    """Check the per-identifier OTP cooldown using canonical identifier formats."""
    try:
        identifier = normalize_auth_target(phone_or_email)
    except ValueError as exc:
        return False, str(exc)

    if '@' in identifier:
        last = OTP.objects.filter(email__iexact=identifier, purpose=purpose).order_by('-created_at').first()
    else:
        last = OTP.objects.filter(phone__in=_phone_lookup_formats(identifier), purpose=purpose).order_by('-created_at').first()

    if last and last.created_at:
        cutoff = timezone.now() - timedelta(minutes=OTP_COOLDOWN_MINUTES)
        if last.created_at > cutoff:
            return False, _("OTP has already been sent. Please try again in a few minutes.")
    return True, ""


def _sms_delivery_ok(response) -> bool:
    if response is True:
        return True
    if not isinstance(response, dict):
        return False
    status_value = response.get('status')
    if status_value in (1, '1', True, 200, '200', 'success', 'successful', 'ok'):
        return True
    return False


def generate_and_send_otp(phone_or_email: str, purpose='login', user=None, is_teacher=False):
    """Generate, persist and send OTP; never report success when delivery failed."""
    identifier = normalize_auth_target(phone_or_email)
    is_email = '@' in identifier

    # Delete stale OTPs for this exact purpose/identifier before issuing a new code.
    if is_email:
        OTP.objects.filter(email__iexact=identifier, purpose=purpose).delete()
    else:
        OTP.objects.filter(phone__in=_phone_lookup_formats(identifier), purpose=purpose).delete()

    raw_code = generate_otp()
    otp = OTP.objects.create(
        user=user,
        phone=None if is_email else identifier,
        email=identifier if is_email else None,
        code=_hash_code(raw_code),
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRE_MINUTES),
        purpose=purpose,
        failed_attempts=0,
    )

    try:
        if is_email:
            if not send_email_otp:
                raise OTPDeliveryError(_("Email authentication is not configured on this server"))
            delivered = send_email_otp(
                identifier,
                raw_code,
                user_type='teacher' if is_teacher else 'user',
            )
            if delivered is not True:
                raise OTPDeliveryError(_("Email provider failed to send the verification code"))
        else:
            sms_phone = '0' + identifier[3:] if identifier.startswith('+98') else identifier
            response = send_teacher_sms(sms_phone, raw_code) if is_teacher else send_sms(sms_phone, raw_code)
            if not _sms_delivery_ok(response):
                provider_message = response.get('message') if isinstance(response, dict) else None
                logger.warning("SMS OTP provider rejected request: %s", provider_message or 'unknown response')
                raise OTPDeliveryError(_("SMS provider failed to send the verification code"))
    except Exception:
        # A code the user never received must not remain valid in the database.
        otp.delete()
        raise

    logger.info("OTP delivered successfully for purpose=%s channel=%s", purpose, 'email' if is_email else 'sms')
    return True


def validate_otp(
    phone_or_email: str,
    raw_code: str,
    purpose='login',
    expected_role=None,
    registration_role='user',
):
    """Atomically validate/consume OTP with attempt limits and role binding."""
    try:
        identifier = normalize_auth_target(phone_or_email)
    except ValueError as exc:
        return False, str(exc)

    raw_code = convert_persian_to_english(str(raw_code)).strip()
    if len(raw_code) != 6 or not raw_code.isdigit():
        return False, _("Invalid verification code format")

    max_attempts = int(getattr(settings, 'OTP_MAX_ATTEMPTS', 5))
    now = timezone.now()

    with transaction.atomic():
        query = OTP.objects.select_for_update().filter(purpose=purpose, is_used=False)
        if '@' in identifier:
            otp = query.filter(email__iexact=identifier).order_by('-created_at').first()
        else:
            otp = query.filter(phone__in=_phone_lookup_formats(identifier)).order_by('-created_at').first()

        if not otp:
            return False, _("No verification code found. Please request a new one.")

        if otp.expires_at < now:
            otp.delete()
            return False, _("OTP has expired. Please request a new one.")

        if otp.failed_attempts >= max_attempts:
            otp.is_used = True
            otp.save(update_fields=['is_used', 'updated_at'])
            return False, _("Too many incorrect attempts. Please request a new verification code.")

        if not verify_otp_code(raw_code, otp.code):
            otp.failed_attempts += 1
            if otp.failed_attempts >= max_attempts:
                otp.is_used = True
            otp.save(update_fields=['failed_attempts', 'is_used', 'updated_at'])
            if otp.is_used:
                return False, _("Too many incorrect attempts. Please request a new verification code.")
            return False, _("OTP code is incorrect.")

        if purpose == 'registration':
            if registration_role not in {'user', 'teacher'}:
                return False, _("Invalid registration role")

            token_value = secrets.token_urlsafe(32)
            VerificationToken.objects.create(
                token=token_value,
                phone=otp.phone,
                email=otp.email.lower() if otp.email else None,
                expires_at=now + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
                target_role=registration_role,
            )
            otp.is_used = True
            otp.save(update_fields=['is_used', 'updated_at'])
            return True, {
                'verification_token': token_value,
                'phone': otp.phone,
                'email': otp.email,
            }

        user = otp.user
        if not user:
            if otp.phone:
                user = User.objects.filter(phone__in=_phone_lookup_formats(otp.phone)).first()
            elif otp.email:
                user, duplicate_error = _find_unique_user_for_email(otp.email)
                if duplicate_error:
                    return False, duplicate_error

        if not user:
            if purpose == 'login':
                return False, _("User account not found. Please register first.")
            return False, _("Unable to process OTP verification.")

        if not user.is_active:
            otp.is_used = True
            otp.save(update_fields=['is_used', 'updated_at'])
            return False, _("This account is inactive.")

        # Do not consume a valid OTP on the wrong role-specific endpoint. This lets
        # the user retry the same valid code on the correct teacher/student endpoint.
        if expected_role and user.role != expected_role:
            return False, _("This verification code belongs to a different account type.")

        otp.is_used = True
        otp.save(update_fields=['is_used', 'updated_at'])
        return True, user


def _auto_username(prefix: str, phone: str | None):
    base = phone.replace('+', '').replace('-', '')[-10:] if phone else secrets.token_hex(4)
    candidate = f"{prefix}_{base}"
    counter = 1
    while User.objects.filter(username=candidate).exists():
        candidate = f"{prefix}_{base}_{counter}"
        counter += 1
    return candidate


def _registration_identity_conflict(token):
    if token.phone and User.objects.filter(phone=token.phone).exists():
        return _("An account with this phone number already exists")
    if token.email and User.objects.filter(email__iexact=token.email).exists():
        return _("An account with this email already exists")
    return None


@transaction.atomic
def complete_registration(verification_token: str, username: str = None, password: str = None,
                          name: str = None, expo_push_token: str = None):
    """Complete student registration using a role-bound, one-time token."""
    token = VerificationToken.objects.select_for_update().filter(
        token=verification_token,
        is_used=False,
    ).first()
    if not token:
        return False, _("Invalid token")
    if token.expires_at < timezone.now():
        token.delete()
        return False, _("Token expired. Please register again.")
    if token.target_role != 'user':
        return False, _("This verification token is not valid for student registration")

    conflict = _registration_identity_conflict(token)
    if conflict:
        return False, conflict

    username = (username or '').strip() or _auto_username('user', token.phone)
    if User.objects.filter(username=username).exists():
        return False, _("Username already exists")

    try:
        with transaction.atomic():
            user = User.objects.create(
                username=username,
                phone=token.phone,
                email=token.email.lower() if token.email else None,
                role='user',
                name=(name or '').strip() or username,
                push_token=expo_push_token or None,
            )
            user.set_password(password)
            user.phone_verified_at = timezone.now() if token.phone else None
            user.email_verified_at = timezone.now() if token.email else None
            user.save()
    except IntegrityError:
        return False, _("An account with these registration details already exists")

    token.is_used = True
    token.save(update_fields=['is_used', 'updated_at'])
    return True, user


@transaction.atomic
def complete_teacher_registration(verification_token: str, username: str = None, password: str = None,
                                  name: str = None, bio: str = None, expo_push_token: str = None):
    """Complete teacher registration atomically, including wallet creation."""
    token = VerificationToken.objects.select_for_update().filter(
        token=verification_token,
        is_used=False,
    ).first()
    if not token:
        return False, _("Invalid token")
    if token.expires_at < timezone.now():
        token.delete()
        return False, _("Token expired. Please register again.")
    if token.target_role != 'teacher':
        return False, _("This verification token is not valid for teacher registration")

    conflict = _registration_identity_conflict(token)
    if conflict:
        return False, conflict

    username = (username or '').strip() or _auto_username('teacher', token.phone)
    if User.objects.filter(username=username).exists():
        return False, _("Username already exists")

    try:
        with transaction.atomic():
            user = User.objects.create(
                username=username,
                phone=token.phone,
                email=token.email.lower() if token.email else None,
                role='teacher',
                name=(name or '').strip() or username,
                bio=bio or '',
                push_token=expo_push_token or None,
            )
            user.set_password(password)
            user.phone_verified_at = timezone.now() if token.phone else None
            user.email_verified_at = timezone.now() if token.email else None
            user.save()

            # Keep the account and its wallet in the same transaction.
            from classroom.models import TeacherWallet
            TeacherWallet.objects.get_or_create(teacher=user)
    except IntegrityError:
        return False, _("An account with these registration details already exists")

    token.is_used = True
    token.save(update_fields=['is_used', 'updated_at'])
    return True, user


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