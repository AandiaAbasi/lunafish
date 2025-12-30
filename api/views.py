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
import jdatetime
import datetime as dt
from account.serializers import *
from account.services import *
from account.models import OTP, VerificationToken
from exercise.models import Field, FieldDetail, CategoryField, Order, OrderDetail
from .exercise_serializers import (
    FieldCreateUpdateSerializer, FieldRetrieveSerializer,
    CategoryFieldCreateSerializer, CategoryFieldRetrieveSerializer,
    OrderCreateSubmitSerializer, OrderRetrieveSerializer, OrderListSerializer,
    OrderDetailRetrieveSerializer
)


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
                - message: string - "بازه زمانی با موفقیت ایجاد شدند"
                
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
        description='Create multiple time slots for a date range with automatic scheduling. Similar to admin bulk creation.',
        request=inline_serializer(
            name='CreateTeacherAvailabilityBulk',
            fields={
                'start_date': serializers.CharField(
                    help_text='Start date in YYYY/MM/DD Jalali format (e.g., 1403/01/01)'
                ),
                'end_date': serializers.CharField(
                    help_text='End date in YYYY/MM/DD Jalali format (e.g., 1403/01/10)'
                ),
                'daily_start_time': serializers.TimeField(
                    help_text='Daily start time in HH:MM format (e.g., 09:00)'
                ),
                'daily_end_time': serializers.TimeField(
                    help_text='Daily end time in HH:MM format (e.g., 17:00)'
                ),
                'session_duration': serializers.IntegerField(
                    default=30,
                    help_text='Duration of each session in minutes (default: 30, min: 5)',
                    min_value=5
                ),
                'break_duration': serializers.IntegerField(
                    default=10,
                    help_text='Break duration between sessions in minutes (default: 10, min: 0)',
                    min_value=0
                ),
                'price': serializers.DecimalField(
                    max_digits=10,
                    decimal_places=2,
                    help_text='Price per session in currency units'
                ),
                'discount_price': serializers.DecimalField(
                    max_digits=10,
                    decimal_places=2,
                    required=False,
                    allow_null=True,
                    help_text='Discounted price per session (optional)'
                ),
                'notes': serializers.CharField(
                    required=False,
                    allow_blank=True,
                    help_text='Optional notes about the availability slots'
                ),
            }
        ),
        responses={
            201: OpenApiResponse(description="Time slots created successfully with count and details"),
            400: OpenApiResponse(description="Invalid date format, time values, or other data validation error"),
            403: OpenApiResponse(description="User is not authenticated as a teacher"),
        }
    )
    def post(self, request):
        import jdatetime
        from datetime import datetime, timedelta
        from classroom.models import TeacherAvailability
        
        # فقط معلمین می‌توانند بازه زمانی اضافه کنند
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
        discount_price_str = request.data.get('discount_price', '')
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
            discount_price = float(discount_price_str) if discount_price_str else None
            
            if session_minutes <= 0 or break_minutes < 0 or price <= 0:
                raise ValueError(_('مقادیر باید مثبت باشند'))
        except (ValueError, TypeError):
            return Response(
                {'error': _('خطا در پردازش داده‌های زمان یا قیمت')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ایجاد بازه‌های زمانی برای هر روز
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
                        discount_price=discount_price,
                        is_available=True,
                        notes=notes
                    )
                    created += 1
                
                cursor += timedelta(minutes=(session_minutes + break_minutes))
            
            cur_date = cur_date + timedelta(days=1)
        
        if created == 0:
            return Response(
                {'error': _('هیچ بازه زمانی جدیدی ایجاد نشد. شاید همه بازه‌ها قبلاً وجود دارند.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # بازیابی و بازگشت بازه‌های ایجاد شده
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
                'message': _('بازه‌های زمانی با موفقیت ایجاد شدند')
            },
            status=status.HTTP_201_CREATED
        )


class BulkCreateTeacherAvailabilityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from classroom.models import TeacherAvailability
        import jdatetime
        import datetime as dt
        from decimal import Decimal

        if request.user.role != 'teacher':
            return Response({'error': _('شما معلم نیستید')}, status=403)

        try:
            start_date = jdatetime.datetime.strptime(
                request.data['start_date'], '%Y/%m/%d'
            ).togregorian().date()

            end_date = jdatetime.datetime.strptime(
                request.data['end_date'], '%Y/%m/%d'
            ).togregorian().date()

            daily_start = dt.datetime.strptime(
                request.data['daily_start_time'], '%H:%M'
            ).time()

            daily_end = dt.datetime.strptime(
                request.data['daily_end_time'], '%H:%M'
            ).time()

            session_minutes = int(request.data.get('session_duration', 45))
            break_minutes = int(request.data.get('break_duration', 15))
            price = Decimal(request.data.get('price', 0))
            
            # Handle discount_price - can be null, empty string, or a value
            discount_price_str = request.data.get('discount_price')
            if discount_price_str is None or discount_price_str == '':
                discount_price = None
            else:
                discount_price = Decimal(str(discount_price_str))

        except (ValueError, TypeError, Decimal.InvalidOperation) as e:
            return Response(
                {
                    'error': _('داده‌های ورودی نامعتبر است'),
                    'details': str(e)
                },
                status=400
            )

        created = 0
        cur_date = start_date

        while cur_date <= end_date:
            cursor = dt.datetime.combine(cur_date, daily_start)
            day_end = dt.datetime.combine(cur_date, daily_end)

            while cursor + dt.timedelta(minutes=session_minutes) <= day_end:
                slot_start = cursor.time()
                slot_end = (cursor + dt.timedelta(minutes=session_minutes)).time()

                exists = TeacherAvailability.objects.filter(
                    teacher=request.user,
                    date=cur_date,
                    start_time=slot_start,
                    end_time=slot_end
                ).exists()

                if not exists:
                    TeacherAvailability.objects.create(
                        teacher=request.user,
                        date=cur_date,
                        start_time=slot_start,
                        end_time=slot_end,
                        price=price,
                        discount_price=discount_price,
                        is_available=True,
                        is_booked=False
                    )
                    created += 1

                cursor += dt.timedelta(minutes=session_minutes + break_minutes)

            cur_date += dt.timedelta(days=1)

        return Response({
            'count': created,
            'message': _('بازه‌های زمانی با موفقیت ایجاد شدند')
        }, status=201)


class TeacherAvailabilityListAPIView(generics.ListAPIView):
    """
    Teacher Availability List API
    
    Retrieve teacher availability time slots with optional filters.
    Teachers see only their own slots, admins/students can query others.
    Requires authentication.
    
    get:
        Get list of teacher availability slots with pagination.
        
        Query parameters:
        - teacher_id: integer (optional) - Filter by specific teacher
        - date: string (optional) - Filter by date in YYYY/MM/DD format
        - is_available: boolean (optional) - Filter available slots only
        - page: integer (optional, default: 1) - Page number for pagination
        - page_size: integer (optional, default: 20) - Items per page
        
        Returns:
            200 OK:
                - count: integer - Total number of slots
                - next: string - URL to next page (or null)
                - previous: string - URL to previous page (or null)
                - results: array - List of availability slots on current page
                
            401 Unauthorized - User not authenticated
    """
    permission_classes = [IsAuthenticated]
    serializer_class = None
    pagination_class = None  # سفارشی سازی پایین‌تر
    
    def get_paginator(self):
        """استفاده از pagination پیش‌فرض DRF"""
        from rest_framework.pagination import PageNumberPagination
        
        class StandardResultsSetPagination(PageNumberPagination):
            page_size = 20
            page_size_query_param = 'page_size'
            page_size_query_description = 'Number of results to return per page.'
            max_page_size = 100
        
        return StandardResultsSetPagination()
    
    @extend_schema(
        tags=['Teacher Time Slots'],
        summary='Get Teacher Availability Slots',
        description='Retrieve teacher availability time slots with optional filters and pagination',
        parameters=[
            OpenApiParameter('teacher_id', OpenApiTypes.INT, required=False, description='Filter by specific teacher'),
            OpenApiParameter('start_date', OpenApiTypes.STR, required=False, description='Filter from date in YYYY/MM/DD Jalali format (e.g., 1403/01/01)'),
            OpenApiParameter('end_date', OpenApiTypes.STR, required=False, description='Filter to date in YYYY/MM/DD Jalali format (e.g., 1403/01/31)'),
            OpenApiParameter('date', OpenApiTypes.STR, required=False, description='Filter by specific date in YYYY/MM/DD Jalali format (e.g., 1403/01/15)'),
            OpenApiParameter('is_available', OpenApiTypes.BOOL, required=False, description='Filter available slots (true/false/1/0)'),
            OpenApiParameter('is_booked', OpenApiTypes.BOOL, required=False, description='Filter booked slots (true/false/1/0)'),
            OpenApiParameter('page', OpenApiTypes.INT, required=False, description='Page number (default: 1)'),
            OpenApiParameter('page_size', OpenApiTypes.INT, required=False, description='Items per page (default: 20, max: 100)'),
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
        
        # فیلتر بر اساس تاریخ (شمسی به میلادی)
        date_str = request.query_params.get('date')
        if date_str:
            try:
                # تبدیل تاریخ شمسی (YYYY/MM/DD) به میلادی
                gregorian_date = jdatetime.datetime.strptime(date_str, '%Y/%m/%d').togregorian().date()
                queryset = queryset.filter(date=gregorian_date)
            except (ValueError, TypeError):
                # اگر فرمت نادرست بود، فیلتر را무시 کن
                pass
        
        # فیلتر بر اساس بازه تاریخی (start_date تا end_date)
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if start_date_str:
            try:
                # تبدیل تاریخ شمسی شروع به میلادی
                start_gregorian_date = jdatetime.datetime.strptime(start_date_str, '%Y/%m/%d').togregorian().date()
                queryset = queryset.filter(date__gte=start_gregorian_date)
            except (ValueError, TypeError):
                pass
        
        if end_date_str:
            try:
                # تبدیل تاریخ شمسی پایان به میلادی
                end_gregorian_date = jdatetime.datetime.strptime(end_date_str, '%Y/%m/%d').togregorian().date()
                queryset = queryset.filter(date__lte=end_gregorian_date)
            except (ValueError, TypeError):
                pass
        
        # فیلتر is_available
        is_available = request.query_params.get('is_available')
        if is_available is not None:
            if is_available.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_available=True)
            elif is_available.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_available=False)
        
        # فیلتر is_booked
        is_booked = request.query_params.get('is_booked')
        if is_booked is not None:
            if is_booked.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_booked=True)
            elif is_booked.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_booked=False)
        
        # مرتب‌سازی
        queryset = queryset.order_by('-date', '-start_time')
        
        # Pagination
        paginator = self.get_paginator()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        serializer = TeacherAvailabilitySerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)


