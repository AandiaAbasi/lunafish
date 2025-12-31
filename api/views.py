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
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import boto3
import re
import jdatetime
import datetime as dt
from account.serializers import *
from account.services import *
from account.models import OTP, VerificationToken, ParentProfile
from classroom.models import ClassBooking, StudentTransaction, TeacherAvailability
from exercise.models import Field, FieldDetail, CategoryField, Order, OrderDetail
from .exercise_serializers import (
    FieldCreateUpdateSerializer, FieldRetrieveSerializer,
    CategoryFieldCreateSerializer, CategoryFieldRetrieveSerializer,
    OrderCreateSubmitSerializer, OrderRetrieveSerializer, OrderListSerializer,
    OrderDetailRetrieveSerializer
)
from .classroom_serializers import TeachingSubjectSerializer
from .parent_serializers import (
    ParentLoginSerializer, ParentProfileSerializer, ParentUpdateUsageTimeSerializer,
    ChildClassHistorySerializer, ChildPaymentHistorySerializer
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
        - **introduction_video** (file, optional): Video file for introduction (MP4, AVI, MOV, WebM, FLV, MKV, 3GP, M4V, OGV)
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
    
    **Example Request (form-data):**
    ```
    name: Dr. Sarah Johnson
    qualifications: PhD in Linguistics, TEFL Certified
    languages_taught: English, Spanish, French
    specialization: Business English
    resume_summary: 10+ years experience
    introduction_video: <file> (video file - MP4, AVI, MOV, etc.)
    hourly_rate: 25.50
    experience_years: 12
    available_times: {...}
    profile_photo_path: <file> (image file - JPG, PNG, GIF)
    ```
    
    **Note:** When uploading files, use form-data instead of JSON. The introduction_video field now expects a video file upload instead of a URL.
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
                
                # بررسی تکراری نبودن - اگر موجود باشد skip می‌کنیم
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
        
        # بازگشت پیام - حتی اگر تعداد 0 باشد
        message = _('بازه‌های زمانی با موفقیت ایجاد شدند')
        if created == 0:
            message = _('هیچ بازه زمانی جدیدی اضافه نشد. احتمالاً تمام این بازه‌ها قبلاً ثبت شده بودند.')
        
        # بازیابی و بازگشت بازه‌های موجود
        slots = TeacherAvailability.objects.filter(
            teacher_id=request.user.id,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date', 'start_time')
        
        from .classroom_serializers import TeacherAvailabilitySerializer
        serializer = TeacherAvailabilitySerializer(slots, many=True)
        
        return Response(
            {
                'data': serializer.data,
                'created_count': created,
                'total_count': slots.count(),
                'message': message
            },
            status=status.HTTP_201_CREATED if created > 0 else status.HTTP_200_OK
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
            
            # Handle price - convert to Decimal
            price_str = request.data.get('price')
            if not price_str:
                return Response(
                    {
                        'error': _('قیمت الزامی است'),
                        'details': 'price field is required'
                    },
                    status=400
                )
            price = Decimal(str(price_str))
            
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
                    'details': f'Error: {str(e)}'
                },
                status=400
            )
        except KeyError as e:
            return Response(
                {
                    'error': _('فیلدهای الزامی گم شده است'),
                    'details': f'Missing field: {str(e)}'
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

                # بررسی تکراری نبودن - اگر موجود باشد skip می‌کنیم
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

        # بازگشت پیام - حتی اگر تعداد 0 باشد
        message = _('بازه‌های زمانی با موفقیت ایجاد شدند')
        status_code = status.HTTP_201_CREATED
        
        if created == 0:
            message = _('هیچ بازه زمانی جدیدی اضافه نشد. احتمالاً تمام این بازه‌ها قبلاً ثبت شده بودند.')
            status_code = status.HTTP_200_OK

        return Response({
            'count': created,
            'message': message
        }, status=status_code)


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


# ========== Class Booking APIs (خریدن کلاس) ==========

class CreateClassBookingAPIView(APIView):
    """
    Create Class Booking (Purchase Class) API
    
    خریدن کلاس - دانش‌آموز یک بازه زمانی را رزرو و خریداری می‌کند
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Class Booking'],
        summary='Book/Purchase a Class',
        description='دانش‌آموز یک بازه زمانی از معلم را خریداری می‌کند',
        request=None,
        responses={
            201: OpenApiResponse(description="Class booked successfully"),
            400: OpenApiResponse(description="Invalid data or unavailable slot"),
            403: OpenApiResponse(description="Only students can book classes"),
            404: OpenApiResponse(description="Slot or subject not found"),
        }
    )
    def post(self, request):
        from classroom.models import ClassBooking, TeacherAvailability, TeachingSubject
        from .classroom_serializers import ClassBookingSerializer, CreateClassBookingSerializer
        
        # فقط دانش‌آموزان می‌توانند کلاس خریداری کنند
        if request.user.role != 'student':
            return Response(
                {'error': _('تنها دانش‌آموزان می‌توانند کلاس خریداری کنند')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # تایید داده‌های ورودی
        serializer = CreateClassBookingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': _('داده‌های نامعتبر'),
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        availability_id = serializer.validated_data['availability']
        subject_id = serializer.validated_data['subject']
        discount_code = serializer.validated_data.get('discount_code')
        
        # دریافت بازه زمانی و موضوع
        try:
            availability = TeacherAvailability.objects.get(id=availability_id)
            subject = TeachingSubject.objects.get(id=subject_id)
        except (TeacherAvailability.DoesNotExist, TeachingSubject.DoesNotExist):
            return Response(
                {'error': _('بازه زمانی یا درس یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # ایجاد رزرو کلاس
        try:
            # قیمت نهایی: اگر قیمت تخفیف وجود دارد از آن استفاده شود، وگرنه قیمت اصلی
            final_price = availability.discount_price if availability.discount_price else availability.price
            
            booking = ClassBooking.objects.create(
                availability=availability,
                teacher=availability.teacher,
                student=request.user,
                subject=subject,
                status='reserved',
                price=availability.price,
                discount_amount=0,
                final_price=final_price
            )
            
            # علامت‌گذاری بازه زمانی به عنوان رزرو شده
            availability.is_booked = True
            availability.is_available = False
            availability.save()
            
            # بازگشت داده‌های رزرو
            response_serializer = ClassBookingSerializer(booking)
            
            return Response({
                'data': response_serializer.data,
                'message': _('کلاس با موفقیت خریداری شد')
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': f'خطا: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class StudentBookingsListAPIView(APIView):
    """
    Get My Bookings (Purchased Classes) API
    
    دریافت لیست کلاس‌های خریداری شده توسط دانش‌آموز
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Class Booking'],
        summary='Get My Bookings',
        description='دریافت لیست کلاس‌های خریداری شده',
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Filter by status: reserved, completed, cancelled, no_show'),
            OpenApiParameter('teacher', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by teacher ID'),
        ],
        responses={
            200: OpenApiResponse(description="List of student bookings"),
            403: OpenApiResponse(description="Students can only view their own bookings"),
        }
    )
    def get(self, request, *args, **kwargs):
        from classroom.models import ClassBooking
        from .classroom_serializers import ClassBookingSerializer
        from rest_framework.pagination import PageNumberPagination
        
        # دریافت کتاب‌های دانش‌آموز
        # فقط دانش‌آموزان می‌توانند رزروهای خود را ببینند
        if request.user.role != 'student':
            return Response(
                {'error': _('فقط دانش‌آموزان می‌توانند این endpoint رو استفاده کنند')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        bookings = ClassBooking.objects.filter(student=request.user)
        
        # فیلتر بر اساس وضعیت
        status_filter = request.query_params.get('status')
        if status_filter:
            bookings = bookings.filter(status=status_filter)
        
        # فیلتر بر اساس معلم
        teacher_id = request.query_params.get('teacher')
        if teacher_id:
            bookings = bookings.filter(teacher_id=teacher_id)
        
        # مرتب‌سازی
        bookings = bookings.select_related('availability', 'subject', 'teacher').order_by('-created_at')
        
        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 20))
        paginated_bookings = paginator.paginate_queryset(bookings, request)
        
        serializer = ClassBookingSerializer(paginated_bookings, many=True)
        return paginator.get_paginated_response(serializer.data)


class TeacherBookingsListAPIView(APIView):
    """
    Get Students Who Booked My Classes API
    
    دریافت لیست دانش‌آموزانی که از کلاس‌های معلم خریداری کردند
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Class Booking'],
        summary='Get My Bookings',
        description='دریافت لیست دانش‌آموزانی که از کلاس‌های معلم خریداری کردند',
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Filter by status: reserved, completed, cancelled, no_show'),
            OpenApiParameter('subject', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by subject ID'),
        ],
        responses={
            200: OpenApiResponse(description="List of bookings for teacher classes"),
            403: OpenApiResponse(description="Teachers can only view bookings for their classes"),
        }
    )
    def get(self, request, *args, **kwargs):
        from classroom.models import ClassBooking, TeachingSubject
        from .classroom_serializers import ClassBookingSerializer
        from rest_framework.pagination import PageNumberPagination
        
        # معلم تنها می‌تواند رزروهای کلاس‌های خود را ببیند
        if request.user.role != 'teacher':
            return Response(
                {'error': _('معلمان می‌توانند تنها رزروهای خود را ببینند')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت کلاس‌های معلم
        subjects = TeachingSubject.objects.filter(teacher=request.user).values_list('id', flat=True)
        bookings = ClassBooking.objects.filter(subject_id__in=subjects)
        
        # فیلتر بر اساس وضعیت
        status_filter = request.query_params.get('status')
        if status_filter:
            bookings = bookings.filter(status=status_filter)
        
        # فیلتر بر اساس موضوع
        subject_id = request.query_params.get('subject')
        if subject_id:
            bookings = bookings.filter(subject_id=subject_id)
        
        # مرتب‌سازی
        bookings = bookings.select_related('availability', 'subject', 'student').order_by('-created_at')
        
        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 20))
        paginated_bookings = paginator.paginate_queryset(bookings, request)
        
        serializer = ClassBookingSerializer(paginated_bookings, many=True)
        return paginator.get_paginated_response(serializer.data)


class UpdateBookingStatusAPIView(APIView):
    """
    Update Booking Status API
    
    تغییر وضعیت رزرو - معلم می‌تواند وضعیت را تکمیل/لغو کند
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Class Booking'],
        summary='Update Booking Status',
        description='تغییر وضعیت رزرو (فقط معلم)',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Booking ID')
        ],
        request=None,
        responses={
            200: OpenApiResponse(description="Booking status updated"),
            400: OpenApiResponse(description="Invalid status"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Booking not found"),
        }
    )
    def patch(self, request, id):
        from classroom.models import ClassBooking
        from .classroom_serializers import ClassBookingSerializer
        
        try:
            booking = ClassBooking.objects.get(id=id)
        except ClassBooking.DoesNotExist:
            return Response(
                {'error': _('رزرو یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # فقط معلم می‌تواند وضعیت را تغییر دهد
        if request.user.role != 'teacher' or booking.teacher_id != request.user.id:
            return Response(
                {'error': _('شما دسترسی ندارید')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        valid_statuses = ['reserved', 'completed', 'cancelled', 'no_show']
        
        if not new_status or new_status not in valid_statuses:
            return Response(
                {'error': _('وضعیت نامعتبر است')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = new_status
        booking.save()
        
        serializer = ClassBookingSerializer(booking)
        return Response({
            'data': serializer.data,
            'message': _('وضعیت رزرو با موفقیت به‌روزرسانی شد')
        }, status=status.HTTP_200_OK)


class CancelBookingAPIView(APIView):
    """
    Cancel Booking API
    
    لغو رزرو - دانش‌آموز می‌تواند رزرو را لغو کند
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Class Booking'],
        summary='Cancel Booking',
        description='لغو رزرو کلاس (فقط دانش‌آموز)',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Booking ID')
        ],
        responses={
            200: OpenApiResponse(description="Booking cancelled"),
            403: OpenApiResponse(description="Permission denied or booking cannot be cancelled"),
            404: OpenApiResponse(description="Booking not found"),
        }
    )
    def post(self, request, id):
        from classroom.models import ClassBooking
        from .classroom_serializers import ClassBookingSerializer
        
        try:
            booking = ClassBooking.objects.get(id=id)
        except ClassBooking.DoesNotExist:
            return Response(
                {'error': _('رزرو یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # فقط دانش‌آموز می‌تواند رزرو خود را لغو کند
        if request.user.role != 'student' or booking.student_id != request.user.id:
            return Response(
                {'error': _('شما دسترسی ندارید')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # تنها رزروهای "reserved" می‌توانند لغو شوند
        if booking.status != 'reserved':
            return Response(
                {'error': _('این رزرو نمی‌تواند لغو شود')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # علامت‌گذاری به عنوان لغو شده
        booking.status = 'cancelled'
        booking.save()
        
        # آزاد کردن بازه زمانی
        booking.availability.is_booked = False
        booking.availability.is_available = True
        booking.availability.save()
        
        serializer = ClassBookingSerializer(booking)
        return Response({
            'data': serializer.data,
            'message': _('رزرو با موفقیت لغو شد')
        }, status=status.HTTP_200_OK)


# ========== Teaching Subject APIs (کلاس‌های معلم) ==========

class TeachingSubjectListAPIView(APIView):
    """
    List Teaching Subjects
    
    دریافت لیست موضوعات تدریس
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get_queryset(self):
        """Filter by teacher if requested"""
        from classroom.models import TeachingSubject
        
        if self.request.user.role == 'teacher':
            # معلم تنها می‌تواند موضوعات خود را ببیند
            return TeachingSubject.objects.filter(teacher=self.request.user).order_by('-created_at')
        elif self.request.user.role == 'admin':
            # ادمین تمام موضوعات را می‌بیند
            return TeachingSubject.objects.all().order_by('-created_at')
        else:
            # دانش‌آموز تنها موضوعات فعال را می‌بیند
            return TeachingSubject.objects.filter(is_active=True).order_by('-created_at')
    
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
        
        # فقط معلمان می‌توانند موضوع ایجاد کنند
        if request.user.role != 'teacher':
            return Response(
                {'error': _('تنها معلمان می‌توانند موضوع تدریس ایجاد کنند')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Build data dict without copying (to avoid pickling file objects)
        data = dict(request.data)
        data['teacher'] = request.user.id
        
        serializer = TeachingSubjectSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeachingSubjectCreateAPIView(APIView):
    """
    Create Teaching Subject
    ایجاد موضوع تدریس جدید (فقط برای معلمان)
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        tags=['Teaching Subject'],
        summary='Create Teaching Subject',
        description='ایجاد موضوع تدریس جدید (فقط برای معلمان)',
        responses={
            201: OpenApiResponse(description="Subject created successfully"),
            400: OpenApiResponse(description="Invalid data"),
            403: OpenApiResponse(description="Only teachers can create subjects"),
        }
    )
    def post(self, request):

        # فقط معلم
        if request.user.role != 'teacher':
            return Response(
                {'error': _('تنها معلمان می‌توانند موضوع تدریس ایجاد کنند')},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TeachingSubjectSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save(teacher=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(
            {
                'message': _('Invalid data provided'),
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


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
    
    Supports file removal with explicit boolean flags:
    - remove_cover_image=true: removes the cover_image file
    - remove_demo_video=true: removes the demo_video file
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    @extend_schema(
        tags=['Teaching Subject'],
        summary='Update Teaching Subject',
        description='ویرایش موضوع تدریس (صاحب موضوع یا ادمین)',
        parameters=[
            OpenApiParameter(
                'id',
                OpenApiTypes.INT,
                required=True,
                location=OpenApiParameter.PATH,
                description='Subject ID'
            )
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
        from .classroom_serializers import TeachingSubjectUpdateSerializer, TeachingSubjectSerializer

        # ---------- get subject ----------
        try:
            subject = TeachingSubject.objects.get(id=id)
        except TeachingSubject.DoesNotExist:
            return Response(
                {'error': _('موضوع تدریسی یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )

        # ---------- permission ----------
        if request.user.role == 'teacher':
            if subject.teacher_id != request.user.id:
                return Response(
                    {'error': _('شما دسترسی به ویرایش این موضوع ندارید')},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif request.user.role != 'admin':
            return Response(
                {'error': _('تنها معلمان یا ادمین می‌توانند موضوع را ویرایش کنند')},
                status=status.HTTP_403_FORBIDDEN
            )

        # ---------- build mutable data safely ----------
        # جلوگیری از TypeError با ایجاد dict جدید
        # از request.data مستقیماً استفاده می‌کنیم (شامل فایل‌ها)
        # فقط فیلدهای مورد نیاز رو استخراج می‌کنیم
        data = {}
        
        # تمام فیلدهای form data رو کپی کن (شامل فایل‌ها)
        for key in request.data.keys():
            data[key] = request.data.get(key)
        
        # teacher فقط توسط admin قابل تغییر است
        if request.user.role != 'admin':
            data.pop('teacher', None)

        # ---------- fix boolean ----------
        if 'is_active' in data and isinstance(data.get('is_active'), str):
            data['is_active'] = data['is_active'].lower() in ['true', '1', 'yes']
        
        # ---------- fix removal flags ----------
        for field in ['remove_cover_image', 'remove_demo_video']:
            if field in data and isinstance(data.get(field), str):
                data[field] = data[field].lower() in ['true', '1', 'yes']

        # ---------- fix integers ----------
        for field in ['min_age', 'max_age']:
            if field in data and data.get(field) not in [None, '']:
                try:
                    data[field] = int(data[field])
                except (TypeError, ValueError):
                    pass

        # ---------- fix level (FormData array issue) ----------
        if 'level' in data and isinstance(data.get('level'), (list, tuple)):
            data['level'] = data['level'][0]

        # ---------- serializer ----------
        serializer = TeachingSubjectUpdateSerializer(
            subject,
            data=data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            # Return the full subject data using the read serializer
            read_serializer = TeachingSubjectSerializer(subject)
            return Response(
                {
                    'data': read_serializer.data,
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
    def post(self, request, subject_id=None):
        from classroom.models import TeachingSubject
        from .exercise_serializers import OrderCreateSubmitSerializer, OrderRetrieveSerializer
        
        # اگر subject_id از URL بیاید، استفاده کن؛ وگرنه از request.data بگیر
        if subject_id is None:
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


# ============= Teacher List and Detail APIs =============

class TeacherListAPIView(generics.ListAPIView):
    """
    API: List all teachers with basic information
    
    Description:
        Returns a paginated list of all verified teachers with their basic
        information for discovery and browsing.
    
    Permissions:
        - Allow any user (public access)
    
    Query Parameters:
        - page: int (default=1) - Page number for pagination
        - page_size: int (default=10) - Number of teachers per page
    
    Returns:
        200 OK:
            - count: int - Total number of teachers
            - next: string or null - URL to next page
            - previous: string or null - URL to previous page
            - results: array of teacher objects
                - id: integer
                - name: string
                - qualifications: string
                - languages_taught: string
                - profile_photo_path: string (image URL or null)
                - hourly_rate: decimal (price per hour)
                - resume_summary: string (truncated to 200 chars)
                - experience_years: integer
                - is_teacher_verified: boolean
                - created_at: string (ISO datetime)
    """
    permission_classes = [AllowAny]
    pagination_class = None  # Will be set dynamically
    
    def get_queryset(self):
        """Get all verified teachers, ordered by creation date"""
        return User.objects.filter(role='teacher', is_teacher_verified=True).order_by('-created_at')
    
    def get_serializer_class(self):
        from .classroom_serializers import TeacherListSerializer
        return TeacherListSerializer
    
    def list(self, request, *args, **kwargs):
        """Override list to add pagination"""
        from rest_framework.pagination import PageNumberPagination
        
        queryset = self.filter_queryset(self.get_queryset())
        
        # Set up pagination
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get('page_size', 10)
        
        try:
            paginator.page_size = int(paginator.page_size)
            if paginator.page_size < 1:
                paginator.page_size = 10
        except (ValueError, TypeError):
            paginator.page_size = 10
        
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TeacherDetailAPIView(APIView):
    """
    API: Get detailed teacher profile
    
    Description:
        Returns complete teacher profile including qualifications, teaching
        subjects, and available time slots.
    
    Permissions:
        - Allow any user (public access)
    
    Path Parameters:
        - id: integer (required) - Teacher ID
    
    Returns:
        200 OK:
            - id: integer
            - name: string
            - email: string (email address)
            - phone: string (phone number)
            - qualifications: string
            - languages_taught: string
            - specialization: string
            - experience_years: integer
            - is_teacher_verified: boolean
            - resume_summary: string (full resume)
            - introduction_video: string (video file URL or null)
            - bio: string
            - profile_photo_path: string (image URL or null)
            - hourly_rate: decimal (price per hour)
            - teaching_subjects: array of teaching subject objects
                - id: integer
                - title: string
                - description: string
                - level: string (beginner/intermediate/advanced)
                - level_display: string (translated level)
                - cover_image: string (image URL or null)
                - demo_video: string (file URL or null)
                - min_age: integer or null
                - max_age: integer or null
                - is_active: boolean
            - availability_slots: array of availability objects
                - id: integer
                - date: string (Jalali date format YYYY/MM/DD)
                - start_time: string (HH:MM format)
                - end_time: string (HH:MM format)
                - price: decimal
                - discount_price: decimal or null
                - is_available: boolean
                - is_booked: boolean
                - is_expired: boolean
                - notes: string
        
        404 Not Found:
            - error: string - "معلم یافت نشد"
    """
    permission_classes = [AllowAny]
    
    def get(self, request, id):
        """Get teacher detail with all related data"""
        try:
            teacher = User.objects.get(id=id, role='teacher', is_teacher_verified=True)
        except User.DoesNotExist:
            return Response(
                {'error': _('معلم یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from .classroom_serializers import TeacherDetailSerializer
        serializer = TeacherDetailSerializer(teacher)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ========== Parent Portal APIs ==========

class ParentLoginAPIView(APIView):
    """
    والدین می‌توانند با شماره تماس، ایمیل یا شناسه دانش‌آموز + رمز والد وارد شوند
    
    post:
        Login with student identifier (ID, phone, or email) and parent password
        
        Request body:
        - identifier: string (required) - شناسه دانش‌آموز (شناسه، شماره تماس یا ایمیل)
        - parent_password: string (required) - رمز والدین
        
        Returns:
            200 OK:
                - parent_token: string - Token for parent
                - parent_id: integer
                - parent_name: string
                - student_id: integer
                - student_name: string
                - can_view_class_history: boolean
                - can_view_payments: boolean
                - can_select_teacher: boolean
                - can_set_usage_time: boolean
                
            400 Bad Request:
                - Student not found
                - Parent profile not found
                - Invalid password
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Parent Portal'],
        summary='Parent Login',
        description='والدین می‌توانند با شماره تماس، ایمیل یا شناسه دانش‌آموز + رمز والد وارد شوند',
        request=inline_serializer(
            name='ParentLoginRequest',
            fields={
                'identifier': serializers.CharField(help_text='شناسه دانش‌آموز (شناسه، شماره تماس یا ایمیل)'),
                'parent_password': serializers.CharField(help_text='رمز والدین', style={'input_type': 'password'})
            }
        ),
        responses={
            200: inline_serializer(
                name='ParentLoginResponse',
                fields={
                    'parent_token': serializers.CharField(),
                    'parent_id': serializers.IntegerField(),
                    'parent_name': serializers.CharField(),
                    'student_id': serializers.IntegerField(),
                    'student_name': serializers.CharField(),
                    'can_view_class_history': serializers.BooleanField(),
                    'can_view_payments': serializers.BooleanField(),
                    'can_select_teacher': serializers.BooleanField(),
                    'can_set_usage_time': serializers.BooleanField()
                }
            )
        }
    )
    def post(self, request):
        """Parent login"""
        from .parent_serializers import ParentLoginSerializer
        
        serializer = ParentLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        parent = serializer.validated_data['parent']
        
        # Update last login
        parent.last_login_at = timezone.now()
        parent.save()
        
        # Generate token
        import secrets
        parent_token = secrets.token_urlsafe(32)
        
        return Response({
            'parent_token': parent_token,
            'parent_id': parent.id,
            'parent_name': parent.parent_name,
            'student_id': parent.student.id,
            'student_name': parent.student.name or parent.student.username,
            'can_view_class_history': parent.can_view_class_history,
            'can_view_payments': parent.can_view_payments,
            'can_select_teacher': parent.can_select_teacher,
            'can_set_usage_time': parent.can_set_usage_time
        }, status=status.HTTP_200_OK)


class ParentDashboardAPIView(APIView):
    """
    داشبورد والد - نمایش خلاصه‌ای از وضعیت کودک
    
    get:
        Get parent dashboard overview for child
        
        Query parameters:
        - child_id: integer (optional) - اگر والد بیش از یک فرزند دارد
        
        Returns:
            200 OK:
                - child: object
                    - id, name, username, birth_date, gender, bio
                    - profile_photo_path, selected_avatar_image
                - total_classes: integer
                - completed_classes: integer
                - cancelled_classes: integer
                - no_show_classes: integer
                - upcoming_classes: integer
                - total_spent: decimal
                - total_pending_payment: decimal
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Parent Portal'],
        summary='Parent Dashboard',
        description='داشبورد والد - نمایش خلاصه وضعیت کودک'
    )
    def get(self, request):
        """Get parent dashboard"""
        # Get parent profile
        try:
            # والد می‌تواند از parent_id query param یا user's parent profile استفاده کند
            student_id = request.query_params.get('child_id')
            
            if student_id:
                # والد می‌خواهد داشبورد یک کودک خاص را ببیند
                try:
                    student = User.objects.get(id=student_id, role='user')
                    parent = ParentProfile.objects.get(student=student, is_active=True)
                except (User.DoesNotExist, ParentProfile.DoesNotExist):
                    return Response(
                        {'error': _('Student not found')},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # اگر parent profile موجود نیست
                return Response(
                    {'error': _('Parent profile not found')},
                    status=status.HTTP_404_NOT_FOUND
                )
        except ParentProfile.DoesNotExist:
            return Response(
                {'error': _('Parent profile not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get class statistics
        from classroom.models import ClassBooking
        student = parent.student
        
        total_classes = ClassBooking.objects.filter(student=student).count()
        completed_classes = ClassBooking.objects.filter(student=student, status='completed').count()
        cancelled_classes = ClassBooking.objects.filter(student=student, status='cancelled').count()
        no_show_classes = ClassBooking.objects.filter(student=student, status='no_show').count()
        
        # Upcoming classes (reserved and not expired)
        from classroom.models import TeacherAvailability
        upcoming_classes = ClassBooking.objects.filter(
            student=student,
            status='reserved',
            availability__is_expired=False
        ).count()
        
        # Get payment statistics
        from classroom.models import StudentTransaction
        total_spent = StudentTransaction.objects.filter(
            student=student,
            transaction_type='class_payment',
            status='completed'
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0
        
        total_pending_payment = StudentTransaction.objects.filter(
            student=student,
            transaction_type='class_payment',
            status='pending'
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0
        
        # Build response
        from .parent_serializers import ChildProfileForParentSerializer
        child_serializer = ChildProfileForParentSerializer(student)
        
        response_data = {
            'child': child_serializer.data,
            'total_classes': total_classes,
            'completed_classes': completed_classes,
            'cancelled_classes': cancelled_classes,
            'no_show_classes': no_show_classes,
            'upcoming_classes': upcoming_classes,
            'total_spent': str(total_spent),
            'total_pending_payment': str(total_pending_payment)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class ChildClassHistoryAPIView(generics.ListAPIView):
    """
    تاریخچه کلاس‌های کودک
    والد می‌تواند تاریخچه کلاس‌های کودک را ببیند
    
    get:
        Get child's class history
        
        Query parameters:
        - child_id: integer (optional)
        - status: string (optional) - reserved, completed, cancelled, no_show
        - ordering: string (optional) - default: -created_at (newest first)
        
        Returns:
            200 OK: List of classes with pagination
                - id, class_date, start_time, end_time
                - teacher_name, teacher_id
                - subject_title, subject_id
                - status, price, discount_amount, final_price
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Parent Portal'],
        summary='Child Class History',
        description='تاریخچه کلاس‌های کودک'
    )
    def get_queryset(self):
        """Get child's classes"""
        student_id = self.request.query_params.get('child_id')
        
        if not student_id:
            return ClassBooking.objects.none()
        
        try:
            student = User.objects.get(id=student_id, role='user')
        except User.DoesNotExist:
            return ClassBooking.objects.none()
        
        queryset = ClassBooking.objects.filter(student=student).select_related(
            'teacher', 'subject', 'availability'
        ).order_by('-created_at')
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    serializer_class = ChildClassHistorySerializer


class ChildPaymentHistoryAPIView(generics.ListAPIView):
    """
    ریز پرداخت‌های کودک
    والد می‌تواند ریز پرداخت‌های کودک را مشاهده کند
    
    get:
        Get child's payment history
        
        Query parameters:
        - child_id: integer (optional)
        - transaction_type: string (optional) - class_payment, refund
        - status: string (optional) - pending, completed, failed, refunded
        - ordering: string (optional) - default: -created_at
        
        Returns:
            200 OK: List of transactions with pagination
                - id, transaction_type, amount
                - booking_id, class_title, teacher_name
                - description, status, payment_date
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Parent Portal'],
        summary='Child Payment History',
        description='ریز پرداخت‌های کودک'
    )
    def get_queryset(self):
        """Get child's transactions"""
        student_id = self.request.query_params.get('child_id')
        
        if not student_id:
            return StudentTransaction.objects.none()
        
        try:
            student = User.objects.get(id=student_id, role='user')
        except User.DoesNotExist:
            return StudentTransaction.objects.none()
        
        queryset = StudentTransaction.objects.filter(student=student).select_related(
            'booking', 'booking__teacher', 'booking__subject'
        ).order_by('-created_at')
        
        # Filter by type and status if provided
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        trans_status = self.request.query_params.get('status')
        if trans_status:
            queryset = queryset.filter(status=trans_status)
        
        return queryset
    
    serializer_class = ChildPaymentHistorySerializer


class ChildPaymentSummaryAPIView(APIView):
    """
    خلاصه وضعیت مالی کودک
    والد می‌تواند مجموع پرداخت‌ها و وضعیت مالی را ببیند
    
    get:
        Get payment summary
        
        Query parameters:
        - child_id: integer (optional)
        
        Returns:
            200 OK:
                - total_paid: decimal
                - total_pending: decimal
                - total_refunded: decimal
                - total_failed: decimal
                - transaction_count: integer
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Parent Portal'],
        summary='Payment Summary',
        description='خلاصه وضعیت مالی کودک'
    )
    def get(self, request):
        """Get payment summary"""
        student_id = request.query_params.get('child_id')
        
        if not student_id:
            return Response(
                {'error': _('Child ID is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student = User.objects.get(id=student_id, role='user')
        except User.DoesNotExist:
            return Response(
                {'error': _('Student not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from classroom.models import StudentTransaction
        from django.db.models import Sum
        
        transactions = StudentTransaction.objects.filter(student=student)
        
        total_paid = transactions.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        total_pending = transactions.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
        total_refunded = transactions.filter(status='refunded').aggregate(Sum('amount'))['amount__sum'] or 0
        total_failed = transactions.filter(status='failed').aggregate(Sum('amount'))['amount__sum'] or 0
        transaction_count = transactions.count()
        
        return Response({
            'total_paid': str(total_paid),
            'total_pending': str(total_pending),
            'total_refunded': str(total_refunded),
            'total_failed': str(total_failed),
            'transaction_count': transaction_count
        }, status=status.HTTP_200_OK)


class ParentUpdateUsageTimeAPIView(APIView):
    """
    به‌روزرسانی محدودیت زمان استفاده کودک
    والد می‌تواند محدودیت زمان روزانه و بازه زمانی مجاز را تعیین کند
    
    post:
        Update usage time restrictions
        
        Request body:
        - daily_usage_limit_minutes: integer (optional) - حداکثر دقایق روزانه (0-1440)
        - allowed_start_time: time (optional) - شروع بازه مجاز (HH:MM)
        - allowed_end_time: time (optional) - پایان بازه مجاز (HH:MM)
        
        Returns:
            200 OK:
                - id, parent_name, student_id
                - daily_usage_limit_minutes
                - allowed_start_time, allowed_end_time
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Parent Portal'],
        summary='Update App Usage Time',
        description='به‌روزرسانی محدودیت زمان استفاده کودک'
    )
    def post(self, request):
        """Update usage time"""
        student_id = request.data.get('child_id')
        
        if not student_id:
            return Response(
                {'error': _('Child ID is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student = User.objects.get(id=student_id, role='user')
            parent = ParentProfile.objects.get(student=student, is_active=True)
        except (User.DoesNotExist, ParentProfile.DoesNotExist):
            return Response(
                {'error': _('Student or parent not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission
        if not parent.can_set_usage_time:
            return Response(
                {'error': _('You do not have permission to set usage time')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from .parent_serializers import ParentUpdateUsageTimeSerializer
        serializer = ParentUpdateUsageTimeSerializer(parent, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ParentProfileAPIView(APIView):
    """
    نمایش اطلاعات والد و مجوزهایش
    
    get:
        Get parent profile information
        
        Returns:
            200 OK:
                - id, parent_name, phone, email
                - student_id, student_name
                - can_view_class_history, can_view_payments
                - can_select_teacher, can_set_usage_time
                - is_active, last_login_at
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Parent Portal'],
        summary='Parent Profile',
        description='نمایش اطلاعات والد'
    )
    def get(self, request):
        """Get parent profile"""
        student_id = request.query_params.get('child_id')
        
        if not student_id:
            return Response(
                {'error': _('Child ID is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student = User.objects.get(id=student_id, role='user')
            parent = ParentProfile.objects.get(student=student, is_active=True)
        except (User.DoesNotExist, ParentProfile.DoesNotExist):
            return Response(
                {'error': _('Student or parent not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from .parent_serializers import ParentProfileSerializer
        serializer = ParentProfileSerializer(parent)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ===== Attendance API =====
class AttendanceAPIView(APIView):
    """
    ثبت و بروزرسانی حضور و غیاب دانش‌آموز در کلاس‌ها
    
    post:
        Mark attendance for a student in a class
        
        URL: /api/attendance/<booking_id>/
        
        Request body:
            - student_id: integer
            - status: string ('present' or 'absent')
        
        Returns:
            200 OK:
                - student_id: integer
                - booking_id: integer
                - status: string
                - created: boolean (True if new, False if updated)
            
            400 Bad Request:
                - Invalid student_id
                - Invalid status
                - Booking not found
                - Student not found
            
            404 Not Found:
                - Booking not found
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Attendance'],
        summary='Mark Attendance',
        description='ثبت یا بروزرسانی حضور و غیاب دانش‌آموز',
        request=inline_serializer(
            name='AttendanceRequest',
            fields={
                'student_id': serializers.IntegerField(help_text='شناسه دانش‌آموز'),
                'status': serializers.ChoiceField(choices=['present', 'absent'], help_text='وضعیت (حاضر یا غایب)')
            }
        ),
        responses={
            200: inline_serializer(
                name='AttendanceResponse',
                fields={
                    'student_id': serializers.IntegerField(),
                    'booking_id': serializers.IntegerField(),
                    'status': serializers.CharField(),
                    'created': serializers.BooleanField()
                }
            )
        }
    )
    def post(self, request, booking_id):
        """Mark attendance"""
        from .classroom_serializers import AttendanceSerializer
        from classroom.models import Attendance
        
        # دریافت student_id و status
        student_id = request.data.get('student_id')
        status_value = request.data.get('status')
        
        # بررسی داده‌های ورودی
        if not student_id or not status_value:
            return Response(
                {'error': _('student_id and status are required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if status_value not in ['present', 'absent']:
            return Response(
                {'error': _('status must be "present" or "absent"')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # بررسی وجود کلاس
        try:
            booking = ClassBooking.objects.get(id=booking_id)
        except ClassBooking.DoesNotExist:
            return Response(
                {'error': _('Booking not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # بررسی وجود دانش‌آموز
        try:
            student = User.objects.get(id=student_id, role='user')
        except User.DoesNotExist:
            return Response(
                {'error': _('Student not found')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ثبت یا بروزرسانی حضور و غیاب
        attendance, created = Attendance.objects.update_or_create(
            booking=booking,
            student=student,
            defaults={'status': status_value}
        )
        
        return Response({
            'student_id': attendance.student.id,
            'booking_id': attendance.booking.id,
            'status': attendance.status,
            'created': created
        }, status=status.HTTP_200_OK)


# ===== Support Message Views =====
class SupportMessageAPIView(APIView):
    """API View for Support Messages"""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    @extend_schema(
        summary=_("Send Support Message"),
        description=_("Send a message to support team with optional file attachments"),
        request=inline_serializer(
            name='SupportMessageCreateRequest',
            fields={
                'teacher_id': serializers.IntegerField(),
                'sender_id': serializers.IntegerField(),
                'message_text': serializers.CharField(required=False, allow_blank=True),
                'attachments': serializers.ListField(child=serializers.FileField(), required=False)
            }
        ),
        responses={
            201: inline_serializer(
                name='SupportMessageCreateResponse',
                fields={
                    'id': serializers.IntegerField(),
                    'teacher_id': serializers.IntegerField(),
                    'sender_id': serializers.IntegerField(),
                    'sender_name': serializers.CharField(),
                    'message_text': serializers.CharField(),
                    'status': serializers.CharField(),
                    'created_at': serializers.DateTimeField(),
                    'attachments': serializers.ListField(child=serializers.DictField())
                }
            ),
            400: inline_serializer(
                name='ErrorResponse',
                fields={'error': serializers.CharField()}
            ),
        }
    )
    def post(self, request):
        """ارسال پیام به تیم پشتیبانی"""
        from classroom.models import SupportMessage, SupportMessageAttachment
        from account.models import User
        
        try:
            teacher_id = request.data.get('teacher_id')
            sender_id = request.data.get('sender_id')
            message_text = request.data.get('message_text', '').strip()
            
            # بررسی معلم یا ادمین (گیرنده پیام)
            try:
                teacher = User.objects.get(id=teacher_id, role__in=['teacher', 'admin'])
            except User.DoesNotExist:
                return Response(
                    {'error': _("Recipient not found")},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # بررسی فرستنده (معلم یا Admin)
            try:
                sender = User.objects.get(id=sender_id, role__in=['teacher', 'admin'])
            except User.DoesNotExist:
                return Response(
                    {'error': _("Sender not found")},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # حداقل یک پیام یا فایل باید وجود داشته باشد
            files = request.FILES.getlist('attachments')
            if not message_text and not files:
                return Response(
                    {'error': _("Message text or attachment is required")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ایجاد پیام
            support_message = SupportMessage.objects.create(
                teacher=teacher,
                sender=sender,
                message_text=message_text if message_text else None,
                status='sent'
            )
            
            # اضافه کردن فایل‌های پیوست
            for file in files:
                SupportMessageAttachment.objects.create(
                    message=support_message,
                    file=file
                )
            
            # دریافت فایل‌های پیوست
            attachments_data = []
            for attachment in support_message.attachments.all():
                attachments_data.append({
                    'id': attachment.id,
                    'file_url': request.build_absolute_uri(attachment.file.url),
                    'file_name': attachment.file.name.split('/')[-1]
                })
            
            return Response({
                'id': support_message.id,
                'teacher_id': teacher.id,
                'sender_id': sender.id,
                'sender_name': sender.get_full_name() or sender.username,
                'message_text': support_message.message_text,
                'status': support_message.status,
                'created_at': support_message.created_at,
                'attachments': attachments_data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary=_("List Support Messages"),
        description=_("Get list of support messages for a teacher"),
        parameters=[
            OpenApiParameter(
                'teacher_id',
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description=_("Teacher ID to filter messages")
            ),
            OpenApiParameter(
                'status',
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description=_("Message status: sent or read")
            ),
            OpenApiParameter(
                'page',
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description=_("Page number")
            ),
        ],
        responses={
            200: inline_serializer(
                name='SupportMessageListResponse',
                fields={
                    'count': serializers.IntegerField(),
                    'next': serializers.CharField(allow_null=True),
                    'previous': serializers.CharField(allow_null=True),
                    'results': serializers.ListField(child=serializers.DictField())
                }
            ),
        }
    )
    def get(self, request):
        """دریافت لیست پیام‌های پشتیبانی"""
        from classroom.models import SupportMessage
        
        teacher_id = request.query_params.get('teacher_id')
        status_filter = request.query_params.get('status')
        
        # فیلتر کردن پیام‌ها
        messages = SupportMessage.objects.all()
        
        if teacher_id:
            messages = messages.filter(teacher_id=teacher_id)
        
        if status_filter in ['sent', 'read']:
            messages = messages.filter(status=status_filter)
        
        # ترتیب‌دهی
        messages = messages.order_by('-created_at')
        
        # صفحه‌بندی
        paginator = Paginator(messages, 10)
        page_number = request.query_params.get('page', 1)
        
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # تبدیل به سریالایزر
        messages_data = []
        for msg in page_obj.object_list:
            attachments_data = []
            for attachment in msg.attachments.all():
                attachments_data.append({
                    'id': attachment.id,
                    'file_url': request.build_absolute_uri(attachment.file.url),
                    'file_name': attachment.file.name.split('/')[-1]
                })
            
            messages_data.append({
                'id': msg.id,
                'teacher_id': msg.teacher.id,
                'sender_id': msg.sender.id if msg.sender else None,
                'sender_name': msg.sender.get_full_name() or msg.sender.username if msg.sender else None,
                'message_text': msg.message_text,
                'status': msg.status,
                'created_at': msg.created_at,
                'read_at': msg.read_at,
                'attachments': attachments_data
            })
        
        return Response({
            'count': paginator.count,
            'next': f"/api/support-messages/?page={page_number + 1}" if page_obj.has_next() else None,
            'previous': f"/api/support-messages/?page={page_number - 1}" if page_obj.has_previous() else None,
            'results': messages_data
        }, status=status.HTTP_200_OK)


class SupportMessageDetailAPIView(APIView):
    """API View for Support Message Details and Actions"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary=_("Mark Message as Read"),
        description=_("Mark a support message as read"),
        responses={
            200: inline_serializer(
                name='MarkAsReadResponse',
                fields={
                    'id': serializers.IntegerField(),
                    'status': serializers.CharField(),
                    'read_at': serializers.DateTimeField()
                }
            ),
        }
    )
    def patch(self, request, message_id):
        """علامت‌گذاری پیام به‌عنوان خوانده‌شده"""
        from classroom.models import SupportMessage
        
        try:
            message = SupportMessage.objects.get(id=message_id)
            message.mark_as_read()
            
            return Response({
                'id': message.id,
                'status': message.status,
                'read_at': message.read_at
            }, status=status.HTTP_200_OK)
        
        except SupportMessage.DoesNotExist:
            return Response(
                {'error': _("Message not found")},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, message_id):
        """حذف پیام پشتیبانی"""
        from classroom.models import SupportMessage
        
        try:
            message = SupportMessage.objects.get(id=message_id)
            message.delete()
            
            return Response(
                {'message': _("Message deleted successfully")},
                status=status.HTTP_204_NO_CONTENT
            )
        
        except SupportMessage.DoesNotExist:
            return Response(
                {'error': _("Message not found")},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TeacherConversationsAPIView(APIView):
    """API View for grouped teacher conversations in support messages"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all teachers with their support message conversations"""
        from classroom.models import SupportMessage
        from django.db.models import Count, Max, Q
        
        try:
            conversations = SupportMessage.objects.values('teacher_id').annotate(
                teacher_name=models.F('teacher__name'),
                teacher_username=models.F('teacher__username'),
                message_count=Count('id'),
                unread_count=Count('id', filter=Q(status='sent')),
                last_message_date=Max('created_at')
            ).order_by('-last_message_date')
            
            results = []
            for conv in conversations:
                results.append({
                    'teacher_id': conv['teacher_id'],
                    'teacher_name': conv['teacher_name'] or conv['teacher_username'],
                    'message_count': conv['message_count'],
                    'unread_count': conv['unread_count'],
                    'last_message_date': conv['last_message_date']
                })
            
            return Response({
                'results': results,
                'total': len(results)
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TeacherConversationDetailAPIView(APIView):
    """API View for getting messages from a specific teacher conversation"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, teacher_id):
        """Get all messages for a specific teacher"""
        from classroom.models import SupportMessage
        from account.models import User
        
        try:
            # دریافت تمام پیام‌های بین این معلم و ادمین (بدون محدودیت role)
            messages = SupportMessage.objects.filter(
                teacher_id=teacher_id
            ).select_related('teacher', 'sender').order_by('created_at')
            
            # بررسی اینکه معلم وجود دارد
            if not messages.exists():
                try:
                    teacher = User.objects.get(id=teacher_id)
                except User.DoesNotExist:
                    return Response(
                        {'error': _("Teacher not found")},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            results = []
            teacher_name = None
            for msg in messages:
                teacher_name = msg.teacher.name or msg.teacher.username
                results.append({
                    'id': msg.id,
                    'teacher_id': msg.teacher_id,
                    'teacher_name': teacher_name,
                    'sender_id': msg.sender_id,
                    'sender_name': msg.sender.name or msg.sender.username if msg.sender else None,
                    'message_text': msg.message_text,
                    'status': msg.status,
                    'created_at': msg.created_at,
                    'created_at_display': msg.created_at_display(),
                    'read_at': msg.read_at,
                    'attachments': [
                        {
                            'id': att.id,
                            'file': att.file.url if att.file else None,
                            'name': att.file.name if att.file else None
                        }
                        for att in msg.attachments.all()
                    ]
                })
            
            # اگر پیامی نیست، حداقل نام معلم را برگردان
            if not teacher_name:
                try:
                    teacher = User.objects.get(id=teacher_id)
                    teacher_name = teacher.name or teacher.username
                except:
                    teacher_name = f"Teacher {teacher_id}"
            
            return Response({
                'results': results,
                'total': len(results),
                'teacher_name': teacher_name
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class AttendanceListAPIView(APIView):
    """
    دریافت لیست حضور و غیاب برای یک جلسه (کلاس)
    
    get:
        Get attendance list for a specific class booking
        
        URL: /api/attendance/<booking_id>/list/
        
        Returns:
            200 OK:
                - List of attendance records
                - Each record: {student_id, student_name, status}
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Attendance'],
        summary='Get Session Attendance List',
        description='دریافت لیست حضور و غیاب برای یک جلسه',
        responses={
            200: inline_serializer(
                name='AttendanceListResponse',
                fields={
                    'results': serializers.ListField(
                        child=inline_serializer(
                            name='AttendanceRecord',
                            fields={
                                'student_id': serializers.IntegerField(),
                                'student_name': serializers.CharField(),
                                'status': serializers.CharField()
                            }
                        )
                    ),
                    'total': serializers.IntegerField(),
                    'present_count': serializers.IntegerField(),
                    'absent_count': serializers.IntegerField()
                }
            )
        }
    )
    def get(self, request, booking_id):
        """Get attendance list for a session"""
        from classroom.models import Attendance
        
        # بررسی وجود کلاس
        try:
            booking = ClassBooking.objects.get(id=booking_id)
        except ClassBooking.DoesNotExist:
            return Response(
                {'error': _('Booking not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # دریافت همه رکوردهای حضور و غیاب برای این جلسه
        attendances = Attendance.objects.filter(booking=booking).select_related('student')
        
        # ساخت لیست پاسخ
        results = []
        for attendance in attendances:
            results.append({
                'student_id': attendance.student.id,
                'student_name': attendance.student.name or attendance.student.username,
                'status': attendance.status
            })
        
        # محاسبه آمار
        total = attendances.count()
        present_count = attendances.filter(status='present').count()
        absent_count = attendances.filter(status='absent').count()
        
        return Response({
            'results': results,
            'total': total,
            'present_count': present_count,
            'absent_count': absent_count
        }, status=status.HTTP_200_OK)


# ========== Financial System APIs ==========

class TeacherWalletDetailAPIView(APIView):
    """
    Get Teacher Wallet Details API
    
    Retrieve complete wallet information for authenticated teacher.
    Teachers see only their own wallet. Admins can view any teacher's wallet.
    Requires authentication.
    
    get:
        Get wallet details with balance information.
        
        Returns:
            200 OK:
                - id: integer - Wallet ID
                - teacher: integer - Teacher user ID
                - teacher_name: string - Teacher's full name
                - balance: decimal - Total available balance
                - available_balance: decimal - Balance ready to withdraw
                - pending_balance: decimal - Balance waiting for confirmation
                - total_earned: decimal - Total income earned
                - total_withdrawn: decimal - Total amount withdrawn
                - bank_name: string - Bank name (optional)
                - account_number: string - Bank account number (optional)
                - iban: string - IBAN (optional)
                - card_number: string - Bank card number (optional)
                - account_holder_name: string - Account holder name (optional)
                - minimum_settlement_amount: decimal - Minimum withdrawal amount
                - is_verified: boolean - Is bank info verified
                - verified_at: datetime - When bank info was verified
                - created_at: datetime
                - updated_at: datetime
                
            403 Forbidden - User is not a teacher or trying to access others' wallet
            404 Not Found - Wallet not found
    
    Example GET Request:
    ```
    GET /api/wallet/
    Authorization: Bearer <teacher_token>
    ```
    
    Example GET Response:
    ```json
    {
        "id": 1,
        "teacher": 42,
        "teacher_name": "علی محمدی",
        "balance": "150000.00",
        "available_balance": "100000.00",
        "pending_balance": "50000.00",
        "total_earned": "500000.00",
        "total_withdrawn": "350000.00",
        "bank_name": "بانک ملی",
        "account_number": "1234567890",
        "iban": "IR123456789",
        "card_number": "6037691234567890",
        "account_holder_name": "علی محمدی",
        "minimum_settlement_amount": "50000.00",
        "is_verified": true,
        "verified_at": "2024-12-15T10:30:00Z",
        "created_at": "2024-01-01T08:00:00Z",
        "updated_at": "2024-12-20T15:45:00Z"
    }
    ```
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Financial - Wallet'],
        summary='Get Teacher Wallet Details',
        description='Get complete wallet information including balance and bank details',
        responses={
            200: OpenApiResponse(description="Wallet details retrieved successfully"),
            403: OpenApiResponse(description="Cannot access this wallet"),
            404: OpenApiResponse(description="Wallet not found"),
        }
    )
    def get(self, request):
        from classroom.models import TeacherWallet
        from .classroom_serializers import TeacherWalletSerializer
        
        # فقط معلمان و ادمین
        if request.user.role not in ['teacher', 'admin']:
            return Response({
                'error': _('فقط معلمان می‌توانند کیف پول خود را ببینند')
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # اگر معلم باشد، کیف پول خود را ببیند
            if request.user.role == 'teacher':
                wallet = TeacherWallet.objects.get(teacher=request.user)
            else:
                # ادمین می‌تواند teacher_id از query param دریافت کند
                teacher_id = request.query_params.get('teacher_id')
                if not teacher_id:
                    return Response({
                        'error': _('teacher_id الزامی است')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                wallet = TeacherWallet.objects.get(teacher_id=teacher_id)
        
        except TeacherWallet.DoesNotExist:
            return Response({
                'error': _('کیف پول یافت نشد')
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TeacherWalletSerializer(wallet)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WithdrawalRequestListAPIView(APIView):
    """
    Get Withdrawal Requests List API
    
    List withdrawal requests with optional filters.
    Teachers see only their own requests. Admins see all requests.
    Requires authentication.
    
    get:
        Get list of withdrawal requests with pagination.
        
        Query parameters:
        - status: string (optional) - Filter by status: pending, processing, completed, failed, cancelled
        - teacher_id: integer (optional, admin only) - Filter by teacher
        - date_from: string (optional) - Start date in YYYY-MM-DD format
        - date_to: string (optional) - End date in YYYY-MM-DD format
        - page: integer (optional, default: 1) - Page number
        - page_size: integer (optional, default: 20) - Items per page
        
        Returns:
            200 OK:
                - count: integer - Total number of requests
                - next: string - URL to next page (or null)
                - previous: string - URL to previous page (or null)
                - results: array - List of withdrawal requests
                    - id: integer
                    - teacher_id: integer
                    - teacher_name: string
                    - amount: decimal
                    - status: string
                    - status_display: string (Farsi)
                    - payment_method: string
                    - payment_method_display: string
                    - account_info: object - Bank details
                    - transaction_id: string - Payment gateway transaction ID
                    - notes: string
                    - admin_notes: string
                    - created_at: datetime
                    - updated_at: datetime
                    - completed_at: datetime (if completed)
                    
            403 Forbidden - User cannot view these requests
    
    Example GET Request:
    ```
    GET /api/withdrawal-requests/?status=pending&page=1&page_size=20
    Authorization: Bearer <teacher_token>
    ```
    
    Example GET Response:
    ```json
    {
        "count": 5,
        "next": "/api/withdrawal-requests/?page=2",
        "previous": null,
        "results": [
            {
                "id": 1,
                "teacher_id": 42,
                "teacher_name": "علی محمدی",
                "amount": "500000.00",
                "status": "pending",
                "status_display": "در انتظار تأیید",
                "payment_method": "bank_transfer",
                "payment_method_display": "انتقال بانکی",
                "account_info": {
                    "bank_name": "بانک ملی",
                    "account_number": "1234567890",
                    "iban": "IR123456789"
                },
                "transaction_id": null,
                "notes": "تقاضای کسب درآمد",
                "admin_notes": null,
                "created_at": "2024-12-15T10:00:00Z",
                "updated_at": "2024-12-15T10:00:00Z",
                "completed_at": null
            }
        ]
    }
    ```
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Financial - Withdrawal'],
        summary='List Withdrawal Requests',
        description='Get list of withdrawal requests with optional filters and pagination',
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Filter by status: pending, processing, completed, failed, cancelled'),
            OpenApiParameter('teacher_id', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by teacher (admin only)'),
            OpenApiParameter('date_from', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Start date (YYYY-MM-DD)'),
            OpenApiParameter('date_to', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='End date (YYYY-MM-DD)'),
            OpenApiParameter('page', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Page number'),
            OpenApiParameter('page_size', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Items per page'),
        ],
        responses={
            200: OpenApiResponse(description="List of withdrawal requests"),
            403: OpenApiResponse(description="User cannot view these requests"),
        }
    )
    def get(self, request):
        from classroom.models import WithdrawalRequest
        from .classroom_serializers import WithdrawalRequestSerializer
        from rest_framework.pagination import PageNumberPagination
        
        # فقط معلمان و ادمین
        if request.user.role not in ['teacher', 'admin']:
            return Response({
                'error': _('فقط معلمان و مدیران می‌توانند این endpoint را استفاده کنند')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # فیلتر بر اساس role
        if request.user.role == 'teacher':
            queryset = WithdrawalRequest.objects.filter(teacher=request.user)
        else:
            # ادمین
            queryset = WithdrawalRequest.objects.all()
        
        # فیلتر بر اساس معلم (فقط ادمین)
        teacher_id = request.query_params.get('teacher_id')
        if teacher_id and request.user.role == 'admin':
            queryset = queryset.filter(teacher_id=teacher_id)
        
        # فیلتر بر اساس وضعیت
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # فیلتر بر اساس بازه تاریخی
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        # مرتب‌سازی
        queryset = queryset.order_by('-created_at')
        
        # صفحه‌بندی
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 20))
        
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = WithdrawalRequestSerializer(paginated_queryset, many=True)
        
        return paginator.get_paginated_response(serializer.data)


class WithdrawalRequestCreateAPIView(APIView):
    """
    Create Withdrawal Request API
    
    Teacher requests to withdraw money from their wallet.
    Validates that available_balance >= amount and minimum_settlement_amount is met.
    Requires authentication (teacher only).
    
    post:
        Create new withdrawal request.
        
        Request body parameters:
        - amount: decimal (required) - Amount to withdraw
        - payment_method: string (required) - Payment method: bank_transfer, card_transfer
        - account_info: object (optional) - Bank details (overrides default if provided)
            - bank_name: string - Bank name
            - account_number: string - Account number
            - iban: string - IBAN
            - card_number: string - Card number
        - notes: string (optional) - Request notes/description
        
        Returns:
            201 Created:
                - id: integer - Withdrawal request ID
                - teacher_id: integer
                - amount: decimal
                - payment_method: string
                - payment_method_display: string
                - account_info: object
                - status: string (default: pending)
                - created_at: datetime
                - message: string - "درخواست تسویه حساب ایجاد شد"
                
            400 Bad Request:
                - Invalid amount (must be positive)
                - Insufficient balance
                - Amount below minimum settlement
                - Invalid payment method
                - Account info missing
                
            403 Forbidden - User is not a teacher
            404 Not Found - Wallet not found
    
    Example POST Request:
    ```json
    {
        "amount": "100000.00",
        "payment_method": "bank_transfer",
        "notes": "تقاضای کسب درآمد از دوره‌های آنلاین"
    }
    ```
    
    Example POST Response:
    ```json
    {
        "id": 5,
        "teacher_id": 42,
        "amount": "100000.00",
        "payment_method": "bank_transfer",
        "payment_method_display": "انتقال بانکی",
        "account_info": {
            "bank_name": "بانک ملی",
            "account_number": "1234567890",
            "iban": "IR123456789"
        },
        "status": "pending",
        "notes": "تقاضای کسب درآمد",
        "created_at": "2024-12-20T12:00:00Z",
        "message": "درخواست تسویه حساب ایجاد شد"
    }
    ```
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Financial - Withdrawal'],
        summary='Create Withdrawal Request',
        description='Create new withdrawal request from teacher wallet',
        request=inline_serializer(
            name='CreateWithdrawalRequest',
            fields={
                'amount': serializers.DecimalField(max_digits=12, decimal_places=2, help_text='مبلغ درخواستی'),
                'payment_method': serializers.ChoiceField(choices=['bank_transfer', 'card_transfer'], help_text='روش پرداخت'),
                'notes': serializers.CharField(required=False, allow_blank=True, help_text='یادداشت‌های اضافی'),
                'account_info': serializers.JSONField(required=False, help_text='اطلاعات حساب بانکی'),
            }
        ),
        responses={
            201: OpenApiResponse(description="Withdrawal request created successfully"),
            400: OpenApiResponse(description="Invalid amount, insufficient balance, or invalid data"),
            403: OpenApiResponse(description="User is not a teacher"),
            404: OpenApiResponse(description="Wallet not found"),
        }
    )
    def post(self, request):
        from classroom.models import TeacherWallet, WithdrawalRequest
        from .classroom_serializers import WithdrawalRequestSerializer
        from decimal import Decimal
        from django.db import transaction
        
        # فقط معلمان
        if request.user.role != 'teacher':
            return Response({
                'error': _('فقط معلمان می‌توانند درخواست تسویه حساب کنند')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # دریافت داده‌ها
        amount_str = request.data.get('amount')
        payment_method = request.data.get('payment_method')
        notes = request.data.get('notes', '').strip()
        account_info = request.data.get('account_info')
        
        # اعتبارسنجی
        if not amount_str or not payment_method:
            return Response({
                'error': _('مبلغ و روش پرداخت الزامی هستند')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # تبدیل مبلغ
        try:
            amount = Decimal(str(amount_str))
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError):
            return Response({
                'error': _('مبلغ نامعتبر است')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # دریافت کیف پول معلم
        try:
            wallet = TeacherWallet.objects.get(teacher=request.user)
        except TeacherWallet.DoesNotExist:
            return Response({
                'error': _('کیف پول یافت نشد')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # بررسی موجودی
        if wallet.available_balance < amount:
            return Response({
                'error': _('موجودی کافی نیست'),
                'available': str(wallet.available_balance)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # بررسی حداقل مبلغ
        if amount < wallet.minimum_settlement_amount:
            return Response({
                'error': _('مبلغ از حداقل درخواست (%(min)s) کمتر است') % {
                    'min': wallet.minimum_settlement_amount
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # بررسی روش پرداخت
        if payment_method not in ['bank_transfer', 'card_transfer']:
            return Response({
                'error': _('روش پرداخت نامعتبر است')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # استفاده از account_info ارائه شده یا اطلاعات بانکی کیف پول
        if not account_info:
            account_info = {
                'bank_name': wallet.bank_name,
                'account_number': wallet.account_number,
                'iban': wallet.iban,
                'card_number': wallet.card_number,
                'account_holder_name': wallet.account_holder_name
            }
            # فیلتر کردن مقادیر خالی
            account_info = {k: v for k, v in account_info.items() if v}
        
        if not account_info:
            return Response({
                'error': _('اطلاعات حساب بانکی مورد نیاز است')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ایجاد درخواست تسویه حساب با استفاده از transaction.atomic
        try:
            with transaction.atomic():
                # قفل کردن کیف پول برای جلوگیری از تغییرات همزمان
                wallet = TeacherWallet.objects.select_for_update().get(teacher=request.user)
                
                # بررسی دوباره موجودی (در صورت تغییر توسط درخواست دیگری)
                if wallet.available_balance < amount:
                    raise ValueError(_('موجودی کافی نیست'))
                
                # کاهش available_balance
                wallet.available_balance -= amount
                wallet.save()
                
                # ایجاد درخواست
                withdrawal = WithdrawalRequest.objects.create(
                    teacher=request.user,
                    amount=amount,
                    payment_method=payment_method,
                    account_info=account_info,
                    notes=notes,
                    status='pending'
                )
                
                # ثبت تراکنش
                from classroom.models import WalletTransaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='withdrawal',
                    amount=amount,
                    balance_before=wallet.available_balance + amount,
                    balance_after=wallet.available_balance,
                    withdrawal=withdrawal,
                    description=f'درخواست تسویه حساب - {payment_method}'
                )
            
            serializer = WithdrawalRequestSerializer(withdrawal)
            return Response({
                'data': serializer.data,
                'message': _('درخواست تسویه حساب ایجاد شد')
            }, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'خطا: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletTransactionListAPIView(APIView):
    """
    Get Wallet Transaction History API
    
    List all transactions for a teacher's wallet with optional filters.
    Teachers see only their own transactions. Admins see all transactions.
    Requires authentication.
    
    get:
        Get list of wallet transactions with pagination.
        
        Query parameters:
        - transaction_type: string (optional) - Filter by type: revenue, confirmation, withdrawal, refund, adjustment, bonus, penalty
        - date_from: string (optional) - Start date in YYYY-MM-DD format
        - date_to: string (optional) - End date in YYYY-MM-DD format
        - teacher_id: integer (optional, admin only) - Filter by teacher
        - page: integer (optional, default: 1) - Page number
        - page_size: integer (optional, default: 20) - Items per page
        
        Returns:
            200 OK:
                - count: integer - Total number of transactions
                - next: string - URL to next page (or null)
                - previous: string - URL to previous page (or null)
                - results: array - List of transactions
                    - id: integer
                    - wallet_id: integer
                    - wallet_teacher_name: string
                    - transaction_type: string
                    - transaction_type_display: string (Farsi)
                    - amount: decimal
                    - balance_before: decimal
                    - balance_after: decimal
                    - description: string
                    - admin_note: string
                    - revenue_id: integer (if related to revenue)
                    - withdrawal_id: integer (if related to withdrawal)
                    - created_at: datetime
                    
            403 Forbidden - User cannot view these transactions
    
    Example GET Request:
    ```
    GET /api/transactions/?transaction_type=revenue&date_from=2024-01-01&page=1
    Authorization: Bearer <teacher_token>
    ```
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Financial - Transactions'],
        summary='List Wallet Transactions',
        description='Get wallet transaction history with optional filters and pagination',
        parameters=[
            OpenApiParameter('transaction_type', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Filter by type: revenue, confirmation, withdrawal, refund, adjustment, bonus, penalty'),
            OpenApiParameter('date_from', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Start date (YYYY-MM-DD)'),
            OpenApiParameter('date_to', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='End date (YYYY-MM-DD)'),
            OpenApiParameter('teacher_id', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by teacher (admin only)'),
            OpenApiParameter('page', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Page number'),
            OpenApiParameter('page_size', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Items per page'),
        ],
        responses={
            200: OpenApiResponse(description="List of wallet transactions"),
            403: OpenApiResponse(description="User cannot view these transactions"),
        }
    )
    def get(self, request):
        from classroom.models import WalletTransaction
        from .classroom_serializers import WalletTransactionSerializer
        from rest_framework.pagination import PageNumberPagination
        
        # فقط معلمان و ادمین
        if request.user.role not in ['teacher', 'admin']:
            return Response({
                'error': _('فقط معلمان و مدیران می‌توانند این endpoint را استفاده کنند')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # فیلتر بر اساس role
        if request.user.role == 'teacher':
            queryset = WalletTransaction.objects.filter(wallet__teacher=request.user)
        else:
            # ادمین
            queryset = WalletTransaction.objects.all()
        
        # فیلتر بر اساس معلم (فقط ادمین)
        teacher_id = request.query_params.get('teacher_id')
        if teacher_id and request.user.role == 'admin':
            queryset = queryset.filter(wallet__teacher_id=teacher_id)
        
        # فیلتر بر اساس نوع تراکنش
        transaction_type = request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # فیلتر بر اساس بازه تاریخی
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        # مرتب‌سازی
        queryset = queryset.order_by('-created_at').select_related('wallet', 'revenue', 'withdrawal')
        
        # صفحه‌بندی
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 20))
        
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = WalletTransactionSerializer(paginated_queryset, many=True)
        
        return paginator.get_paginated_response(serializer.data)


class FinancialSummaryAPIView(APIView):
    """
    Get Financial Summary API
    
    Get summary of financial data for a teacher or admin overview.
    Teachers see their own summary. Admins can request any teacher's summary.
    Requires authentication.
    
    get:
        Get financial summary statistics.
        
        Query parameters:
        - teacher_id: integer (optional, admin only) - Get summary for specific teacher
        - date_from: string (optional) - Period start date (YYYY-MM-DD)
        - date_to: string (optional) - Period end date (YYYY-MM-DD)
        
        Returns:
            200 OK:
                - wallet: object
                    - total_balance: decimal - Current total balance
                    - available_balance: decimal - Amount ready to withdraw
                    - pending_balance: decimal - Amount in confirmation process
                    - total_earned: decimal - Cumulative lifetime earnings
                    - total_withdrawn: decimal - Cumulative lifetime withdrawals
                    - is_verified: boolean - Is bank info verified
                    
                - statistics: object
                    - total_bookings: integer - Total class bookings
                    - completed_bookings: integer - Completed classes
                    - pending_bookings: integer - Awaiting completion
                    - revenue_items: integer - Number of revenue transactions
                    - average_price_per_class: decimal - Average class price
                    
                - transactions: object
                    - revenue_count: integer - Number of class revenues
                    - withdrawal_count: integer - Number of withdrawals
                    - refund_count: integer - Number of refunds
                    - total_transactions: integer
                    
                - period: object (if date filters applied)
                    - start_date: string
                    - end_date: string
                    - earned_this_period: decimal
                    - withdrawn_this_period: decimal
                    
            403 Forbidden - User cannot view this summary
            404 Not Found - Teacher or wallet not found
    
    Example GET Request:
    ```
    GET /api/financial-summary/?teacher_id=42&date_from=2024-01-01&date_to=2024-12-31
    Authorization: Bearer <admin_token>
    ```
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Financial - Summary'],
        summary='Get Financial Summary',
        description='Get financial summary statistics for teacher or admin',
        parameters=[
            OpenApiParameter('teacher_id', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Teacher ID (admin only)'),
            OpenApiParameter('date_from', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Period start date (YYYY-MM-DD)'),
            OpenApiParameter('date_to', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Period end date (YYYY-MM-DD)'),
        ],
        responses={
            200: OpenApiResponse(description="Financial summary retrieved successfully"),
            403: OpenApiResponse(description="User cannot view this summary"),
            404: OpenApiResponse(description="Teacher or wallet not found"),
        }
    )
    def get(self, request):
        from classroom.models import (
            TeacherWallet, ClassBooking, ClassRevenue,
            WithdrawalRequest, WalletTransaction
        )
        from django.db.models import Count, Sum, Avg
        from datetime import datetime
        
        # فقط معلمان و ادمین
        if request.user.role not in ['teacher', 'admin']:
            return Response({
                'error': _('فقط معلمان و مدیران می‌توانند این endpoint را استفاده کنند')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # تعیین معلم
        if request.user.role == 'teacher':
            teacher = request.user
        else:
            # ادمین
            teacher_id = request.query_params.get('teacher_id')
            if not teacher_id:
                return Response({
                    'error': _('teacher_id الزامی است')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                teacher = User.objects.get(id=teacher_id, role='teacher')
            except User.DoesNotExist:
                return Response({
                    'error': _('معلم یافت نشد')
                }, status=status.HTTP_404_NOT_FOUND)
        
        # دریافت کیف پول
        try:
            wallet = TeacherWallet.objects.get(teacher=teacher)
        except TeacherWallet.DoesNotExist:
            return Response({
                'error': _('کیف پول یافت نشد')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # داده‌های بازه تاریخی
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')
        
        date_from = None
        date_to = None
        
        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # جمع‌آوری اطلاعات کلی
        wallet_data = {
            'total_balance': str(wallet.balance),
            'available_balance': str(wallet.available_balance),
            'pending_balance': str(wallet.pending_balance),
            'total_earned': str(wallet.total_earned),
            'total_withdrawn': str(wallet.total_withdrawn),
            'is_verified': wallet.is_verified
        }
        
        # آمار کلاس‌ها
        bookings = ClassBooking.objects.filter(teacher=teacher)
        
        if date_from:
            bookings = bookings.filter(created_at__date__gte=date_from)
        if date_to:
            bookings = bookings.filter(created_at__date__lte=date_to)
        
        total_bookings = bookings.count()
        completed_bookings = bookings.filter(status='completed').count()
        pending_bookings = bookings.filter(status='reserved').count()
        
        avg_price = bookings.aggregate(Avg('final_price'))['final_price__avg'] or 0
        
        statistics_data = {
            'total_bookings': total_bookings,
            'completed_bookings': completed_bookings,
            'pending_bookings': pending_bookings,
            'revenue_items': ClassRevenue.objects.filter(teacher=teacher).count(),
            'average_price_per_class': str(avg_price)
        }
        
        # آمار تراکنش‌ها
        transactions = WalletTransaction.objects.filter(wallet=wallet)
        
        if date_from:
            transactions = transactions.filter(created_at__date__gte=date_from)
        if date_to:
            transactions = transactions.filter(created_at__date__lte=date_to)
        
        revenue_count = transactions.filter(transaction_type='revenue').count()
        withdrawal_count = transactions.filter(transaction_type='withdrawal').count()
        refund_count = transactions.filter(transaction_type='refund').count()
        
        transactions_data = {
            'revenue_count': revenue_count,
            'withdrawal_count': withdrawal_count,
            'refund_count': refund_count,
            'total_transactions': transactions.count()
        }
        
        # داده‌های بازه‌ای (اگر تاریخ مشخص شده)
        period_data = None
        
        if date_from or date_to:
            revenues = ClassRevenue.objects.filter(teacher=teacher)
            if date_from:
                revenues = revenues.filter(created_at__date__gte=date_from)
            if date_to:
                revenues = revenues.filter(created_at__date__lte=date_to)
            
            earned = revenues.aggregate(Sum('teacher_share'))['teacher_share__sum'] or 0
            
            withdrawals = WithdrawalRequest.objects.filter(teacher=teacher, status='completed')
            if date_from:
                withdrawals = withdrawals.filter(updated_at__date__gte=date_from)
            if date_to:
                withdrawals = withdrawals.filter(updated_at__date__lte=date_to)
            
            withdrawn = withdrawals.aggregate(Sum('amount'))['amount__sum'] or 0
            
            period_data = {
                'start_date': date_from_str,
                'end_date': date_to_str,
                'earned_this_period': str(earned),
                'withdrawn_this_period': str(withdrawn)
            }
        
        return Response({
            'wallet': wallet_data,
            'statistics': statistics_data,
            'transactions': transactions_data,
            'period': period_data
        }, status=status.HTTP_200_OK)


class WithdrawalApproveAPIView(APIView):
    """
    Approve Withdrawal Request API (Admin Only)
    
    Admin approves a pending withdrawal request and updates transaction status.
    Only admins can approve withdrawal requests.
    Requires authentication with admin role.
    
    post:
        Approve pending withdrawal request.
        
        Path parameters:
        - request_id: integer (required) - Withdrawal request ID
        
        Request body parameters:
        - transaction_id: string (optional) - Payment gateway transaction ID
        - notes: string (optional) - Admin notes about approval
        
        Returns:
            200 OK:
                - id: integer - Request ID
                - teacher_id: integer
                - amount: decimal
                - status: string (set to: processing or completed)
                - transaction_id: string - Payment transaction ID
                - approved_at: datetime
                - admin_notes: string
                - message: string - "درخواست تسویه حساب تأیید شد"
                
            403 Forbidden - User is not admin
            404 Not Found - Withdrawal request not found
            400 Bad Request - Request is not in pending status
    
    Example POST Request:
    ```json
    {
        "transaction_id": "TXN123456789",
        "notes": "تأیید شده و در حال پردازش"
    }
    ```
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Financial - Admin'],
        summary='Approve Withdrawal Request',
        description='Admin approves withdrawal request (admin only)',
        parameters=[
            OpenApiParameter('request_id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Request ID')
        ],
        responses={
            200: OpenApiResponse(description="Withdrawal request approved successfully"),
            400: OpenApiResponse(description="Request is not in pending status"),
            403: OpenApiResponse(description="User is not an admin"),
            404: OpenApiResponse(description="Withdrawal request not found"),
        }
    )
    def post(self, request, request_id):
        from classroom.models import WithdrawalRequest
        from .classroom_serializers import WithdrawalRequestSerializer
        from django.db import transaction
        
        # فقط ادمین
        if request.user.role != 'admin':
            return Response({
                'error': _('فقط مدیران می‌توانند درخواست‌ها را تأیید کنند')
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            withdrawal = WithdrawalRequest.objects.get(id=request_id)
        except WithdrawalRequest.DoesNotExist:
            return Response({
                'error': _('درخواست تسویه حساب یافت نشد')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # بررسی وضعیت
        if withdrawal.status != 'pending':
            return Response({
                'error': _('تنها درخواست‌های در انتظار تأیید را می‌توان تأیید کرد')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # دریافت داده‌ها
        transaction_id = request.data.get('transaction_id')
        notes = request.data.get('notes', '').strip()
        
        # آپدیت درخواست
        try:
            with transaction.atomic():
                withdrawal.status = 'processing'  # یا completed
                if transaction_id:
                    withdrawal.transaction_id = transaction_id
                if notes:
                    withdrawal.admin_notes = notes
                withdrawal.save()
        
        except Exception as e:
            return Response({
                'error': f'خطا: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = WithdrawalRequestSerializer(withdrawal)
        return Response({
            'data': serializer.data,
            'message': _('درخواست تسویه حساب تأیید شد')
        }, status=status.HTTP_200_OK)


class StudentTransactionListAPIView(APIView):
    """
    Get Student Transaction History API
    
    List student transactions (class payments, refunds, etc.).
    Students see only their own transactions. Admins see all transactions.
    Requires authentication.
    
    get:
        Get list of student transactions with pagination.
        
        Query parameters:
        - transaction_type: string (optional) - Filter by type: class_payment, refund
        - status: string (optional) - Filter by status: pending, completed, failed, refunded
        - student_id: integer (optional, admin only) - Filter by student
        - date_from: string (optional) - Start date in YYYY-MM-DD format
        - date_to: string (optional) - End date in YYYY-MM-DD format
        - page: integer (optional, default: 1) - Page number
        - page_size: integer (optional, default: 20) - Items per page
        
        Returns:
            200 OK:
                - count: integer - Total number of transactions
                - next: string - URL to next page (or null)
                - previous: string - URL to previous page (or null)
                - results: array - List of transactions
                    - id: integer
                    - student_id: integer
                    - student_name: string
                    - transaction_type: string
                    - transaction_type_display: string (Farsi)
                    - amount: decimal
                    - booking_id: integer
                    - class_title: string
                    - teacher_name: string
                    - status: string
                    - status_display: string (Farsi)
                    - description: string
                    - payment_date: datetime
                    - created_at: datetime
                    
            403 Forbidden - User cannot view these transactions
    
    Example GET Request:
    ```
    GET /api/student-transactions/?status=completed&page=1
    Authorization: Bearer <student_token>
    ```
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Financial - Student'],
        summary='List Student Transactions',
        description='Get student transaction history with optional filters and pagination',
        parameters=[
            OpenApiParameter('transaction_type', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Filter by type: class_payment, refund'),
            OpenApiParameter('status', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Filter by status: pending, completed, failed, refunded'),
            OpenApiParameter('student_id', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by student (admin only)'),
            OpenApiParameter('date_from', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Start date (YYYY-MM-DD)'),
            OpenApiParameter('date_to', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='End date (YYYY-MM-DD)'),
            OpenApiParameter('page', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Page number'),
            OpenApiParameter('page_size', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Items per page'),
        ],
        responses={
            200: OpenApiResponse(description="List of student transactions"),
            403: OpenApiResponse(description="User cannot view these transactions"),
        }
    )
    def get(self, request):
        from classroom.models import StudentTransaction
        from .classroom_serializers import StudentTransactionSerializer
        from rest_framework.pagination import PageNumberPagination
        
        # فقط دانش‌آموزان و ادمین
        if request.user.role not in ['user', 'admin']:
            return Response({
                'error': _('فقط دانش‌آموزان و مدیران می‌توانند این endpoint را استفاده کنند')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # فیلتر بر اساس role
        if request.user.role == 'user':
            queryset = StudentTransaction.objects.filter(student=request.user)
        else:
            # ادمین
            queryset = StudentTransaction.objects.all()
        
        # فیلتر بر اساس دانش‌آموز (فقط ادمین)
        student_id = request.query_params.get('student_id')
        if student_id and request.user.role == 'admin':
            queryset = queryset.filter(student_id=student_id)
        
        # فیلتر بر اساس نوع تراکنش
        transaction_type = request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # فیلتر بر اساس وضعیت
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # فیلتر بر اساس بازه تاریخی
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        # مرتب‌سازی
        queryset = queryset.order_by('-created_at').select_related('student', 'booking', 'booking__teacher')
        
        # صفحه‌بندی
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 20))
        
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = StudentTransactionSerializer(paginated_queryset, many=True)
        
        return paginator.get_paginated_response(serializer.data)
