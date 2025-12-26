"""
API Views for mobile application - Unified User Model
Based on alolebas pattern with JWT authentication
Supports role-based access: user, teacher, admin
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, parsers
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
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
    """API: Send OTP to teacher phone"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['identifier']
            
            # Check cooldown
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
            
            # Generate and send OTP with teacher template
            try:
                if '@' in str(identifier):
                    return Response({
                        "success": False,
                        "message": _("Sending OTP to email is currently not supported")
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    generate_and_send_otp(identifier, purpose='login', user=None, is_teacher=True)
                    
                return Response({
                    "success": True,
                    "message": _("Verification code sent.")
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "success": False,
                    "message": _(f"Error sending code: {str(e)}")
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "success": False,
            "message": _("Invalid data provided"),
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TeacherVerifyOTPAPIView(APIView):
    """API: Verify OTP and login teacher"""
    permission_classes = [AllowAny]
    
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
    """API: List all articles"""
    permission_classes = [AllowAny]
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleListSerializer


class ArticleDetailAPIView(APIView):
    """API: Get article detail"""
    permission_classes = [AllowAny]
    
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


class AboutAPIView(APIView):
    """
    Get About Page API (Duplicate)
    
    Retrieve content for the about/company information page.
    
    get:
        Get about page content.
        
        Returns:
            - success: Boolean
            - data: About page object with id, title, description, contact_info, created_at
    """
    permission_classes = [AllowAny]
    
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
    List Terms and Conditions API (Duplicate)
    
    Retrieve all terms and conditions documents.
    
    get:
        List all terms ordered by creation date.
        
        Returns:
            - List of term objects with id, title, content, version, created_at
    """
    permission_classes = [AllowAny]
    queryset = Term.objects.all().order_by('-created_at')
    serializer_class = TermSerializer


class PrivacyListAPIView(generics.ListAPIView):
    """
    List Privacy Policies API (Duplicate)
    
    Retrieve all privacy policy documents.
    
    get:
        List all privacy policies ordered by creation date.
       
    List Contact Information API (Duplicate)
    
    Retrieve all contact information records.
    
    get:
        List all contact records ordered by type.
        
        Returns:
            - List of contact objects with id, type, value (phone/email/address), created_at
    
        Returns:
            - List of privacy objects with id, title, content, version, created_at
    """
    permission_classes = [AllowAny]
    queryset = Privacy.objects.all().order_by('-created_at')
    serializer_class = PrivacySerializer


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


class ContactPhoneAPIView(APIView):
    """
    Get Phone Contact API
    
    Retrieve the primary phone contact information.
    
    get:
        Get the first phone contact record from the database.
        
        Returns:
            - status: 'success' or 'error'
            - data: Contact object with type='phone' and value (phone number)
            - message: Status message
    """
    permission_classes = [AllowAny]
    
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
    permission_classes = [AllowAny]
    
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

