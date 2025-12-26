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
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from drf_spectacular.decorators import extend_schema
from drf_spectacular.types import OpenApiTypes
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
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'required': ['identifier'],
                'properties': {
                    'identifier': {
                        'type': 'string',
                        'description': 'Phone number or email address for OTP'
                    },
                    'purpose': {
                        'type': 'string',
                        'enum': ['login', 'registration'],
                        'default': 'login',
                        'description': 'Purpose of OTP: login or registration'
                    }
                },
                'example': {
                    'identifier': '+989123456789',
                    'purpose': 'login'
                }
            }
        },
        responses={
            200: {
                'description': 'OTP sent successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'message': 'OTP sent to your phone number',
                            'identifier': '+989123456789'
                        }
                    }
                }
            },
            400: {'description': 'Invalid identifier or too many requests'},
            429: {'description': 'Rate limit exceeded - please wait before requesting another OTP'}
        },
        tags=['authentication']
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
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'required': ['identifier', 'code'],
                'properties': {
                    'identifier': {
                        'type': 'string',
                        'description': 'Phone number or email address that received the OTP'
                    },
                    'code': {
                        'type': 'string',
                        'description': '6-digit OTP code'
                    },
                    'purpose': {
                        'type': 'string',
                        'enum': ['login', 'registration'],
                        'default': 'login',
                        'description': 'Purpose of OTP verification'
                    }
                },
                'example': {
                    'identifier': '+989123456789',
                    'code': '123456',
                    'purpose': 'login'
                }
            }
        },
        responses={
            200: {
                'description': 'OTP verified successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'message': 'Login successful',
                            'user': {
                                'id': 1,
                                'username': 'user123',
                                'email': 'user@example.com',
                                'first_name': 'John',
                                'last_name': 'Doe'
                            },
                            'tokens': {
                                'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...'
                            }
                        }
                    }
                }
            },
            400: {'description': 'Invalid OTP code or identifier'}
        },
        tags=['authentication']
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
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'required': ['verification_token', 'username', 'password', 'name'],
                'properties': {
                    'verification_token': {
                        'type': 'string',
                        'description': 'Token received from OTP verification'
                    },
                    'username': {
                        'type': 'string',
                        'description': 'Desired username (must be unique)'
                    },
                    'password': {
                        'type': 'string',
                        'format': 'password',
                        'description': 'Account password'
                    },
                    'name': {
                        'type': 'string',
                        'description': "User's full name"
                    },
                    'expo_push_token': {
                        'type': 'string',
                        'description': 'Expo push notification token (optional)'
                    }
                },
                'example': {
                    'verification_token': 'abc123def456...',
                    'username': 'john_doe',
                    'password': 'SecurePass123!',
                    'name': 'John Doe'
                }
            }
        },
        responses={
            201: {'description': 'User registered successfully with JWT tokens'},
            400: {'description': 'Invalid verification token or registration failed'}
        },
        tags=['authentication']
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
        
        Request parameters:
        - username: User's username (required)
        - password: User's password (required)
        
        Returns: JWT tokens + user profile data
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
    Check Username Availability API (Duplicate)
    
    Verify if a username is available for registration.
    Accepts both GET and POST requests.
    
    get:
        Check if username is available (query parameter).
        
        Query parameters:
        - username: Username to check (required, minimum 3 characters)
        
        Returns:
            - success: Boolean
            - available: Boolean (true if available)
            - message: Status message
    
    post:
        Check if username is available (body parameter).
        
        Request body:
        - username: Username to check (required, minimum 3 characters)
        
        Returns:
            - success: Boolean
            - available: Boolean (true if available)
            - message: Status message
    """
    permission_classes = [AllowAny]
    
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
    avatar, and role-specific settings.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'first_name': {
                        'type': 'string',
                        'description': "User's or Teacher's first name"
                    },
                    'last_name': {
                        'type': 'string',
                        'description': "User's or Teacher's last name"
                    },
                    'email': {
                        'type': 'string',
                        'format': 'email',
                        'description': 'Email address'
                    },
                    'phone': {
                        'type': 'string',
                        'description': 'Phone number'
                    },
                    'bio': {
                        'type': 'string',
                        'description': 'User biography or description'
                    },
                    'avatar_url': {
                        'type': 'string',
                        'description': 'Avatar URL (for regular users)'
                    },
                    'specialization': {
                        'type': 'string',
                        'description': 'Area of specialization (for teachers)'
                    },
                    'experience_years': {
                        'type': 'integer',
                        'description': 'Years of teaching experience (for teachers)'
                    },
                    'qualifications': {
                        'type': 'string',
                        'description': 'Professional qualifications (for teachers)'
                    }
                },
                'example': {
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'john@example.com',
                    'phone': '+989123456789',
                    'bio': 'Software developer'
                }
            }
        },
        responses={
            200: {
                'description': 'Profile updated successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'message': 'Profile updated successfully',
                            'user': {
                                'id': 1,
                                'username': 'john_doe',
                                'email': 'john@example.com',
                                'phone': '+989123456789',
                                'first_name': 'John',
                                'last_name': 'Doe',
                                'bio': 'Software developer',
                                'role': 'user'
                            }
                        }
                    }
                }
            },
            400: {'description': 'Invalid data provided'},
            401: {'description': 'User not authenticated'}
        },
        tags=['profile']
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
    
    post:
        Set an avatar as the user's profile picture.
        
        Request body parameters:
            - avatar_template_id: integer (required) - ID of avatar template to select
        
        Returns:
            200 OK:
                - success: boolean (true)
                - message: string - Success message
                - user: object - Updated user profile with selected avatar
                
            404 Not Found - Avatar template does not exist
            400 Bad Request - Invalid data provided
    """
    permission_classes = [IsAuthenticated]
    
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
    
    post:
        Promote authenticated user to teacher role.
        
        Request body parameters:
            - specialization: string (required) - Area of expertise (e.g., "Mathematics", "English")
            - experience_years: integer (required) - Years of teaching experience
            - qualifications: string (required) - Professional qualifications and certifications
        
        Returns:
            200 OK:
                - success: boolean (true)
                - message: string - Promotion confirmation
                - user: object - Updated user profile with teacher role
                
            400 Bad Request:
                - User is already a teacher
                - Invalid or missing required fields
            401 Unauthorized - User not authenticated
    """
    permission_classes = [IsAuthenticated]
    
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
    Change User Password API (Duplicate)
    
    Allow authenticated users to change their account password.
    Requires old password verification.
    
    post:
        Change the authenticated user's password.
        
        Request body:
        - old_password: Current password (required)
        - new_password: New password (required)
        - confirm_password: Confirm new password (required)
        
        Returns:
            - success: Boolean
            - message: Success or error message
    """
    permission_classes = [IsAuthenticated]
    
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
    
    post:
        Logout the authenticated user and invalidate their refresh token.
        
        Request body parameters:
            - refresh_token: string (required) - Refresh token to blacklist
            OR
            - refresh: string (required) - Alternative parameter name for refresh token
        
        Returns:
            200 OK:
                - success: boolean (true)
                - message: string - "Logout successful"
                
            400 Bad Request:
                - Refresh token not provided
                - Invalid token format
            401 Unauthorized - User not authenticated
    """
    permission_classes = [IsAuthenticated]
    
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

