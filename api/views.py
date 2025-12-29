"""
API Views for mobile application - Unified User Model
Based on alolebas pattern with JWT authentication
Supports role-based access: user, teacher, admin
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, parsers, serializers
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, inline_serializer
from drf_spectacular.openapi import OpenApiResponse
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db import models
from django.http import StreamingHttpResponse, HttpResponse
import boto3
import re
from account.serializers import *
from account.services import *
from account.models import OTP, VerificationToken

# Import email function with fallback
try:
    from account.utils import send_email_otp
except ImportError:
    send_email_otp = None
from core.models import Article, FAQ, About, Term, Privacy, Contact, Banner
from core.serializers import (
    ArticleListSerializer, ArticleDetailSerializer, FAQSerializer,
    AboutSerializer, TermSerializer, PrivacySerializer, ContactSerializer,
    BannerSerializer
)

User = get_user_model()


def get_tokens_for_user(user):
    """Generate JWT tokens for user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }



# ========== OTP Authentication APIs ==========

class SendOTPAPIView(APIView):
    """
    Send OTP (One-Time Password) API
    
    Send OTP to user's phone or email for authentication.
    Supports both login and registration purposes.
    
    post:
        Send OTP to specified phone number or email.
        
        Request body parameters:
        - identifier: string (required) - Phone number (09xx format) or email address
        - purpose: string (optional) - Purpose of OTP: 'login' or 'registration'. Default: 'login'
        
        Returns:
            200 OK:
                - success: boolean (true)
                - message: string - "Verification code sent."
                
            400 Bad Request:
                - Phone number already registered (for registration)
                - OTP cooldown (must wait 2 minutes between requests)
                - Invalid identifier format
                
            429 Too Many Requests - Rate limit exceeded, try again later
            503 Service Unavailable - Email service not configured
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Authentication - OTP'],
        summary='Send OTP Code',
        description='Send One-Time Password to phone number or email for authentication',
        request=SendOTPSerializer,
        responses={
            200: OpenApiResponse(description="Verification code sent successfully"),
            400: OpenApiResponse(description="Invalid data or phone already registered"),
            429: OpenApiResponse(description="Rate limit exceeded"),
            503: OpenApiResponse(description="Email service not configured"),
        }
    )
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['identifier']
            purpose = serializer.validated_data.get('purpose', 'login')
            
            # For registration, check if user already exists
            if purpose == 'registration':
                # Normalize phone if needed
                import phonenumbers
                check_identifier = identifier
                if identifier.startswith('09'):
                    try:
                        phone_obj = phonenumbers.parse(identifier, "IR")
                        check_identifier = phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)
                    except:
                        pass
                
                # Check if FULLY registered user exists (has username)
                existing_user = User.objects.filter(phone=check_identifier).first() or User.objects.filter(phone=identifier).first()
                if existing_user and existing_user.username and not existing_user.username.startswith('user_'):
                    return Response({
                        "success": False,
                        "message": _("This phone number is already registered. Please log in.")
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if '@' in identifier:
                    existing_user = User.objects.filter(email=identifier).first()
                    if existing_user and existing_user.username and not existing_user.username.startswith('user_'):
                        return Response({
                            "success": False,
                            "message": _("This email is already registered. Please log in.")
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check for unused verification tokens (incomplete registration)
                # Delete expired tokens
                VerificationToken.objects.filter(
                    expires_at__lt=timezone.now()
                ).delete()
                
                # Check if there's a valid unused token for this phone/email
                unused_token = VerificationToken.objects.filter(
                    phone=check_identifier if not '@' in identifier else None,
                    email=identifier if '@' in identifier else None,
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).first()
                
                if unused_token:
                    # User started registration but didn't complete it
                    # Allow them to continue - they can request new OTP
                    pass
            
            # Check if can send OTP (cooldown check)
            recent_otp = OTP.objects.filter(
                phone=identifier if '@' not in str(identifier) else None,
                email=identifier if '@' in str(identifier) else None,
                is_used=False
            ).order_by('-created_at').first()
            
            if recent_otp and (timezone.now() - recent_otp.created_at).seconds < 120:
                return Response({
                    "success": False,
                    "message": _("Please wait 2 minutes.")
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Generate and send OTP
            try:
                if '@' in str(identifier):
                    # Email OTP - check if send_email_otp is available
                    if not send_email_otp:
                        return Response({
                            "success": False,
                            "message": _("Email authentication is not configured on this server")
                        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                    # Generate and send email OTP
                    generate_and_send_otp(identifier, purpose=purpose)
                else:
                    # Phone OTP - using utils.py send_sms
                    generate_and_send_otp(identifier, purpose=purpose)
                    
                return Response({
                    "success": True,
                    "message": _("Verification code sent.")
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "success": False,
                    "message": _(f"Error sending code: {str(e)}")
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Format errors for better readability
        error_messages = []
        for field, errors in serializer.errors.items():
            if field == 'non_field_errors':
                error_messages.extend([str(e) for e in errors])
            else:
                for error in errors:
                    error_messages.append(f"{field}: {error}")
        
        return Response({
            "success": False,
            "message": " | ".join(error_messages) if error_messages else _("Invalid data provided"),
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPAPIView(APIView):
    """
    Verify OTP API
    
    Verify one-time password for login or registration.
    Returns JWT tokens for login or verification token for registration.
    
    post:
        Verify OTP code sent to phone/email.
        
        Request parameters:
        - identifier: Phone number or email (required)
        - code: OTP code received (required)
        - purpose: 'login' or 'registration' (optional, default: 'login')
        
        Returns:
            For login: user profile + JWT tokens
            For registration: verification token
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Authentication - OTP'],
        summary='Verify OTP Code',
        description='Verify One-Time Password code for login or registration. Returns JWT tokens for login or verification token for registration.',
        responses={
            200: OpenApiResponse(description="OTP verified successfully, returns tokens or verification token"),
            400: OpenApiResponse(description="Invalid or expired OTP"),
            401: OpenApiResponse(description="Unauthorized - Invalid credentials"),
        }
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['identifier']
            code = serializer.validated_data['code']
            purpose = serializer.validated_data.get('purpose', 'login')
            
            ok, result = validate_otp(identifier, code, purpose=purpose)
            
            if ok:
                # If registration, return verification token
                if purpose == 'registration' and isinstance(result, dict):
                    return Response({
                        "success": True,
                        "message": _("Verification code is correct. Please complete registration"),
                        "data": {
                            "verification_token": result['verification_token'],
                            "phone": result.get('phone'),
                            "email": result.get('email')
                        }
                    }, status=status.HTTP_200_OK)
                
                # For login, return user and tokens
                user = result
                tokens = get_tokens_for_user(user)
                user_data = UserProfileSerializer(user).data
                
                return Response({
                    "success": True,
                    "message": _("Login successful"),
                    "user": user_data,
                    "tokens": tokens
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "success": False,
                    "message": result
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Format errors for better readability
        error_messages = []
        for field, errors in serializer.errors.items():
            if field == 'non_field_errors':
                error_messages.extend([str(e) for e in errors])
            else:
                for error in errors:
                    error_messages.append(f"{field}: {error}")
        
        return Response({
            "success": False,
            "message": " | ".join(error_messages) if error_messages else _("Invalid data"),
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CompleteRegistrationAPIView(APIView):
    """
    Complete User Registration API
    
    Finalize user registration by setting username and password.
    Must be called after OTP verification (verify-otp endpoint).
    
    post:
        Complete user registration process.
        
        Request body parameters:
        - verification_token: string (required) - Token returned from verify-otp endpoint
        - username: string (required, 3-150 chars) - Unique username for login
        - password: string (required, min 8 chars) - Account password
        - name: string (required) - User's full name
        - expo_push_token: string (optional) - Push notification token for mobile app
        
        Returns:
            201 Created:
                - success: boolean (true)
                - message: string - "Registration completed successfully"
                - user: object - User profile with id, username, name, phone, email, role
                - tokens: object - JWT tokens {access, refresh}
                
            400 Bad Request:
                - Invalid or expired verification token
                - Username already exists
                - Password too weak
                - Missing required fields
                
            401 Unauthorized - Invalid token
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Authentication - Registration'],
        summary='Complete User Registration',
        description='Finalize user registration by setting username and password after OTP verification.',
        request=CompleteRegistrationSerializer,
        responses={
            201: OpenApiResponse(description="Registration completed successfully"),
            400: OpenApiResponse(description="Invalid or expired token, username exists, or weak password"),
            401: OpenApiResponse(description="Invalid token"),
        }
    )
    def post(self, request):
        serializer = CompleteRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            verification_token = serializer.validated_data['verification_token']
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            name = serializer.validated_data['name']
            
            # Get expo_push_token if provided
            expo_push_token = serializer.validated_data.get('expo_push_token', '')
            
            ok, result = complete_registration(
                verification_token=verification_token,
                name=name,
                username=username,
                password=password,
                expo_push_token=expo_push_token
            )
            
            if ok:
                user = result
                tokens = get_tokens_for_user(user)
                user_data = UserProfileSerializer(user).data
                
                return Response({
                    "success": True,
                    "message": _("Registration completed successfully"),
                    "user": user_data,
                    "tokens": tokens
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "success": False,
                    "message": result
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "success": False,
            "message": _("Invalid data"),
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ========== Teacher Authentication APIs ==========

class UserLoginPasswordAPIView(APIView):
    """
    User Login with Username/Password API
    
    Authenticate user using username and password credentials.
    Returns JWT tokens and user profile information.
    
    post:
        Login a user with username and password.
        
        Request body parameters:
        - username: string (required) - User's registered username
        - password: string (required) - User's account password
        
        Returns:
            200 OK:
                - success: boolean (true)
                - message: string - "Login successful"
                - user: object - User profile data
                - tokens: object - JWT tokens {access: string, refresh: string}
                
            400 Bad Request:
                - Invalid credentials
                - User account not found
                - Missing username or password
                
            401 Unauthorized - Invalid username/password combination
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Authentication - Login'],
        summary='User Login with Password',
        description='Authenticate user with username and password. Returns JWT tokens and user profile.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string', 'description': 'User registered username'},
                    'password': {'type': 'string', 'description': 'User account password'}
                },
                'required': ['username', 'password']
            }
        },
        responses={
            200: OpenApiResponse(description="Login successful, returns user profile and tokens"),
            400: OpenApiResponse(description="Invalid credentials or missing fields"),
            401: OpenApiResponse(description="Invalid username/password combination"),
        }
    )
    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '').strip()
        
        if not username or not password:
            return Response({
                "success": False,
                "message": _("Username and password are required")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Regular users (not teachers)
            
            tokens = get_tokens_for_user(user)
            user_data = UserProfileSerializer(user).data
            
            return Response({
                "success": True,
                "message": _("Login successful"),
                "user": user_data,
                "tokens": tokens
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": False,
                "message": _("Username or password is incorrect")
            }, status=status.HTTP_401_UNAUTHORIZED)


class TeacherLoginPasswordAPIView(APIView):
    """
    Teacher Login with Username/Password API
    
    Authenticate teacher using username and password credentials.
    Returns JWT tokens and teacher profile with specialization info.
    
    post:
        Login a teacher with username and password.
        
        Request parameters:
        - username: Teacher's username (required)
        - password: Teacher's password (required)
        
        Returns: JWT tokens + teacher profile with specialization
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Teacher Authentication - Login'],
        summary='Teacher Login with Password',
        description='Authenticate teacher with username and password. Returns JWT tokens and teacher profile.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string', 'description': 'Teacher registered username'},
                    'password': {'type': 'string', 'description': 'Teacher account password'}
                },
                'required': ['username', 'password']
            }
        },
        responses={
            200: OpenApiResponse(description="Login successful"),
            400: OpenApiResponse(description="Invalid credentials"),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Account is not for a teacher"),
        }
    )
    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '').strip()
        
        if not username or not password:
            return Response({
                "success": False,
                "message": _("Username and password are required")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Check if user is teacher
            if user.role != 'teacher':
                return Response({
                    "success": False,
                    "message": _("This account is not for a teacher")
                }, status=status.HTTP_403_FORBIDDEN)
            
            tokens = get_tokens_for_user(user)
            user_data = UserProfileSerializer(user).data
            
            return Response({
                "success": True,
                "message": _("Login successful"),
                "user": user_data,
                "tokens": tokens
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": False,
                "message": _("Username or password is incorrect")
            }, status=status.HTTP_401_UNAUTHORIZED)


class TeacherSendOTPAPIView(APIView):
    """
    Teacher Send OTP API
    
    Send OTP to teacher phone or email for authentication.
    
    post:
        Send OTP to teacher's phone or email.
        
        Request parameters:
        - identifier: Phone or email (required)
        - purpose: 'login' or 'registration' (optional)
        
        Returns: Confirmation of OTP sent
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Teacher Authentication - OTP'],
        summary='Send OTP to Teacher',
        description='Send One-Time Password to teacher phone or email for authentication',
        request=SendOTPSerializer,
        responses={
            200: OpenApiResponse(description="OTP sent successfully"),
            429: OpenApiResponse(description="Rate limit - wait 2 minutes"),
            500: OpenApiResponse(description="Server error"),
        }
    )
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['identifier']
            
            # Determine if it's email or phone
            is_email = '@' in str(identifier)
            
            # Check cooldown
            if is_email:
                recent_otp = OTP.objects.filter(
                    email=identifier,
                    purpose='login',
                    is_used=False
                ).order_by('-created_at').first()
            else:
                recent_otp = OTP.objects.filter(
                    phone=identifier,
                    purpose='login',
                    is_used=False
                ).order_by('-created_at').first()
            
            if recent_otp and (timezone.now() - recent_otp.created_at).seconds < 120:
                return Response({
                    "success": False,
                    "message": _("Please wait 2 minutes before requesting a new code.")
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Generate and send OTP with teacher template
            try:
                generate_and_send_otp(identifier, purpose='login', user=None, is_teacher=True)
                    
                return Response({
                    "success": True,
                    "message": _("Verification code sent successfully.") if is_email else _("Verification code sent.")
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "success": False,
                    "message": _(f"Error sending verification code: {str(e)}")
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "success": False,
            "message": _("Invalid data provided"),
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TeacherVerifyOTPAPIView(APIView):
    """
    Teacher Verify OTP API
    
    Verify OTP and login teacher or return verification token for registration.
    
    post:
        Verify OTP code for teacher.
        
        Request parameters:
        - identifier: Phone or email (required)
        - code: OTP code (required)
        - purpose: 'login' or 'registration' (optional)
        
        Returns: User tokens and profile or verification token
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Teacher Authentication - OTP'],
        summary='Verify Teacher OTP',
        description='Verify OTP code for teacher login or registration',
        responses={
            200: OpenApiResponse(description="OTP verified successfully"),
            400: OpenApiResponse(description="Invalid OTP"),
            403: OpenApiResponse(description="Account is not for teachers"),
        }
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['identifier']
            code = serializer.validated_data['code']
            
            ok, result = validate_otp(identifier, code, purpose='login')
            
            if ok:
                user = result
                
                # Check if user is teacher
                if user.role != 'teacher':
                    return Response({
                        "success": False,
                        "message": _("This account is not for teachers")
                    }, status=status.HTTP_403_FORBIDDEN)
                
                tokens = get_tokens_for_user(user)
                user_data = UserProfileSerializer(user).data
                
                return Response({
                    "success": True,
                    "message": _("Login successful"),
                    "user": user_data,
                    "tokens": tokens
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "success": False,
                    "message": result
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "success": False,
            "message": _("Invalid data provided"),
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TeacherCompleteRegistrationAPIView(APIView):
    """
    Complete Teacher Registration API (Duplicate)
    
    Finalize teacher registration by setting username and password.
    Must be called after OTP verification with teacher-specific fields.
    
    post:
        Complete teacher registration process.
        
        Request body:
        - verification_token: Token from OTP verification (required)
        - username: Desired username (required, unique)
        - password: Account password (required)
        - name: Teacher's full name (required)
        - specialization: Area of specialization (required)
        - experience_years: Years of teaching experience (required)
        
        Returns:
            - success: Boolean
            - user: Newly created teacher profile
            - tokens: {access, refresh} JWT tokens
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Teacher Authentication - Registration'],
        summary='Complete Teacher Registration',
        description='Finalize teacher registration after OTP verification with specialization details.',
        request=CompleteTeacherRegistrationSerializer,
        responses={
            201: OpenApiResponse(description="Teacher registration completed successfully"),
            400: OpenApiResponse(description="Invalid token or validation failed"),
        }
    )
    def post(self, request):
        serializer = CompleteTeacherRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            verification_token = serializer.validated_data['verification_token']
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            name = serializer.validated_data.get('name', '')
            bio = serializer.validated_data.get('bio', '')
            
            # Get expo_push_token if provided
            expo_push_token = serializer.validated_data.get('expo_push_token', '')
            
            ok, result = complete_teacher_registration(
                verification_token=verification_token,
                name=name,
                username=username,
                password=password,
                bio=bio,
                expo_push_token=expo_push_token
            )
            
            if ok:
                user = result
                tokens = get_tokens_for_user(user)
                user_data = UserProfileSerializer(user).data
                
                return Response({
                    "success": True,
                    "message": _("Teacher registration completed successfully"),
                    "user": user_data,
                    "tokens": tokens
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "success": False,
                    "message": result
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "success": False,
            "message": _("Invalid data"),
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ========== Email-Based Authentication APIs ==========

class UserSendEmailOTPAPIView(APIView):
    """
    Send Email OTP for User API
    
    Send OTP to user's email for authentication.
    Used in email-based login and registration.
    
    post:
        Send OTP to specified email address for user login.
        
        Request parameters:
        - email: Email address (required)
        - purpose: 'login' or 'registration' (optional)
        
        Returns: Email confirmation + OTP status
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Authentication - Email OTP'],
        summary='Send Email OTP to User',
        description='Send One-Time Password to user email for authentication',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string', 'format': 'email', 'description': 'User email address'},
                    'purpose': {'type': 'string', 'enum': ['login', 'registration'], 'description': 'Purpose of OTP'}
                },
                'required': ['email']
            }
        },
        responses={
            200: OpenApiResponse(description="OTP sent successfully"),
            400: OpenApiResponse(description="Invalid email"),
            429: OpenApiResponse(description="Rate limit"),
        }
    )
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        
        if not email or '@' not in email:
            return Response({
                "success": False,
                "message": _("Please provide a valid email address")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check cooldown
        ok, msg = can_send_otp(email, purpose='login')
        if not ok:
            return Response({
                "success": False,
                "message": _(msg)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Check if email belongs to teacher
        existing_user = User.objects.filter(email=email).first()
        if existing_user and existing_user.role == 'teacher':
            return Response({
                "success": False,
                "message": _("This email is registered as a teacher account. Please use teacher login.")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not send_email_otp:
            return Response({
                "success": False,
                "message": _("Email authentication is not configured on this server")
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            generate_and_send_otp(email, purpose='login', user=None, is_teacher=False)
            return Response({
                "success": True,
                "message": _("Verification code has been sent to your email"),
                "email": email
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": _(f"Error sending OTP: {str(e)}")
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserVerifyEmailOTPAPIView(APIView):
    """
    Verify Email OTP for User API
    
    Verify OTP sent to user's email for login.
    Marks email as verified and returns authentication tokens.
    
    post:
        Verify OTP code sent to user email.
        
        Request parameters:
        - email: Email address (required)
        - code: 6-digit OTP code (required)
        
        Returns: JWT tokens + user profile data
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        code = request.data.get('code', '').strip()
        
        if not email or not code:
            return Response({
                "success": False,
                "message": _("Email and verification code are required")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(code) != 6 or not code.isdigit():
            return Response({
                "success": False,
                "message": _("Invalid verification code format")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ok, result = validate_otp(email, code, purpose='login')
        
        if ok:
            user = result
            
            # Check if user is trying to login as regular user but is teacher
            if user.role == 'teacher':
                return Response({
                    "success": False,
                    "message": _("This email is registered as a teacher account. Please use teacher login.")
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Mark email as verified
            if not user.email_verified_at:
                user.email_verified_at = timezone.now()
                user.save()
            
            tokens = get_tokens_for_user(user)
            user_data = UserProfileSerializer(user).data
            
            return Response({
                "success": True,
                "message": _("Login successful"),
                "user": user_data,
                "tokens": tokens
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": False,
                "message": result
            }, status=status.HTTP_400_BAD_REQUEST)


class TeacherSendEmailOTPAPIView(APIView):
    """
    Send OTP to Email for Teacher API
    
    Send OTP to teacher's email for authentication.
    Used in email-based teacher login and registration.
    
    post:
        Send OTP to specified email address for teacher login.
        
        Request body:
        - email: Email address (required)
        - purpose: 'login' or 'registration' (optional, default: 'login')
        
        Returns:
            - success: Boolean
            - message: Status message
            - email: Confirmed email address
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        
        if not email or '@' not in email:
            return Response({
                "success": False,
                "message": _("Please provide a valid email address")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check cooldown
        ok, msg = can_send_otp(email, purpose='login')
        if not ok:
            return Response({
                "success": False,
                "message": _(msg)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Check if email belongs to regular user
        existing_user = User.objects.filter(email=email).first()
        if existing_user and existing_user.role != 'teacher':
            return Response({
                "success": False,
                "message": _("This email is registered as a regular user account. Please use regular user login.")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not send_email_otp:
            return Response({
                "success": False,
                "message": _("Email authentication is not configured on this server")
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            generate_and_send_otp(email, purpose='login', user=None, is_teacher=True)
            return Response({
                "success": True,
                "message": _("Verification code has been sent to your email"),
                "email": email
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": _(f"Error sending OTP: {str(e)}")
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherVerifyEmailOTPAPIView(APIView):
    """
    Verify Email OTP for Teacher API
    
    Verify OTP sent to teacher's email for login.
    Marks email as verified and returns authentication tokens.
    
    post:
        Verify OTP code sent to teacher email.
        
        Request body:
        - email: Email address (required)
        - code: 6-digit OTP code (required)
        
        Returns:
            - success: Boolean
            - user: Teacher profile data with specialization and experience
            - tokens: {access, refresh} JWT tokens
            - message: Status message
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        code = request.data.get('code', '').strip()
        
        if not email or not code:
            return Response({
                "success": False,
                "message": _("Email and verification code are required")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(code) != 6 or not code.isdigit():
            return Response({
                "success": False,
                "message": _("Invalid verification code format")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ok, result = validate_otp(email, code, purpose='login')
        
        if ok:
            user = result
            
            # Check if user is actually a teacher
            if user.role != 'teacher':
                return Response({
                    "success": False,
                    "message": _("This email is registered as a regular user account. Please use regular user login.")
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Mark email as verified
            if not user.email_verified_at:
                user.email_verified_at = timezone.now()
                user.save()
            
            tokens = get_tokens_for_user(user)
            user_data = UserProfileSerializer(user).data
            
            return Response({
                "success": True,
                "message": _("Login successful"),
                "user": user_data,
                "tokens": tokens
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": False,
                "message": result
            }, status=status.HTTP_400_BAD_REQUEST)


class CheckUsernameAPIView(APIView):
    """
    Check Username Availability API
    
    Verify if a username is available for registration.
    Accepts both GET and POST requests.
    
    get:
        Check if username is available (query parameter).
        
        Query parameters:
        - username: string (required, min 3 characters) - Username to check
        
        Returns:
            200 OK:
                - success: boolean
                - available: boolean (true if available)
                - message: string - "This username is available." or "This username has already been taken."
                
            400 Bad Request:
                - Username is empty
                - Username less than 3 characters
    
    post:
        Check if username is available (body parameter).
        
        Request body parameters:
        - username: string (required, min 3 characters) - Username to check
        
        Returns:
            200 OK:
                - success: boolean
                - available: boolean (true if available)
                - message: string - "This username is available." or "This username has already been taken."
                
            400 Bad Request:
                - Username is empty
                - Username less than 3 characters
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Utilities'],
        summary='Check Username Availability',
        description='Verify if a username is available for registration',
        parameters=[
            OpenApiParameter(
                name='username',
                description='Username to check (minimum 3 characters)',
                required=True,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY
            )
        ],
        responses={
            200: OpenApiResponse(description="Username availability check result"),
            400: OpenApiResponse(description="Invalid username format"),
        }
    )
    def get(self, request):
        """GET method - username in query params"""
        username = request.GET.get('username', '').strip()
        
        if not username:
            return Response({
                "success": False,
                "message": _("Username is required")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(username) < 3:
            return Response({
                "success": False,
                "message": _("Username must be at least 3 characters")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if username exists
        exists = User.objects.filter(username=username).exists()
        
        if exists:
            return Response({
                "success": False,
                "available": False,
                "message": _("This username has already been taken.")
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": True,
                "available": True,
                "message": _("This username is available.")
            }, status=status.HTTP_200_OK)
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string', 'description': 'Username to check (minimum 3 characters)'}
                },
                'required': ['username']
            }
        },
        responses={
            200: OpenApiResponse(description="Username availability check result"),
            400: OpenApiResponse(description="Invalid username format"),
        }
    )
    def post(self, request):
        """POST method - username in body or query params"""
        # Try to get from query params first (for flexibility)
        username = request.GET.get('username', '').strip()
        
        # If not in query params, try body
        if not username:
            serializer = CheckUsernameSerializer(data=request.data)
            if serializer.is_valid():
                username = serializer.validated_data['username']
            else:
                return Response({
                    "success": False,
                    "message": _("Username is invalid"),
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate minimum length
        if len(username) < 3:
            return Response({
                "success": False,
                "message": _("Username must be at least 3 characters")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if username exists
        exists = User.objects.filter(username=username).exists()
        
        if exists:
            return Response({
                "success": False,
                "available": False,
                "message": _("This username has already been taken.")
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "success": True,
                "available": True,
                "message": _("This username is available.")
            }, status=status.HTTP_200_OK)


# ========== Profile Management APIs ==========

class FetchUserAPIView(APIView):
    """
    Fetch Current User Data API
    
    Retrieve current authenticated user's complete profile information.
    Requires valid JWT authentication token.
    
    get:
        Get current user information based on authentication token.
        
        Returns:
            200 OK:
                - success: boolean (true)
                - user: object containing:
                    - id: integer
                    - username: string
                    - email: string
                    - phone: string
                    - first_name: string
                    - last_name: string
                    - bio: string
                    - role: string (user or teacher)
                    - avatar: string (URL)
                    
            401 Unauthorized - Invalid or missing authentication token
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Profile Management'],
        summary='Fetch Current User Profile',
        description='Get authenticated user profile information',
        responses={
            200: OpenApiResponse(description="User profile retrieved successfully"),
            401: OpenApiResponse(description="User not authenticated"),
        }
    )
    def get(self, request):
        """Get current user information"""
        serializer = UserProfileSerializer(request.user)
        return Response({
            "success": True,
            "user": serializer.data
        }, status=status.HTTP_200_OK)


class UserProfileAPIView(APIView):
    """
    User Profile Management API
    
    Manage user and teacher profile information including personal details,
    avatar, and role-specific settings. Requires authentication.
    
    post:
        Update the current user's profile information.
        Supports both regular users and teachers with role-specific fields.
        
        Request body parameters for regular users:
            - first_name: string (optional) - User's first name
            - last_name: string (optional) - User's last name  
            - email: string (optional, unique) - Email address
            - phone: string (optional, unique) - Phone number
            - bio: string (optional) - User biography
            - avatar_url: string (optional) - Avatar URL
            
        Request body parameters for teachers:
            - first_name: string (optional) - Teacher's first name
            - last_name: string (optional) - Teacher's last name
            - email: string (optional, unique) - Email address
            - phone: string (optional, unique) - Phone number
            - bio: string (optional) - Biography
            - specialization: string (optional) - Area of specialization (e.g., "Mathematics", "English")
            - experience_years: integer (optional) - Years of teaching experience
            - qualifications: string (optional) - Professional qualifications and certifications
        
        Returns:
            200 OK:
                - success: boolean (true)
                - message: string - "Profile updated successfully" or "Teacher profile updated successfully"
                - user or teacher: object - Updated profile data
                
            400 Bad Request:
                - Invalid data provided
                - Email already in use
                - Phone already in use
                
            401 Unauthorized - User not authenticated
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    @extend_schema(
        tags=['Profile Management'],
        summary='Update User/Teacher Profile',
        description='Update user or teacher profile information based on role',
        request=EditUserProfileSerializer,
        responses={
            200: OpenApiResponse(description="Profile updated successfully"),
            400: OpenApiResponse(description="Invalid data or duplicate email/phone"),
            401: OpenApiResponse(description="User not authenticated"),
        }
    )
    def post(self, request):
        """Update user profile via POST"""
        # Use appropriate serializer based on role
        if request.user.role == 'teacher':
            serializer = EditTeacherProfileSerializer(request.user, data=request.data, partial=True)
            key = 'teacher'
            message = _("Teacher profile updated successfully")
        else:
            serializer = EditUserProfileSerializer(request.user, data=request.data, partial=True)
            key = 'user'
            message = _("Profile updated successfully")
            
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": message,
                key: serializer.__class__(request.user).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            "success": False,
            "message": _("Invalid data provided"),
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ========== Complete Profile APIs ==========

class CompleteStudentProfileAPIView(APIView):
    """
    Complete Student Profile API
    
    Allow students to complete their profile with basic information.
    Students can set their name, birth date, gender, and select an avatar.
    Requires authentication.
    
    post:
        Complete student profile information.
        
        Request body parameters:
            - name: string (optional) - Student's full name
            - birth_date: string (optional) - Birth date in YYYY-MM-DD format
            - gender: string (optional) - Gender: 'male', 'female', 'custom', 'prefer_not_to_say'
            - selected_avatar_id: integer (optional) - ID of avatar template to select
        
        Returns:
            200 OK:
                - success: boolean (true)
                - message: string - "Profile completed successfully"
                - user: object - Updated student profile data
                
            400 Bad Request:
                - Invalid data provided
                - Invalid avatar ID
                - Invalid date format
                
            401 Unauthorized - User not authenticated
            403 Forbidden - User is not a student
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    @extend_schema(
        request=CompleteStudentProfileSerializer,
        responses={
            200: OpenApiResponse(description="Student profile completed successfully"),
            400: OpenApiResponse(description="Invalid data or invalid avatar"),
            401: OpenApiResponse(description="User not authenticated"),
            403: OpenApiResponse(description="User is not a student"),
        }
    )
    def post(self, request):
        # Check if user is a student (regular user)
        if request.user.role != 'user':
            return Response({
                "success": False,
                "message": _("Only students can use this endpoint")
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CompleteStudentProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": _("Profile completed successfully"),
                "user": UserProfileSerializer(request.user).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            "success": False,
            "message": _("Invalid data provided"),
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CompleteTeacherProfileAPIView(APIView):
    """
    Complete Teacher Profile API
    
    Allow teachers to complete their professional profile with detailed information.
    Teachers can set: name, qualifications, languages taught, introduction video,
    resume summary, hourly rate, and available teaching times.
    Requires authentication and teacher role.
    
    post:
        Complete teacher profile with professional information.
        
        **Request body (form-data or JSON):**
        
        - **name** (string, optional): Teacher's full name
        - **qualifications** (string, optional): Educational qualifications and certifications
        - **languages_taught** (string, optional): Languages that can be taught (comma-separated)
        - **specialization** (string, optional): Area of specialization/expertise
        - **resume_summary** (string, optional): Brief professional background summary
        - **introduction_video** (string/URL, optional): YouTube/video URL for introduction
        - **hourly_rate** (decimal, optional): Suggested hourly teaching rate (e.g., 15.50)
        - **available_times** (JSON, optional): JSON object with available teaching times
        - **experience_years** (integer, optional): Years of teaching experience
        - **profile_photo_path** (file, optional): Teacher profile photo/picture (image file)
        
        **Returns:**
        
        - **200 OK**: Profile updated successfully
            - success: boolean (true)
            - message: string - "Teacher profile completed successfully"
            - user: object - Updated teacher profile data with all fields
                
        - **400 Bad Request**: Validation error
            - Invalid data provided
            - Invalid hourly rate (must be positive)
            - Invalid experience years (cannot be negative)
            - Invalid video URL
            - File too large or invalid format
                
        - **401 Unauthorized**: User not authenticated
            - message: "Not authenticated"
            
        - **403 Forbidden**: User is not a teacher
            - message: "Only teachers can use this endpoint"
    
    **Example Request (JSON):**
    ```json
    {
        "name": "Dr. Sarah Johnson",
        "qualifications": "PhD in Linguistics, TEFL Certified",
        "languages_taught": "English, Spanish, French",
        "specialization": "Business English, Test Preparation",
        "resume_summary": "10+ years teaching experience in international schools",
        "introduction_video": "https://youtube.com/watch?v=abc123",
        "hourly_rate": 25.50,
        "experience_years": 12,
        "available_times": {
            "monday": ["09:00-12:00", "14:00-17:00"],
            "wednesday": ["10:00-13:00"],
            "friday": ["15:00-19:00"]
        }
    }
    ```
    
    **Example Request (form-data):**
    ```
    name: Dr. Sarah Johnson
    qualifications: PhD in Linguistics, TEFL Certified
    languages_taught: English, Spanish, French
    specialization: Business English
    resume_summary: 10+ years experience
    introduction_video: https://youtube.com/watch?v=abc123
    hourly_rate: 25.50
    experience_years: 12
    available_times: {...}
    profile_photo_path: <file>
    ```
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    @extend_schema(
        request=CompleteTeacherProfileSerializer,
        responses={
            200: OpenApiResponse(description="Teacher profile completed successfully"),
            400: OpenApiResponse(description="Invalid data or validation error"),
            401: OpenApiResponse(description="User not authenticated"),
            403: OpenApiResponse(description="User is not a teacher"),
        }
    )
    def post(self, request):
        # Check if user is a teacher
        if request.user.role != 'teacher':
            return Response({
                "success": False,
                "message": _("Only teachers can use this endpoint")
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CompleteTeacherProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": _("Teacher profile completed successfully"),
                "user": UserProfileSerializer(request.user).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            "success": False,
            "message": _("Invalid data provided"),
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ========== Avatar Templates APIs ==========

class AvatarTemplateListAPIView(generics.ListAPIView):
    """API: List all available avatar templates for selection"""
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Get all avatar templates"""
        from account.models import AvatarTemplate
        return AvatarTemplate.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        from account.serializers import AvatarTemplateSerializer
        return AvatarTemplateSerializer


class SelectAvatarAPIView(APIView):
    """
    Select Avatar Template API
    
    Select and set an avatar template as the user's profile photo.
    Requires authentication.
    
    post:
        Set an avatar as the user's profile picture.
        
        Request body parameters:
            - avatar_template_id: integer (required) - ID of avatar template to select (from /api/avatars/)
        
        Returns:
            200 OK:
                - success: boolean (true)
                - message: string - "Avatar selected successfully"
                - user: object - Updated user profile with selected_avatar field
                
            400 Bad Request:
                - Invalid data provided
                - avatar_template_id is not an integer
                - Missing avatar_template_id
                
            401 Unauthorized - User not authenticated
            404 Not Found - Avatar template with given ID does not exist
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'avatar_template_id': {'type': 'integer', 'description': 'ID of avatar template'}
                },
                'required': ['avatar_template_id']
            }
        },
        responses={
            200: OpenApiResponse(description="Avatar selected successfully"),
            400: OpenApiResponse(description="Invalid data or missing avatar_template_id"),
            401: OpenApiResponse(description="User not authenticated"),
            404: OpenApiResponse(description="Avatar template not found"),
        }
    )
    def post(self, request):
        """Select an avatar as profile photo"""
        from account.models import AvatarTemplate
        from account.serializers import SelectAvatarSerializer
        
        serializer = SelectAvatarSerializer(data=request.data)
        if serializer.is_valid():
            avatar_id = serializer.validated_data['avatar_template_id']
            
            try:
                avatar = AvatarTemplate.objects.get(id=avatar_id)
                
                # Set the selected avatar for user
                request.user.selected_avatar = avatar
                request.user.save()
                
                return Response({
                    "success": True,
                    "message": _("Avatar selected successfully"),
                    "user": UserProfileSerializer(request.user).data
                }, status=status.HTTP_200_OK)
                
            except AvatarTemplate.DoesNotExist:
                return Response({
                    "success": False,
                    "message": _("Selected avatar does not exist")
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "success": False,
            "message": _("Invalid data provided"),
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)





class PromoteToTeacherAPIView(APIView):
    """
    Promote to Teacher Role API
    
    Upgrade a regular user account to teacher role.
    User must provide professional qualifications and experience details.
    Requires authentication.
    
    post:
        Promote authenticated user to teacher role.
        
        Request body parameters:
            - specialization: string (required) - Area of expertise (e.g., "Mathematics", "English", "Computer Science")
            - experience_years: integer (required) - Years of teaching experience (minimum 0)
            - qualifications: string (required) - Professional qualifications and certifications (min 10 characters)
        
        Returns:
            200 OK:
                - success: boolean (true)
                - message: string - "Promoted to teacher successfully"
                - user: object - Updated user profile with role="teacher"
                
            400 Bad Request:
                - User is already a teacher
                - Invalid or missing required fields
                - Insufficient qualifications length
                
            401 Unauthorized - User not authenticated
            403 Forbidden - User already has teacher role
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=PromoteToTeacherSerializer,
        responses={
            200: OpenApiResponse(description="Promoted to teacher successfully"),
            400: OpenApiResponse(description="Invalid data, already a teacher, or insufficient qualifications"),
            401: OpenApiResponse(description="User not authenticated"),
            403: OpenApiResponse(description="User already has teacher role"),
        }
    )
    def post(self, request):
        if request.user.role == 'teacher':
            return Response({
                "success": False,
                "message": _("You are already a teacher")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PromoteToTeacherSerializer(data=request.data)
        if serializer.is_valid():
            try:
                ok, message = promote_to_teacher(request.user)
                if ok:
                    return Response({
                        "success": True,
                        "message": message,
                        "user": UserProfileSerializer(request.user).data
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "success": False,
                        "message": message
                    }, status=status.HTTP_400_BAD_REQUEST)
            except ValidationError as e:
                return Response({
                    "success": False,
                    "message": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "success": False,
            "message": _("Invalid data provided"),
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ========== Password & Settings APIs ==========

class ChangePasswordAPIView(APIView):
    """
    Change User Password API
    
    Allow authenticated users to change their account password.
    Requires old password verification for security.
    Requires authentication.
    
    post:
        Change the authenticated user's password.
        
        Request body parameters:
        - old_password: string (required) - Current password for verification
        - new_password: string (required, min 8 chars) - New password
        - confirm_password: string (required) - Confirmation of new password (must match new_password)
        
        Returns:
            200 OK:
                - success: boolean (true)
                - message: string - "Password changed successfully"
                
            400 Bad Request:
                - Old password is incorrect
                - New password and confirm password do not match
                - Password too weak (less than 8 characters)
                - Missing required fields
                
            401 Unauthorized - User not authenticated
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Account Settings'],
        summary='Change User Password',
        description='Change authenticated user password with old password verification',
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password changed successfully"),
            400: OpenApiResponse(description="Invalid data, incorrect old password, or passwords do not match"),
            401: OpenApiResponse(description="User not authenticated"),
        }
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            
            try:
                change_user_password(request.user, new_password)
                return Response({
                    "success": True,
                    "message": _("Password changed successfully")
                }, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({
                    "success": False,
                    "message": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "success": False,
            "message": _("Invalid data provided"),
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class LogoutAPIView(APIView):
    """
    Logout User API
    
    Logout authenticated user by blacklisting their refresh token.
    Prevents token reuse for enhanced security.
    Requires authentication.
    
    post:
        Logout the authenticated user and invalidate their refresh token.
        
        Request body parameters:
            - refresh_token: string (required) - Refresh token received at login (from tokens.refresh)
            OR
            - refresh: string (required) - Alternative parameter name for refresh token
        
        Returns:
            200 OK:
                - success: boolean (true)
                - message: string - "Logout successful" or "Logout successful (token not expired)"
                
            400 Bad Request:
                - Refresh token not provided
                - Invalid token format
                
            401 Unauthorized - User not authenticated
            500 Internal Server Error - Invalid refresh token
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Authentication'],
        summary='Logout User',
        description='Logout user and blacklist their refresh token for security',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh_token': {'type': 'string', 'description': 'Refresh token from login'},
                    'refresh': {'type': 'string', 'description': 'Alternative parameter name for refresh token'}
                },
                'anyOf': [
                    {'required': ['refresh_token']},
                    {'required': ['refresh']}
                ]
            }
        },
        responses={
            200: OpenApiResponse(description="Logout successful"),
            400: OpenApiResponse(description="Refresh token not provided or invalid format"),
            401: OpenApiResponse(description="User not authenticated"),
            500: OpenApiResponse(description="Invalid refresh token"),
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token') or request.data.get('refresh')
            if not refresh_token:
                return Response({
                    "success": False,
                    "message": _("Refresh token not provided")
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({
                    "success": True,
                    "message": _("Logout successful")
                }, status=status.HTTP_200_OK)
            except AttributeError:
                # Blacklist not enabled, just return success
                return Response({
                    "success": True,
                    "message": _("Logout successful (token not expired)")
                }, status=status.HTTP_200_OK)
        except TokenError as e:
            return Response({
                "success": False,
                "message": _(f"Token is invalid: {str(e)}")
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "success": False,
                "message": _(f"Error logging out: {str(e)}")
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== Core Content APIs ==========

class ArticleListAPIView(generics.ListAPIView):
    """
    List Articles API
    
    Retrieve all published articles.
    
    get:
        List all articles ordered by creation date (newest first).
        Supports pagination.
        
        Returns:
            - Array of article objects with id, title, content, author, created_at
    """
    permission_classes = [AllowAny]
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleListSerializer
    
    @extend_schema(
        tags=['Content'],
        summary='List Articles',
        description='Retrieve all published articles with pagination'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ArticleDetailAPIView(APIView):
    """
    Get Article Detail API
    
    Retrieve full content of a specific article.
    
    get:
        Get complete article with all details.
        
        Path parameters:
        - pk: integer - Article ID
        
        Returns:
            200 OK:
                - success: boolean (true)
                - data: Article object with full content
                
            404 Not Found - Article not found
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Content'],
        summary='Get Article Detail',
        description='Retrieve full content of a specific article',
        parameters=[
            OpenApiParameter('pk', OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Article ID')
        ]
    )
    def get(self, request, pk):
        article = get_object_or_404(Article, pk=pk)
        serializer = ArticleDetailSerializer(article)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class FAQListAPIView(generics.ListAPIView):
    """
    List FAQs API
    
    Retrieve all active frequently asked questions.
    
    get:
        List all active FAQs with pagination support.
        
        Returns:
            - List of FAQ objects with id, question, answer, created_at
    """
    permission_classes = [AllowAny]
    queryset = FAQ.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = FAQSerializer
    
    @extend_schema(
        tags=['Content'],
        summary='List FAQs',
        description='Retrieve all active frequently asked questions'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AboutAPIView(APIView):
    """
    Get About Page API
    
    Retrieve content for the about/company information page.
    
    get:
        Get about page content.
        
        Returns:
            200 OK:
                - success: boolean (true)
                - data: About page object with id, title, description, contact_info, created_at
                
            404 Not Found - About content not available
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Content'],
        summary='Get About Page',
        description='Retrieve company/about information page content'
    )
    def get(self, request):
        about = About.objects.first()
        if about:
            serializer = AboutSerializer(about)
            return Response({
                "success": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "message": _("About us content not found")
        }, status=status.HTTP_404_NOT_FOUND)


class TermListAPIView(generics.ListAPIView):
    """
    List Terms and Conditions API
    
    Retrieve all terms and conditions documents.
    
    get:
        List all terms ordered by creation date.
        
        Returns:
            - List of term objects with id, title, content, version, created_at
    """
    permission_classes = [AllowAny]
    queryset = Term.objects.all().order_by('-created_at')
    serializer_class = TermSerializer
    
    @extend_schema(
        tags=['Content'],
        summary='List Terms and Conditions',
        description='Retrieve all terms and conditions documents'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PrivacyListAPIView(generics.ListAPIView):
    """
    List Privacy Policies API
    
    Retrieve all privacy policy documents.
    
    get:
        List all privacy policies ordered by creation date.
        
        Returns:
            - List of privacy objects with id, title, content, version, created_at
    """
    permission_classes = [AllowAny]
    queryset = Privacy.objects.all().order_by('-created_at')
    serializer_class = PrivacySerializer
    
    @extend_schema(
        tags=['Content'],
        summary='List Privacy Policies',
        description='Retrieve all privacy policy documents'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ContactListAPIView(generics.ListAPIView):
    """
    List Contact Information API
    
    Retrieve all contact information records.
    
    get:
        List all contact records ordered by type.
        
        Returns:
            - List of contact objects with id, type, value (phone/email/address), created_at
    """
    permission_classes = [AllowAny]
    queryset = Contact.objects.all().order_by('type')
    serializer_class = ContactSerializer
    
    @extend_schema(
        tags=['Content'],
        summary='List Contact Information',
        description='Retrieve all contact information records'
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ContactPhoneAPIView(APIView):
    """
    Get Phone Contact API
    
    Retrieve the primary phone contact information.
    
    get:
        Get the first phone contact record from the database.
        
        Returns:
            200 OK:
                - status: 'success'
                - data: Contact object with type='phone' and value (phone number)
                - message: Status message
                
            404 Not Found - No phone contact found
            500 Internal Server Error
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Content'],
        summary='Get Phone Contact',
        description='Retrieve the primary phone contact information'
    )
    def get(self, request):
        """Get the first contact record where type is 'phone'"""
        try:
            phone_contact = Contact.objects.filter(type='phone').first()
            
            if not phone_contact:
                return Response({
                    'status': 'error',
                    'message': _("No phone contact found"),
                    'data': None
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = ContactSerializer(phone_contact)
            return Response({
                'status': 'success',
                'message': _("Phone contact retrieved successfully"),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e),
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IsTeacher(permissions.BasePermission):
    """Only teachers have access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teacher'


# ========== Home Page API ==========
class HomePageAPIView(APIView):
    """
    Home Page Content API
    
    Retrieve home page content including banners and featured sections.
    
    get:
        Get home page data for mobile app home screen.
        
        Returns:
            200 OK:
                - data: array of sections
                    - id: section identifier
                    - type: section type (banners, featured, etc.)
                    - data: section content
                - message: Status message
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Content'],
        summary='Get Home Page Content',
        description='Retrieve home page content including banners and featured sections'
    )
    def get(self, request):
        # 1. Main banners
        banners = Banner.objects.filter(is_active=True, placement='app_home').order_by('sort', '-created_at')[:5]
        banners_data = BannerSerializer(banners, many=True).data

        return Response({
            'status': 'success',
            'data': [
                {
                    "id": "banners",
                    "type": "banners",
                    "data": banners_data
                }
            ],
            'message': _("Home page data retrieved successfully")
        })


# ===== Teacher Time Slot (Availability) APIs =====
class CreateTeacherAvailabilityAPIView(APIView):
    """
    Create Teacher Availability Slots API (Bulk with Date Range)
    
    Add multiple time slots for teacher availability based on date range.
    Similar to admin bulk creation feature.
    Only teachers can create availability slots.
    Requires authentication.
    
    post:
        Create multiple teacher availability slots for a date range.
        
        Request body parameters (JSON):
        - start_date: string (required) - Start date in YYYY/MM/DD format
        - end_date: string (required) - End date in YYYY/MM/DD format
        - daily_start_time: string (required) - Daily start time in HH:MM format
        - daily_end_time: string (required) - Daily end time in HH:MM format
        - session_duration: integer (optional, default: 30) - Session duration in minutes
        - break_duration: integer (optional, default: 10) - Break duration between sessions in minutes
        - price: number (required) - Price per session
        - notes: string (optional) - Additional notes about the slots
        
        Returns:
            201 Created:
                - data: array - List of created availability slots
                - created_count: integer - Number of slots created
                - message: string - "شکاف‌های زمانی با موفقیت ایجاد شدند"
                
            400 Bad Request - Invalid data provided
            403 Forbidden - User is not a teacher
        
        Example Request:
        ```json
        {
            "start_date": "1403/01/01",
            "end_date": "1403/01/10",
            "daily_start_time": "09:00",
            "daily_end_time": "17:00",
            "session_duration": 30,
            "break_duration": 10,
            "price": 50000,
            "notes": "Online classes via Zoom"
        }
        ```
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    
    @extend_schema(
        tags=['Teacher Time Slots'],
        summary='Create Teacher Availability Slots (Bulk Date Range)',
        description='Add multiple time slots for teacher availability based on date range with automatic session scheduling.',
        request=inline_serializer(
            name='CreateTeacherAvailabilityBulk',
            fields={
                'start_date': serializers.CharField(help_text='Start date in YYYY/MM/DD format (Jalali)'),
                'end_date': serializers.CharField(help_text='End date in YYYY/MM/DD format (Jalali)'),
                'daily_start_time': serializers.TimeField(help_text='Daily start time in HH:MM format'),
                'daily_end_time': serializers.TimeField(help_text='Daily end time in HH:MM format'),
                'session_duration': serializers.IntegerField(default=30, help_text='Session duration in minutes (default: 30)'),
                'break_duration': serializers.IntegerField(default=10, help_text='Break duration in minutes (default: 10)'),
                'price': serializers.DecimalField(max_digits=10, decimal_places=2, help_text='Price per session'),
                'notes': serializers.CharField(required=False, allow_blank=True, help_text='Additional notes (optional)'),
            }
        ),
        responses={
            201: OpenApiResponse(description="Time slots created successfully"),
            400: OpenApiResponse(description="Invalid data provided"),
            403: OpenApiResponse(description="User is not a teacher"),
        }
    )
    def post(self, request):
        import jdatetime
        from datetime import datetime, timedelta
        from classroom.models import TeacherAvailability
        
        # فقط معلمین می‌توانند شکاف زمانی اضافه کنند
        if request.user.role != 'teacher':
            return Response(
                {'error': _('شما معلم نیستید')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # گرفتن داده‌ها
        start_date_str = request.data.get('start_date', '').strip()
        end_date_str = request.data.get('end_date', '').strip()
        daily_start_str = request.data.get('daily_start_time', '').strip()
        daily_end_str = request.data.get('daily_end_time', '').strip()
        session_minutes_str = request.data.get('session_duration', '30')
        break_minutes_str = request.data.get('break_duration', '10')
        price_str = request.data.get('price', '')
        notes = request.data.get('notes', '').strip()
        
        # اعتبارسنجی پارامترهای الزامی
        if not all([start_date_str, end_date_str, daily_start_str, daily_end_str, price_str]):
            return Response(
                {'error': _('لطفاً تمام فیلدهای الزامی را پر کنید')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تبدیل تاریخ‌های شمسی به میلادی
        try:
            start_date = jdatetime.datetime.strptime(start_date_str, '%Y/%m/%d').togregorian().date()
            end_date = jdatetime.datetime.strptime(end_date_str, '%Y/%m/%d').togregorian().date()
        except Exception as e:
            return Response(
                {'error': _('فرمت تاریخ نادرست است. لطفاً از فرمت YYYY/MM/DD استفاده کنید')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تبدیل زمان‌ها و مدت‌های زمانی
        try:
            daily_start = datetime.strptime(daily_start_str, '%H:%M').time()
            daily_end = datetime.strptime(daily_end_str, '%H:%M').time()
            session_minutes = int(session_minutes_str) if session_minutes_str else 30
            break_minutes = int(break_minutes_str) if break_minutes_str else 10
            price = float(price_str) if price_str else 0
            
            if session_minutes <= 0 or break_minutes < 0 or price <= 0:
                raise ValueError(_('مقادیر باید مثبت باشند'))
        except (ValueError, TypeError):
            return Response(
                {'error': _('خطا در پردازش داده‌های زمان یا قیمت')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ایجاد شکاف‌های زمانی برای هر روز
        created = 0
        cur_date = start_date
        
        while cur_date <= end_date:
            cursor = datetime.combine(cur_date, daily_start)
            day_end = datetime.combine(cur_date, daily_end)
            
            while cursor + timedelta(minutes=session_minutes) <= day_end:
                slot_start = cursor.time()
                slot_end = (cursor + timedelta(minutes=session_minutes)).time()
                
                # بررسی تکراری نبودن
                if not TeacherAvailability.objects.filter(
                    teacher_id=request.user.id,
                    date=cur_date,
                    start_time=slot_start,
                    end_time=slot_end
                ).exists():
                    TeacherAvailability.objects.create(
                        teacher_id=request.user.id,
                        date=cur_date,
                        start_time=slot_start,
                        end_time=slot_end,
                        price=price,
                        is_available=True,
                        notes=notes
                    )
                    created += 1
                
                cursor += timedelta(minutes=(session_minutes + break_minutes))
            
            cur_date = cur_date + timedelta(days=1)
        
        if created == 0:
            return Response(
                {'error': _('هیچ شکاف زمانی جدیدی ایجاد نشد. شاید همه شکاف‌ها قبلاً وجود دارند.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # بازیابی و بازگشت شکاف‌های ایجاد شده
        new_slots = TeacherAvailability.objects.filter(
            teacher_id=request.user.id,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date', 'start_time')
        
        from .classroom_serializers import TeacherAvailabilitySerializer
        serializer = TeacherAvailabilitySerializer(new_slots, many=True)
        
        return Response(
            {
                'data': serializer.data,
                'created_count': created,
                'message': _('شکاف‌های زمانی با موفقیت ایجاد شدند')
            },
            status=status.HTTP_201_CREATED
        )


class BulkCreateTeacherAvailabilityAPIView(APIView):
    """
    Bulk Create Teacher Availability Slots (Direct) API
    
    Add multiple time slots directly for teacher availability.
    Use this for creating individual slots without date range calculation.
    For automatic date range scheduling, use CreateTeacherAvailabilityAPIView.
    Only teachers can create availability slots.
    Requires authentication.
    
    post:
        Create multiple teacher availability slots at once (direct array).
        
        Request body parameters:
        - availabilities: array (required) - Array of availability objects
            - date: string - Date in YYYY/MM/DD format (Jalali)
            - start_time: string - Start time in HH:MM format
            - end_time: string - End time in HH:MM format
            - price: number - Price per session
            - notes: string (optional) - Additional notes
        
        Returns:
            201 Created:
                - data: array - List of created availability slots
                - count: integer - Number of slots created
                - message: string - "شکاف‌های زمانی با موفقیت ایجاد شدند"
                
            400 Bad Request - Invalid data or empty array
            403 Forbidden - User is not a teacher
        
        Example Request:
        ```json
        {
            "availabilities": [
                {
                    "date": "1403/01/01",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "price": 50000,
                    "notes": "Morning session"
                },
                {
                    "date": "1403/01/01",
                    "start_time": "14:00",
                    "end_time": "15:00",
                    "price": 50000,
                    "notes": "Afternoon session"
                }
            ]
        }
        ```
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    
    @extend_schema(
        tags=['Teacher Time Slots'],
        summary='Bulk Create Teacher Availability Slots (Direct)',
        description='Add multiple time slots directly for teacher availability without date range calculation.',
        request=inline_serializer(
            name='BulkCreateTeacherAvailabilityDirect',
            fields={
                'availabilities': serializers.ListField(
                    child=inline_serializer(
                        name='AvailabilityItemDirect',
                        fields={
                            'date': serializers.CharField(help_text='Date in YYYY/MM/DD format (Jalali)'),
                            'start_time': serializers.TimeField(help_text='Start time in HH:MM format'),
                            'end_time': serializers.TimeField(help_text='End time in HH:MM format'),
                            'price': serializers.DecimalField(max_digits=10, decimal_places=2, help_text='Price per session'),
                            'notes': serializers.CharField(required=False, allow_blank=True, help_text='Additional notes (optional)'),
                        }
                    ),
                    help_text='Array of availability objects to create'
                )
            }
        ),
        responses={
            201: OpenApiResponse(description="Time slots created successfully"),
            400: OpenApiResponse(description="Invalid data or empty array provided"),
            403: OpenApiResponse(description="User is not a teacher"),
        }
    )
    def post(self, request):
        from .classroom_serializers import TeacherAvailabilitySerializer
        from classroom.models import TeacherAvailability
        
        # فقط معلمین می‌توانند
        if request.user.role != 'teacher':
            return Response(
                {'error': _('شما معلم نیستید')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        availabilities_data = request.data.get('availabilities', [])
        if not isinstance(availabilities_data, list) or len(availabilities_data) == 0:
            return Response(
                {'error': _('لطفاً لیست شکاف‌های زمانی را ارائه دهید')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # بیشترین تعداد در یک درخواست
        if len(availabilities_data) > 100:
            return Response(
                {'error': _('حداکثر 100 شکاف زمانی در یک درخواست مجاز است')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # اضافه کردن معلم به هر شکاف
        for item in availabilities_data:
            item['teacher'] = request.user.id
        
        serializer = TeacherAvailabilitySerializer(data=availabilities_data, many=True)
        if serializer.is_valid():
            instances = serializer.save()
            return Response(
                {
                    'data': serializer.data,
                    'count': len(instances),
                    'message': _('شکاف‌های زمانی با موفقیت ایجاد شدند')
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherAvailabilityListAPIView(generics.ListAPIView):
    """
    Teacher Availability List API
    
    Retrieve teacher availability time slots with optional filters.
    Teachers see only their own slots, admins/students can query others.
    Requires authentication.
    
    get:
        Get list of teacher availability slots.
        
        Query parameters:
        - teacher_id: integer (optional) - Filter by specific teacher
        - date: string (optional) - Filter by date in YYYY/MM/DD format
        - is_available: boolean (optional) - Filter available slots only
        
        Returns:
            200 OK:
                - data: array - List of availability slots
                - count: integer - Total number of slots
                
            401 Unauthorized - User not authenticated
    """
    permission_classes = [IsAuthenticated]
    serializer_class = None
    
    @extend_schema(
        tags=['Teacher Time Slots'],
        summary='Get Teacher Availability Slots',
        description='Retrieve teacher availability time slots with optional filters',
        parameters=[
            OpenApiParameter('teacher_id', OpenApiTypes.INT, required=False, description='Filter by specific teacher'),
            OpenApiParameter('date', OpenApiTypes.STR, required=False, description='Filter by date in YYYY/MM/DD format'),
            OpenApiParameter('is_available', OpenApiTypes.BOOL, required=False, description='Filter available slots only'),
        ]
    )
    def get(self, request, *args, **kwargs):
        from .classroom_serializers import TeacherAvailabilitySerializer
        from classroom.models import TeacherAvailability
        
        # اگر معلم است، فقط خود را می‌بیند
        if request.user.role == 'teacher':
            queryset = TeacherAvailability.objects.filter(teacher=request.user)
        else:
            # ادمین یا دانش‌آموز
            teacher_id = request.query_params.get('teacher_id')
            if teacher_id:
                queryset = TeacherAvailability.objects.filter(teacher_id=teacher_id)
            else:
                queryset = TeacherAvailability.objects.all()
        
        # فیلتر بر اساس تاریخ
        date_str = request.query_params.get('date')
        if date_str:
            queryset = queryset.filter(date=date_str)
        
        # فیلتر دسترسی‌پذیری
        is_available = request.query_params.get('is_available')
        if is_available and is_available.lower() in ['true', '1', 'yes']:
            queryset = queryset.filter(is_available=True)
        
        serializer = TeacherAvailabilitySerializer(queryset, many=True)
        return Response(
            {'data': serializer.data, 'count': queryset.count()},
            status=status.HTTP_200_OK
        )


class UpdateTeacherAvailabilityAPIView(APIView):
    """
    Update Teacher Availability Slot API
    
    Update an existing teacher availability time slot.
    Only the teacher who created the slot can update it.
    Cannot update booked slots.
    Requires authentication.
    
    patch:
        Update teacher availability slot details.
        
        Path parameters:
        - id: integer (required) - Time slot ID
        
        Request body parameters:
        - date: string (optional) - Date in YYYY/MM/DD format
        - start_time: string (optional) - Start time in HH:MM format
        - end_time: string (optional) - End time in HH:MM format
        - price: number (optional) - Price per hour or session
        - notes: string (optional) - Additional notes
        - is_available: boolean (optional) - Availability status
        
        Returns:
            200 OK:
                - data: object - Updated slot details
                - message: string - "Slot updated successfully"
                
            400 Bad Request - Cannot update booked slot
            403 Forbidden - User is not slot owner
            404 Not Found - Slot does not exist
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    
    @extend_schema(
        tags=['Teacher Time Slots'],
        summary='Update Teacher Availability Slot',
        description='Update existing teacher availability slot (owner only)',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Time slot ID')
        ]
    )
    def patch(self, request, id):
        from .classroom_serializers import TeacherAvailabilitySerializer
        from classroom.models import TeacherAvailability
        
        try:
            availability = TeacherAvailability.objects.get(id=id)
        except TeacherAvailability.DoesNotExist:
            return Response(
                {'error': _('شکاف زمانی یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # فقط معلم می‌تواند ویرایش کند
        if request.user.role != 'teacher' or availability.teacher_id != request.user.id:
            return Response(
                {'error': _('شما دسترسی به این شکاف زمانی ندارید')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # اگر رزرو شده، نمی‌تواند تغییر کند
        if availability.is_booked:
            return Response(
                {'error': _('این شکاف زمانی رزرو شده است و نمی‌تواند تغییر کند')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TeacherAvailabilitySerializer(availability, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'data': serializer.data, 'message': _('شکاف زمانی با موفقیت ویرایش شد')},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteTeacherAvailabilityAPIView(APIView):
    """
    Delete Teacher Availability Slot API
    
    Delete an existing teacher availability time slot.
    Only the teacher who created the slot can delete it.
    Cannot delete booked slots.
    Requires authentication.
    
    delete:
        Delete teacher availability slot.
        
        Path parameters:
        - id: integer (required) - Time slot ID
        
        Returns:
            204 No Content - Slot deleted successfully
            
            400 Bad Request - Cannot delete booked slot
            403 Forbidden - User is not slot owner
            404 Not Found - Slot does not exist
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Teacher Time Slots'],
        summary='Delete Teacher Availability Slot',
        description='Delete existing teacher availability slot (owner only, cannot be booked)',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Time slot ID')
        ],
        responses={
            204: OpenApiResponse(description="Slot deleted successfully"),
            400: OpenApiResponse(description="Cannot delete booked slot"),
            403: OpenApiResponse(description="User is not slot owner"),
            404: OpenApiResponse(description="Slot not found"),
        }
    )
    def delete(self, request, id):
        from classroom.models import TeacherAvailability
        
        try:
            availability = TeacherAvailability.objects.get(id=id)
        except TeacherAvailability.DoesNotExist:
            return Response(
                {'error': _('شکاف زمانی یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # فقط معلم می‌تواند حذف کند
        if request.user.role != 'teacher' or availability.teacher_id != request.user.id:
            return Response(
                {'error': _('شما دسترسی به این شکاف زمانی ندارید')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # اگر رزرو شده، نمی‌تواند حذف کند
        if availability.is_booked:
            return Response(
                {'error': _('این شکاف زمانی رزرو شده است و نمی‌تواند حذف شود')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        availability.delete()
        return Response(
            {'message': _('شکاف زمانی با موفقیت حذف شد')},
            status=status.HTTP_204_NO_CONTENT
        )


