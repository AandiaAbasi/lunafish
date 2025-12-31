"""Unified serializers for role-based User with social auth"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, AvatarTemplate
from . import services

def convert_persian_to_english_digits(text):
    """Convert Persian/Arabic digits to English digits"""
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    arabic_digits = '٠١٢٣٤٥٦٧٨٩'
    english_digits = '0123456789'
    
    translation_table = str.maketrans(
        persian_digits + arabic_digits,
        english_digits + english_digits
    )
    return text.translate(translation_table)

# Username Check
class CheckUsernameSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=150)

# Authentication
class SendOTPSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    purpose = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        # Accept identifier, phone_number, or phone
        identifier = data.get('identifier') or data.get('phone_number') or data.get('phone')
        if not identifier:
            raise serializers.ValidationError({"phone": _("Phone number or email is required")})
        
        # Convert Persian/Arabic digits to English
        identifier = convert_persian_to_english_digits(identifier)
        data['identifier'] = identifier
        
        # Normalize and validate purpose
        purpose = data.get('purpose', 'login') or 'login'
        if purpose == 'register':
            purpose = 'registration'
        
        valid_purposes = ['registration', 'login', 'phone_verification', 'email_verification', 'password_reset']
        if purpose not in valid_purposes:
            raise serializers.ValidationError({"purpose": _("Invalid purpose. Must be one of: {valid_purposes}").format(valid_purposes=', '.join(valid_purposes))})
        
        data['purpose'] = purpose
        
        return data


class VerifyOTPSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    code = serializers.CharField(min_length=6, max_length=6)
    purpose = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        # Accept identifier, phone_number, or phone
        identifier = data.get('identifier') or data.get('phone_number') or data.get('phone')
        if not identifier:
            raise serializers.ValidationError({"phone": _("Phone number or email is required")})
        
        # Convert Persian/Arabic digits to English
        identifier = convert_persian_to_english_digits(identifier)
        data['identifier'] = identifier
        
        # Validate and convert code
        code = data.get('code', '')
        if not code:
            raise serializers.ValidationError({"code": _("Verification code is required")})
        
        code = convert_persian_to_english_digits(code)
        if not code.isdigit():
            raise serializers.ValidationError({"code": _("Code must be numeric")})
        
        if len(code) != 6:
            raise serializers.ValidationError({"code": _("Code must be 6 digits")})
        
        data['code'] = code
        
        # Normalize and validate purpose
        purpose = data.get('purpose', 'login') or 'login'
        if purpose == 'register':
            purpose = 'registration'
        
        valid_purposes = ['registration', 'login', 'phone_verification', 'email_verification', 'password_reset']
        if purpose not in valid_purposes:
            raise serializers.ValidationError({"purpose": _("Invalid purpose. Must be one of: {valid_purposes}").format(valid_purposes=', '.join(valid_purposes))})
        
        data['purpose'] = purpose
        
        return data


class CompleteRegistrationSerializer(serializers.Serializer):
    verification_token = serializers.CharField()
    username = serializers.CharField(min_length=3, max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(min_length=6, write_only=True)
    
    # Optional fields
    name = serializers.CharField(max_length=300, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    expo_push_token = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_username(self, value):
        # If username is not provided, it will be auto-generated from phone number
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_("This username is already taken"))
        return value
    
    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class CompleteTeacherRegistrationSerializer(serializers.Serializer):
    """Serializer for completing teacher registration"""
    verification_token = serializers.CharField()
    username = serializers.CharField(min_length=3, max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(min_length=6, write_only=True)
    
    # Optional fields
    name = serializers.CharField(max_length=300, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    bio = serializers.CharField(max_length=500, required=False, allow_blank=True)
    expo_push_token = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_username(self, value):
        # If username is not provided, it will be auto-generated from phone number
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_("This username is already taken"))
        return value
    
    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=False)
    confirm_password = serializers.CharField(required=False)
    
    # Alternative field names for mobile app compatibility
    password = serializers.CharField(required=False, write_only=True)
    password_confirmation = serializers.CharField(required=False, write_only=True)
    
    def validate(self, attrs):
        new_password = attrs.get('new_password') or attrs.get('password')
        confirm_password = attrs.get('confirm_password') or attrs.get('password_confirmation')
        
        if not new_password:
            raise serializers.ValidationError({'new_password': _('New password is required')})
        if not confirm_password:
            raise serializers.ValidationError({'confirm_password': _('Password confirmation is required')})
        if new_password != confirm_password:
            raise serializers.ValidationError({'confirm_password': _('Passwords do not match')})
        
        try:
            validate_password(new_password)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})
        
        attrs['new_password'] = new_password
        attrs['confirm_password'] = confirm_password
        return attrs


# Profile
class UserProfileSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_teacher = serializers.SerializerMethodField()
    selected_avatar_id = serializers.IntegerField(source='selected_avatar.id', read_only=True, allow_null=True)
    selected_avatar_image = serializers.ImageField(source='selected_avatar.image', read_only=True, allow_null=True)
    
    class Meta:
        model = User
        fields = ['id','username','name','email','phone','profile_photo_path','bio','gender','birth_date','role','role_display','is_teacher','is_teacher_verified','selected_avatar_id','selected_avatar_image','date_joined']
        read_only_fields = ['id','username','role','is_teacher_verified','date_joined','selected_avatar_id','selected_avatar_image']
    
    def get_is_teacher(self,obj):
        return obj.role == 'teacher'


class EditUserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, min_length=3, max_length=150)
    birth_date = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=10,
        help_text=_("Birth date in Jalali format (YYYY-MM-DD), e.g., 1403-05-24")
    )
    
    class Meta:
        model = User
        fields = ['username','name','bio','gender','birth_date','profile_photo_path']
        extra_kwargs = {'profile_photo_path':{'required':False}}
    
    def validate_birth_date(self, value):
        """Validate birth date format"""
        if value:
            import re
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                raise serializers.ValidationError(
                    _("Birth date must be in YYYY-MM-DD format (Jalali calendar), e.g., 1403-05-24")
                )
        return value
    
    def validate_username(self, value):
        """Validate username format and uniqueness"""
        if not value:
            return value
        
        value = value.strip()
        
        # Validate format: only letters, numbers, and underscores
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(_("Username can only contain letters, numbers, and underscores."))
        
        # Check minimum length
        if len(value) < 3:
            raise serializers.ValidationError(_("Username must be at least 3 characters long."))
        
        # Check if username is taken by another user
        if self.instance and value != self.instance.username:
            if User.objects.filter(username=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(_("This username is already taken. Please choose another one."))
        
        return value


class CompleteStudentProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for completing student profile with basic information.
    Students can set: name, age (birth_date), gender, and select an avatar.
    Birth date should be in Jalali calendar format (YYYY-MM-DD).
    """
    birth_date = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=10,
        help_text=_("Birth date in Jalali format (YYYY-MM-DD), e.g., 1403-05-24")
    )
    selected_avatar_id = serializers.IntegerField(
        required=False,
        write_only=True,
        help_text=_("ID of the avatar template to select")
    )
    
    class Meta:
        model = User
        fields = ['name', 'birth_date', 'gender', 'selected_avatar_id']
        extra_kwargs = {
            'name': {'required': False},
            'birth_date': {'required': False},
            'gender': {'required': False},
        }
    
    def validate_birth_date(self, value):
        """Validate birth date format"""
        if value:
            import re
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                raise serializers.ValidationError(
                    _("Birth date must be in YYYY-MM-DD format (Jalali calendar), e.g., 1403-05-24")
                )
        return value
    
    def validate_selected_avatar_id(self, value):
        """Validate that avatar exists"""
        if value:
            if not AvatarTemplate.objects.filter(id=value).exists():
                raise serializers.ValidationError(_("Selected avatar does not exist"))
        return value
    
    def create(self, validated_data):
        avatar_id = validated_data.pop('selected_avatar_id', None)
        instance = super().create(validated_data)
        if avatar_id:
            instance.selected_avatar_id = avatar_id
            instance.save()
        return instance
    
    def update(self, instance, validated_data):
        avatar_id = validated_data.pop('selected_avatar_id', None)
        instance = super().update(instance, validated_data)
        if avatar_id:
            instance.selected_avatar_id = avatar_id
            instance.save()
        return instance


class EditTeacherProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, min_length=3, max_length=150)
    # Allow explicit null to remove files
    introduction_video = serializers.FileField(required=False, allow_null=True)
    profile_photo_path = serializers.ImageField(required=False, allow_null=True)
    
    # Support alternative field names for compatibility
    educational_qualifications = serializers.CharField(required=False, write_only=True, allow_blank=True)
    years_of_experience = serializers.IntegerField(required=False, write_only=True)
    
    # Support Jalali date format with slash
    birth_date = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=10,
        help_text=_("Birth date in Jalali format (YYYY-MM-DD or YYYY/MM/DD)")
    )
    
    # Support short gender codes
    gender = serializers.CharField(required=False, allow_blank=True, max_length=20)
    
    class Meta:
        model = User
        fields = [
            'username', 'name', 'email', 'phone', 'bio', 'profile_photo_path',
            'gender', 'birth_date',
            'qualifications', 'languages_taught', 'specialization', 
            'resume_summary', 'introduction_video', 'hourly_rate', 'experience_years',
            'is_teacher_verified',
            'educational_qualifications', 'years_of_experience'
        ]
        read_only_fields = ['is_teacher_verified']
        extra_kwargs = {
            'profile_photo_path': {'required': False, 'allow_null': True},
            'introduction_video': {'required': False, 'allow_null': True},
            'email': {'required': False},
            'phone': {'required': False},
            'bio': {'required': False},
            'gender': {'required': False},
            'birth_date': {'required': False},
            'qualifications': {'required': False},
            'languages_taught': {'required': False},
            'specialization': {'required': False},
            'resume_summary': {'required': False},
            'hourly_rate': {'required': False},
            'experience_years': {'required': False},
            'educational_qualifications': {'required': False},
            'years_of_experience': {'required': False},
        }
    
    def validate_birth_date(self, value):
        """Validate birth date format - accept both YYYY-MM-DD and YYYY/MM/DD"""
        if not value:
            return value
        
        import re
        # Convert slash to dash for consistency
        if '/' in value:
            value = value.replace('/', '-')
        
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
            raise serializers.ValidationError(
                _("Birth date must be in YYYY-MM-DD or YYYY/MM/DD format (Jalali calendar)")
            )
        return value
    
    def validate_gender(self, value):
        """Normalize gender codes - accept 'm'/'f' and convert to full names"""
        if not value:
            return value
        
        value_lower = value.lower()
        # Map short codes to full gender values
        gender_map = {
            'm': 'male',
            'f': 'female',
            'male': 'male',
            'female': 'female',
            'custom': 'custom',
            'prefer_not_to_say': 'prefer_not_to_say',
        }
        
        if value_lower not in gender_map:
            raise serializers.ValidationError(
                _("Gender must be: m, f, male, female, custom, or prefer_not_to_say")
            )
        
        return gender_map[value_lower]
    
    def validate_username(self, value):
        """Validate username format and uniqueness"""
        if not value:
            return value
        
        value = value.strip()
        
        # Validate format: only letters, numbers, and underscores
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(_("Username can only contain letters, numbers, and underscores."))
        
        # Check minimum length
        if len(value) < 3:
            raise serializers.ValidationError(_("Username must be at least 3 characters long."))
        
        # Check if username is taken by another user
        if self.instance and value != self.instance.username:
            if User.objects.filter(username=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(_("This username is already taken. Please choose another one."))
        
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if not value:
            return value
        
        if self.instance and value != self.instance.email:
            if User.objects.filter(email=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(_("This email is already registered."))
        
        return value
    
    def validate_phone(self, value):
        """Validate phone uniqueness"""
        if not value:
            return value
        
        if self.instance and value != self.instance.phone:
            if User.objects.filter(phone=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(_("This phone number is already registered."))
        
        return value
    
    def validate(self, attrs):
        if self.instance and self.instance.role != 'teacher':
            raise serializers.ValidationError({'non_field_errors': [_('User is not a teacher')]})
        
        # Map alternative field names
        if 'educational_qualifications' in attrs:
            attrs['qualifications'] = attrs.pop('educational_qualifications')
        
        if 'years_of_experience' in attrs:
            attrs['experience_years'] = attrs.pop('years_of_experience')
        
        return attrs


class CompleteTeacherProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for completing teacher profile with professional information.
    Teachers can set: name, qualifications, languages, introduction video, 
    resume summary, hourly rate, and available times.
    """
    profile_photo_path = serializers.ImageField(required=False, allow_null=True, help_text=_("Teacher profile photo"))
    qualifications = serializers.CharField(required=False, allow_blank=True, help_text=_("Educational qualifications and certifications"))
    languages_taught = serializers.CharField(required=False, allow_blank=True, help_text=_("Languages that can be taught"))
    specialization = serializers.CharField(required=False, allow_blank=True, help_text=_("Area of specialization"))
    resume_summary = serializers.CharField(required=False, allow_blank=True, help_text=_("Brief professional summary"))
    introduction_video = serializers.FileField(required=False, allow_null=True, help_text=_("Introduction video file"))
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True, help_text=_("Hourly teaching rate"))
    available_times = serializers.JSONField(required=False, allow_null=True, help_text=_("Available teaching times (JSON format)"))
    experience_years = serializers.IntegerField(required=False, allow_null=True, help_text=_("Years of teaching experience"))
    
    class Meta:
        model = User
        fields = [
            'name',
            'qualifications',
            'languages_taught',
            'specialization',
            'resume_summary',
            'introduction_video',
            'hourly_rate',
            'available_times',
            'experience_years',
            'profile_photo_path'
        ]
        extra_kwargs = {
            'name': {'required': False, 'help_text': _("Teacher full name")},
        }
    
    def validate_hourly_rate(self, value):
        """Validate hourly rate is positive"""
        if value is not None and value <= 0:
            raise serializers.ValidationError(_("Hourly rate must be greater than zero"))
        return value
    
    def validate_experience_years(self, value):
        """Validate experience years is non-negative"""
        if value is not None and value < 0:
            raise serializers.ValidationError(_("Experience years cannot be negative"))
        return value
    
    def validate(self, attrs):
        if self.instance and self.instance.role != 'teacher':
            raise serializers.ValidationError({'non_field_errors': [_('User is not a teacher')]})
        return attrs
    

class PromoteToTeacherSerializer(serializers.Serializer):
    bio = serializers.CharField(required=False)


# Admin
class UserListSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    class Meta:
        model = User
        fields = ['id','username','email','phone','role','role_display','is_teacher_verified','is_active','date_joined']
        read_only_fields = fields


# ========== Avatar Templates ==========
class AvatarTemplateSerializer(serializers.ModelSerializer):
    """Serializer for avatar templates"""
    class Meta:
        model = AvatarTemplate
        fields = ['id', 'image']


class SelectAvatarSerializer(serializers.Serializer):
    """Serializer for selecting an avatar as profile photo"""
    avatar_template_id = serializers.IntegerField(required=True)
    
    def validate_avatar_template_id(self, value):
        """Validate that avatar exists"""
        try:
            AvatarTemplate.objects.get(id=value)
            return value
        except AvatarTemplate.DoesNotExist:
            raise serializers.ValidationError(_("Selected avatar does not exist"))