class TeacherAvailabilityDetailAPIView(APIView):
    """
    Get Teacher Availability Slot Details API
    
    Retrieve detailed information about a specific teacher availability time slot.
    Only the teacher who created the slot can view its details.
    Requires authentication.
    
    get:
        Retrieve complete details of a teacher availability slot.
        
        Path parameters:
        - id: integer (required) - Time slot ID
        
        Returns:
            200 OK:
                - data: object - Complete slot details with all information
                - message: string - "Slot details retrieved successfully"
                - Fields returned:
                    - id: integer - Slot ID
                    - teacher: integer - Teacher ID
                    - date: string - Date in YYYY/MM/DD format
                    - start_time: string - Start time in HH:MM format
                    - end_time: string - End time in HH:MM format
                    - price: number - Regular price
                    - discount_price: number - Discounted price (if any)
                    - is_available: boolean - Availability status
                    - is_booked: boolean - Booking status
                    - notes: string - Additional notes
                    - created_at: string - Creation timestamp
                    - updated_at: string - Last update timestamp
                
            403 Forbidden - User is not slot owner
            404 Not Found - Slot does not exist
    
    Example GET Request:
    ```
    GET /api/teacher/availability/123/
    Authorization: Bearer <token>
    ```
    
    Example GET Response:
    ```json
    {
        "data": {
            "id": 123,
            "teacher": 1,
            "date": "1403/01/15",
            "start_time": "09:00",
            "end_time": "10:00",
            "price": 50000,
            "discount_price": 40000,
            "is_available": true,
            "is_booked": false,
            "notes": "Online via Zoom - English Speaking Session",
            "created_at": "2025-01-01T10:00:00Z",
            "updated_at": "2025-01-02T14:30:00Z"
        },
        "message": "Slot details retrieved successfully"
    }
    ```
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Teacher Time Slots'],
        summary='Get Teacher Availability Slot Details',
        description='Retrieve complete details of a specific teacher availability slot',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Time slot ID')
        ],
        responses={
            200: OpenApiResponse(description="Slot details retrieved successfully"),
            403: OpenApiResponse(description="User is not slot owner"),
            404: OpenApiResponse(description="Slot not found"),
        }
    )
    def get(self, request, id):
        from .classroom_serializers import TeacherAvailabilitySerializer
        from classroom.models import TeacherAvailability
        
        try:
            availability = TeacherAvailability.objects.get(id=id)
        except TeacherAvailability.DoesNotExist:
            return Response(
                {'error': _('بازه زمانی یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # فقط معلم می‌تواند جزئیات خود را ببیند
        if request.user.role != 'teacher' or availability.teacher_id != request.user.id:
            return Response(
                {'error': _('شما دسترسی به این بازه زمانی ندارید')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TeacherAvailabilitySerializer(availability)
        return Response(
            {'data': serializer.data, 'message': _('جزئیات بازه زمانی با موفقیت دریافت شد')},
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
        - discount_price: number (optional) - Discounted price
        - notes: string (optional) - Additional notes
        - is_available: boolean (optional) - Availability status
        
        Returns:
            200 OK:
                - data: object - Updated slot details
                - message: string - "Slot updated successfully"
                
            400 Bad Request - Cannot update booked slot
            403 Forbidden - User is not slot owner
            404 Not Found - Slot does not exist
    
    Example PATCH Request:
    ```json
    {
        "price": 60000,
        "discount_price": 45000,
        "notes": "Updated: Online via Google Meet"
    }
    ```
    
    Example PATCH Response:
    ```json
    {
        "data": {
            "id": 123,
            "teacher": 1,
            "date": "1403/01/15",
            "start_time": "09:00",
            "end_time": "10:00",
            "price": 60000,
            "discount_price": 45000,
            "is_available": true,
            "is_booked": false,
            "notes": "Updated: Online via Google Meet",
            "created_at": "2025-01-01T10:00:00Z"
        },
        "message": "Slot updated successfully"
    }
    ```
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    
    @extend_schema(
        tags=['Teacher Time Slots'],
        summary='Update Teacher Availability Slot',
        description='Update existing teacher availability slot (owner only)',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Time slot ID')
        ],
        responses={
            200: OpenApiResponse(description="Slot updated successfully"),
            400: OpenApiResponse(description="Cannot update booked slot"),
            403: OpenApiResponse(description="User is not slot owner"),
            404: OpenApiResponse(description="Slot not found"),
        }
    )
    def patch(self, request, id):
        from .classroom_serializers import TeacherAvailabilitySerializer
        from classroom.models import TeacherAvailability
        
        try:
            availability = TeacherAvailability.objects.get(id=id)
        except TeacherAvailability.DoesNotExist:
            return Response(
                {'error': _('بازه زمانی یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # فقط معلم می‌تواند ویرایش کند
        if request.user.role != 'teacher' or availability.teacher_id != request.user.id:
            return Response(
                {'error': _('شما دسترسی به این بازه زمانی ندارید')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # اگر رزرو شده، نمی‌تواند تغییر کند
        if availability.is_booked:
            return Response(
                {'error': _('این بازه زمانی رزرو شده است و نمی‌تواند تغییر کند')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TeacherAvailabilitySerializer(availability, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'data': serializer.data, 'message': _('بازه زمانی با موفقیت ویرایش شد')},
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
                {'error': _('بازه زمانی یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # فقط معلم می‌تواند حذف کند
        if request.user.role != 'teacher' or availability.teacher_id != request.user.id:
            return Response(
                {'error': _('شما دسترسی به این بازه زمانی ندارید')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # اگر رزرو شده، نمی‌تواند حذف کند
        if availability.is_booked:
            return Response(
                {'error': _('این بازه زمانی رزرو شده است و نمی‌تواند حذف شود')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        availability.delete()
        return Response(
            {'message': _('بازه زمانی با موفقیت حذف شد')},
            status=status.HTTP_204_NO_CONTENT
        )


# ========== Teaching Subject APIs (کلاس‌های معلم) ==========

class TeachingSubjectListAPIView(APIView):
    """
    List Teaching Subjects
    
    دریافت لیست موضوعات تدریس
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by teacher if requested"""
        from classroom.models import TeachingSubject
        
        if self.request.user.role == 'teacher':
            # معلم تنها می‌تواند موضوعات خود را ببیند
            return TeachingSubject.objects.filter(teacher=self.request.user)
        elif self.request.user.role == 'admin':
            # ادمین تمام موضوعات را می‌بیند
            return TeachingSubject.objects.all()
        else:
            # دانش‌آموز تنها موضوعات فعال را می‌بیند
            return TeachingSubject.objects.filter(is_active=True)
    
    @extend_schema(
        tags=['Teaching Subject'],
        summary='List Teaching Subjects',
        description='دریافت لیست موضوعات تدریس',
        parameters=[
            OpenApiParameter('teacher', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by teacher ID'),
            OpenApiParameter('level', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Filter by level: beginner, intermediate, advanced'),
            OpenApiParameter('is_active', OpenApiTypes.BOOL, required=False, location=OpenApiParameter.QUERY, description='Filter by active status'),
        ],
        responses={
            200: OpenApiResponse(description="List of teaching subjects"),
        }
    )
    def get(self, request):
        from classroom.models import TeachingSubject
        from .classroom_serializers import TeachingSubjectSerializer
        
        queryset = self.get_queryset()
        
        # Filter by teacher
        teacher_id = request.query_params.get('teacher')
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        # Filter by level
        level = request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        # Filter by active status
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active)
        
        serializer = TeachingSubjectSerializer(queryset, many=True)
        return Response({'results': serializer.data}, status=status.HTTP_200_OK)


class TeachingSubjectCreateAPIView(APIView):
    """
    Create Teaching Subject
    
    ایجاد موضوع تدریس جدید
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    @extend_schema(
        tags=['Teaching Subject'],
        summary='Create Teaching Subject',
        description='ایجاد موضوع تدریس جدید (فقط برای معلمان)',
        request=None,
        responses={
            201: OpenApiResponse(description="Subject created successfully"),
            400: OpenApiResponse(description="Invalid data"),
            403: OpenApiResponse(description="Only teachers can create subjects"),
        }
    )
    def post(self, request):
        from classroom.models import TeachingSubject
        from .classroom_serializers import TeachingSubjectSerializer
        
        # فقط معلمان می‌توانند موضوع ایجاد کنند
        if request.user.role != 'teacher':
            return Response(
                {'error': _('تنها معلمان می‌توانند موضوع تدریس ایجاد کنند')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data.copy()
        data['teacher'] = request.user.id
        
        serializer = TeachingSubjectSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeachingSubjectRetrieveAPIView(APIView):
    """
    Retrieve Teaching Subject
    
    دریافت جزئیات موضوع تدریس
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Teaching Subject'],
        summary='Get Teaching Subject Details',
        description='دریافت جزئیات موضوع تدریس',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Subject ID')
        ],
        responses={
            200: OpenApiResponse(description="Subject details"),
            404: OpenApiResponse(description="Subject not found"),
        }
    )
    def get(self, request, id):
        from classroom.models import TeachingSubject
        from .classroom_serializers import TeachingSubjectSerializer
        
        try:
            subject = TeachingSubject.objects.get(id=id)
        except TeachingSubject.DoesNotExist:
            return Response(
                {'error': _('موضوع تدریسی یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # بررسی دسترسی
        if request.user.role != 'admin' and request.user.role == 'student':
            if not subject.is_active:
                return Response(
                    {'error': _('دسترسی محدود است')},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = TeachingSubjectSerializer(subject)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TeachingSubjectUpdateAPIView(APIView):
    """
    Update Teaching Subject
    
    ویرایش موضوع تدریس
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    @extend_schema(
        tags=['Teaching Subject'],
        summary='Update Teaching Subject',
        description='ویرایش موضوع تدریس (صاحب موضوع یا ادمین)',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Subject ID')
        ],
        request=None,
        responses={
            200: OpenApiResponse(description="Subject updated successfully"),
            400: OpenApiResponse(description="Invalid data"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Subject not found"),
        }
    )
    def post(self, request, id):
        from classroom.models import TeachingSubject
        from .classroom_serializers import TeachingSubjectSerializer
        
        try:
            subject = TeachingSubject.objects.get(id=id)
        except TeachingSubject.DoesNotExist:
            return Response(
                {'error': _('موضوع تدریسی یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # بررسی دسترسی - فقط صاحب یا ادمین
        if request.user.role == 'teacher' and subject.teacher_id != request.user.id:
            return Response(
                {'error': _('شما دسترسی به ویرایش این موضوع ندارید')},
                status=status.HTTP_403_FORBIDDEN
            )
        elif request.user.role not in ['teacher', 'admin']:
            return Response(
                {'error': _('تنها معلمان و ادمین می‌توانند موضوع را ویرایش کنند')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # اگر داده خالی برای teacher تلقی شود (فقط ادمین تغییر می‌دهد)
        data = request.data.copy()
        if 'teacher' in data and request.user.role == 'teacher':
            del data['teacher']
        
        serializer = TeachingSubjectSerializer(subject, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'data': serializer.data,
                    'message': _('موضوع تدریسی با موفقیت ویرایش شد')
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                'error': _('داده‌های نامعتبر'),
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class TeachingSubjectDeleteAPIView(APIView):
    """
    Delete Teaching Subject
    
    حذف موضوع تدریس
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Teaching Subject'],
        summary='Delete Teaching Subject',
        description='حذف موضوع تدریس (صاحب یا ادمین)',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Subject ID')
        ],
        responses={
            204: OpenApiResponse(description="Subject deleted successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Subject not found"),
        }
    )
    def post(self, request, id):
        from classroom.models import TeachingSubject
        
        try:
            subject = TeachingSubject.objects.get(id=id)
        except TeachingSubject.DoesNotExist:
            return Response(
                {'error': _('موضوع تدریسی یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # بررسی دسترسی - فقط صاحب یا ادمین
        if request.user.role == 'teacher' and subject.teacher_id != request.user.id:
            return Response(
                {'error': _('شما دسترسی به حذف این موضوع ندارید')},
                status=status.HTTP_403_FORBIDDEN
            )
        elif request.user.role not in ['teacher', 'admin']:
            return Response(
                {'error': _('تنها معلمان و ادمین می‌توانند موضوع را حذف کنند')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        subject.delete()
        return Response(
            {'message': _('موضوع تدریسی با موفقیت حذف شد')},
            status=status.HTTP_204_NO_CONTENT
        )

# ========== Exercise APIs (آزمون‌ها) ==========

class CreateFieldAPIView(APIView):
    """
    Create Question (Field) API
    
    Create a new question with optional answer options.
    Supports multiple question types:
    - input (تایپی) - Typing/text questions
    - checkbox (چند گزینه‌ای) - Multiple choice questions
    - radioButton (تک گزینه‌ای) - Single choice questions
    
    Only teachers can create questions.
    Requires authentication.
    
    post:
        Create a new question with answer details.
        
        Request body parameters:
        - title: string (required) - Question text/title
        - type: string (required) - Question type: 'input', 'checkbox', or 'radioButton'
        - is_required: integer (optional) - 0 or 1 - Whether answer is required
        - image_path: string (optional) - Path to question image
        - audio_path: string (optional) - Path to question audio
        - video_path: string (optional) - Path to question video
        - guide: string (optional) - Question guide/hint
        - des: string (optional) - Question description
        - sort: integer (optional, default: 0) - Sort order
        - details: array (optional) - Answer options for choice questions
            - title: string - Option text
            - is_correct: integer - 1 if correct, 0 if incorrect, -1 for text
            - image_path: string (optional) - Option image
            - guide: string (optional) - Explanation for this option
            
        Returns:
            201 Created:
                - id: integer - Question ID
                - title: string
                - type: string
                - is_required: integer
                - details: array - Answer options
                - message: string - "Question created successfully"
                
            400 Bad Request - Invalid data
            403 Forbidden - User is not a teacher
    
    Example Request - Multiple Choice:
    ```json
    {
        "title": "What is 2+2?",
        "type": "radioButton",
        "is_required": 1,
        "guide": "Choose the correct answer",
        "details": [
            {
                "title": "3",
                "is_correct": 0
            },
            {
                "title": "4",
                "is_correct": 1
            },
            {
                "title": "5",
                "is_correct": 0
            }
        ]
    }
    ```
    
    Example Request - Typing:
    ```json
    {
        "title": "Write your name",
        "type": "input",
        "is_required": 1,
        "guide": "Enter your full name"
    }
    ```
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Exercise - Questions'],
        summary='Create Question',
        description='Create new question with optional answer options. Only for teachers.',
        request=None,
        responses={
            201: OpenApiResponse(description="Question created successfully"),
            400: OpenApiResponse(description="Invalid data"),
            403: OpenApiResponse(description="Only teachers can create questions"),
        }
    )
    def post(self, request):
        from exercise.models import Field
        from .exercise_serializers import FieldCreateUpdateSerializer
        
        # فقط معلمان می‌توانند سؤال ایجاد کنند
        if request.user.role != 'teacher':
            return Response(
                {'error': _('تنها معلمان می‌توانند سؤال ایجاد کنند')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = FieldCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            field = serializer.save()
            response_serializer = FieldRetrieveSerializer(field)
            return Response({
                'data': response_serializer.data,
                'message': _('سؤال با موفقیت ایجاد شد')
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': _('داده‌های نامعتبر'),
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CreateExamAPIView(APIView):
    """
    Create Exam API
    
    Create an exam (CategoryField) by adding questions to a teaching subject.
    Teachers add one or more questions to their class.
    
    post:
        Create new exam by linking questions to a teaching subject.
        
        Request body parameters:
        - teachingsubject_id: integer (required) - ID of the class/subject
        - questions: array (required) - List of questions to add
            - field_id: integer - Question ID (from create-field endpoint)
            - step: integer - Question step/group number (0, 1, 2, ...)
            - sort: integer - Order within step (0, 1, 2, ...)
            - type: string - Question type (from Field type)
            - is_conditional: boolean (optional) - Is this conditional question
        
        Returns:
            201 Created:
                - id: integer - Exam ID
                - subject: object
                - questions: array - All questions in exam
                - total_questions: integer
                - message: string - "Exam created successfully"
                
            400 Bad Request - Invalid data or non-existent subject
            403 Forbidden - Teacher can only create exam for their own subject
            404 Not Found - Teaching subject not found
    
    Example Request:
    ```json
    {
        "teachingsubject_id": 5,
        "questions": [
            {
                "field_id": 1,
                "step": 0,
                "sort": 0,
                "type": "radioButton"
            },
            {
                "field_id": 2,
                "step": 0,
                "sort": 1,
                "type": "input"
            },
            {
                "field_id": 3,
                "step": 1,
                "sort": 0,
                "type": "checkbox"
            }
        ]
    }
    ```
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Exercise - Exams'],
        summary='Create Exam',
        description='Create new exam by adding questions to a teaching subject',
        request=None,
        responses={
            201: OpenApiResponse(description="Exam created successfully"),
            400: OpenApiResponse(description="Invalid data or non-existent subject"),
            403: OpenApiResponse(description="Can only create exam for own subject"),
            404: OpenApiResponse(description="Teaching subject not found"),
        }
    )
    def post(self, request):
        from exercise.models import CategoryField, Field
        from classroom.models import TeachingSubject
        from .exercise_serializers import ExamSerializer
        
        # فقط معلمان می‌توانند آزمون ایجاد کنند
        if request.user.role != 'teacher':
            return Response(
                {'error': _('تنها معلمان می‌توانند آزمون ایجاد کنند')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        subject_id = request.data.get('teachingsubject_id')
        questions = request.data.get('questions', [])
        
        if not subject_id:
            return Response(
                {'error': _('شناسه موضوع الزامی است')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not questions:
            return Response(
                {'error': _('حداقل یک سؤال الزامی است')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            subject = TeachingSubject.objects.get(id=subject_id)
        except TeachingSubject.DoesNotExist:
            return Response(
                {'error': _('موضوع تدریسی یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # بررسی اینکه معلم صاحب این موضوع است
        if subject.teacher_id != request.user.id:
            return Response(
                {'error': _('شما می‌توانید تنها برای موضوعات خود آزمون ایجاد کنید')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # ایجاد سؤالات برای آزمون
        created_questions = []
        try:
            for question_data in questions:
                field_id = question_data.get('field_id')
                
                try:
                    field = Field.objects.get(id=field_id)
                except Field.DoesNotExist:
                    return Response(
                        {'error': f"سؤال با شناسه {field_id} یافت نشد"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                exam_question = CategoryField.objects.create(
                    teachingsubject=subject,
                    field=field,
                    step=question_data.get('step', 0),
                    sort=question_data.get('sort', 0),
                    type=question_data.get('type', field.type),
                    is_conditional=question_data.get('is_conditional', False)
                )
                created_questions.append(exam_question)
            
            # بازگشت داده‌های آزمون
            exam_questions = CategoryField.objects.filter(teachingsubject=subject).select_related('field')
            
            return Response({
                'data': {
                    'id': subject.id,
                    'subject_id': subject.id,
                    'subject_title': subject.title,
                    'questions': [{
                        'id': q.id,
                        'field_id': q.field_id,
                        'field_title': q.field.title,
                        'type': q.type,
                        'step': q.step,
                        'sort': q.sort,
                        'is_conditional': q.is_conditional,
                        'details': [{
                            'id': d.id,
                            'title': d.title,
                            'is_correct': d.is_correct
                        } for d in q.field.details.all()]
                    } for q in exam_questions],
                    'total_questions': exam_questions.count()
                },
                'message': _('آزمون با موفقیت ایجاد شد')
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': f"خطا: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class GetExamAPIView(APIView):
    """
    Get Exam API
    
    Retrieve complete exam with all questions and options.
    Students and teachers can access their exams.
    
    get:
        Get exam questions and options.
        
        Path parameters:
        - subject_id: integer - Teaching subject (exam) ID
        
        Returns:
            200 OK:
                - id: integer - Exam ID
                - subject_id: integer
                - subject_title: string
                - questions: array - All questions in exam
                    - id: integer
                    - title: string
                    - type: string - input, checkbox, radioButton
                    - guide: string
                    - des: string
                    - details: array - Answer options (for choice questions)
                        - id: integer
                        - title: string
                        - image_path: string
                - total_questions: integer
                
            404 Not Found - Exam/subject not found
            403 Forbidden - User does not have access
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Exercise - Exams'],
        summary='Get Exam Questions',
        description='Retrieve complete exam with all questions and options',
        parameters=[
            OpenApiParameter('subject_id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Teaching subject (exam) ID')
        ],
        responses={
            200: OpenApiResponse(description="Exam questions and options"),
            403: OpenApiResponse(description="User does not have access to this exam"),
            404: OpenApiResponse(description="Exam/subject not found"),
        }
    )
    def get(self, request, subject_id):
        from exercise.models import CategoryField
        from classroom.models import TeachingSubject
        from .exercise_serializers import FieldRetrieveSerializer
        
        try:
            subject = TeachingSubject.objects.get(id=subject_id)
        except TeachingSubject.DoesNotExist:
            return Response(
                {'error': _('موضوع تدریسی یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # بررسی دسترسی
        # معلم تنها می‌تواند موضوع خود را ببیند
        # دانش‌آموز می‌تواند موضوع فعال را ببیند
        if request.user.role == 'teacher' and subject.teacher_id != request.user.id:
            return Response(
                {'error': _('شما دسترسی به این موضوع ندارید')},
                status=status.HTTP_403_FORBIDDEN
            )
        elif request.user.role == 'student' and not subject.is_active:
            return Response(
                {'error': _('این موضوع دسترس پذیر نیست')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت تمام سؤالات آزمون
        exam_questions = CategoryField.objects.filter(
            teachingsubject=subject
        ).select_related('field').order_by('step', 'sort')
        
        questions_data = []
        for eq in exam_questions:
            field = eq.field
            field_data = FieldRetrieveSerializer(field).data
            field_data['exam_question_id'] = eq.id
            field_data['step'] = eq.step
            field_data['sort'] = eq.sort
            questions_data.append(field_data)
        
        return Response({
            'id': subject.id,
            'subject_id': subject.id,
            'subject_title': subject.title,
            'questions': questions_data,
            'total_questions': exam_questions.count()
        }, status=status.HTTP_200_OK)


class SubmitExamAPIView(APIView):
    """
    Submit Exam Answers API
    
    Student submits exam answers and receives score.
    Calculates correctness and generates result.
    
    post:
        Submit exam answers.
        
        Request body parameters:
        - teachingsubject_id: integer (required) - Exam/subject ID
        - answers: array (required) - Student answers
            - field_id: integer - Question ID
            - field_detail_id: integer (optional) - Selected option ID (for choice questions)
            - value: string (optional) - Text answer (for typing questions)
        
        Returns:
            201 Created:
                - id: integer - Attempt/Order ID
                - subject_title: string
                - score: integer - Number of correct answers
                - correct: integer - Count of correct answers
                - incorrect: integer - Count of incorrect answers
                - total_questions: integer
                - percentage: float - Percentage score
                - details: array - Answer details with scoring
                - created_at: datetime
                
            400 Bad Request - Invalid answers or subject not found
            403 Forbidden - User cannot submit exam
            404 Not Found - Subject not found
    
    Example Request:
    ```json
    {
        "teachingsubject_id": 5,
        "answers": [
            {
                "field_id": 1,
                "field_detail_id": 10
            },
            {
                "field_id": 2,
                "value": "My answer text"
            },
            {
                "field_id": 3,
                "field_detail_id": 25
            }
        ]
    }
    ```
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Exercise - Submissions'],
        summary='Submit Exam Answers',
        description='Submit exam answers and receive score',
        request=None,
        responses={
            201: OpenApiResponse(description="Exam answers submitted, score calculated"),
            400: OpenApiResponse(description="Invalid answers or subject not found"),
            403: OpenApiResponse(description="Cannot submit exam"),
            404: OpenApiResponse(description="Subject not found"),
        }
    )
    def post(self, request):
        from classroom.models import TeachingSubject
        from .exercise_serializers import OrderCreateSubmitSerializer, OrderRetrieveSerializer
        
        subject_id = request.data.get('teachingsubject_id')
        answers = request.data.get('answers', [])
        
        if not subject_id or not answers:
            return Response(
                {'error': _('شناسه موضوع و جوابات الزامی هستند')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            subject = TeachingSubject.objects.get(id=subject_id)
        except TeachingSubject.DoesNotExist:
            return Response(
                {'error': _('موضوع تدریسی یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # ایجاد شیء با داده‌های تایید شده
        serializer = OrderCreateSubmitSerializer(
            data={
                'teachingsubject_id': subject_id,
                'answers': answers
            },
            context={'request': request}
        )
        
        if serializer.is_valid():
            order = serializer.save()
            response_serializer = OrderRetrieveSerializer(order)
            
            return Response({
                'data': response_serializer.data,
                'message': _('پاسخ‌ها با موفقیت ثبت شدند')
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': _('داده‌های نامعتبر'),
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class GetExamResultsAPIView(APIView):
    """
    Get Exam Results API
    
    Get all exam attempts and scores for a specific subject or student.
    Teachers see all student results for their subject.
    Students see only their own results.
    
    get:
        Get exam results.
        
        Query parameters:
        - subject_id: integer (optional) - Filter by subject
        - page: integer (optional) - Page number
        - page_size: integer (optional) - Items per page
        
        Returns:
            200 OK:
                - results: array - List of exam attempts
                    - id: integer
                    - subject_title: string
                    - score: integer
                    - correct: integer
                    - incorrect: integer
                    - total_questions: integer
                    - percentage: float
                    - created_at: datetime
                - pagination: object
                
            403 Forbidden - User cannot view these results
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Exercise - Results'],
        summary='Get Exam Results',
        description='Get exam attempts and scores. Teachers see student results, students see own results.',
        parameters=[
            OpenApiParameter('subject_id', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by subject ID'),
            OpenApiParameter('page', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Page number'),
            OpenApiParameter('page_size', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Items per page'),
        ],
        responses={
            200: OpenApiResponse(description="List of exam results"),
            403: OpenApiResponse(description="User cannot view these results"),
        }
    )
    def get(self, request):
        from exercise.models import Order
        from .exercise_serializers import OrderListSerializer
        
        # دانش‌آموز تنها نتایج خود را می‌بیند
        if request.user.role == 'student':
            queryset = Order.objects.filter(user=request.user)
        # معلم نتایج موضوعات خود را می‌بیند
        elif request.user.role == 'teacher':
            from classroom.models import TeachingSubject
            subject_ids = TeachingSubject.objects.filter(teacher=request.user).values_list('id', flat=True)
            queryset = Order.objects.filter(teachingsubject_id__in=subject_ids)
        # ادمین تمام نتایج را می‌بیند
        else:
            queryset = Order.objects.all()
        
        # فیلتر بر اساس موضوع
        subject_id = request.query_params.get('subject_id')
        if subject_id:
            queryset = queryset.filter(teachingsubject_id=subject_id)
        
        # مرتب‌سازی
        queryset = queryset.order_by('-created_at')
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        paginated = queryset[start:end]
        
        serializer = OrderListSerializer(paginated, many=True)
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class GetExamAttemptDetailAPIView(APIView):
    """
    Get Exam Attempt Details API
    
    Get detailed results of a single exam attempt with all answers.
    Shows which answers were correct/incorrect.
    
    get:
        Get complete attempt details.
        
        Path parameters:
        - attempt_id: integer - Exam attempt ID
        
        Returns:
            200 OK:
                - id: integer - Attempt ID
                - user_name: string
                - subject_title: string
                - score: integer
                - correct: integer
                - incorrect: integer
                - details: array - Each answer with its correctness
                    - field_id: integer
                    - field_title: string
                    - student_answer: string or option title
                    - is_correct: boolean
                    - score: integer
                - created_at: datetime
                
            403 Forbidden - User cannot view this attempt
            404 Not Found - Attempt not found
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Exercise - Results'],
        summary='Get Exam Attempt Details',
        description='Get detailed results of a single exam attempt with all answers',
        parameters=[
            OpenApiParameter('attempt_id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Attempt ID')
        ],
        responses={
            200: OpenApiResponse(description="Attempt details with answers and scoring"),
            403: OpenApiResponse(description="User cannot view this attempt"),
            404: OpenApiResponse(description="Attempt not found"),
        }
    )
    def get(self, request, attempt_id):
        from exercise.models import Order
        from .exercise_serializers import OrderRetrieveSerializer
        
        try:
            order = Order.objects.get(id=attempt_id)
        except Order.DoesNotExist:
            return Response(
                {'error': _('تلاش برای امتحان یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # بررسی دسترسی
        if request.user.role == 'student' and order.user_id != request.user.id:
            return Response(
                {'error': _('شما دسترسی به این نتایج ندارید')},
                status=status.HTTP_403_FORBIDDEN
            )
        elif request.user.role == 'teacher':
            if order.teachingsubject.teacher_id != request.user.id:
                return Response(
                    {'error': _('شما دسترسی به این نتایج ندارید')},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = OrderRetrieveSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

