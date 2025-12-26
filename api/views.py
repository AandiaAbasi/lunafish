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
    """API: Send OTP to phone or email"""
    permission_classes = [AllowAny]
    
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
    """API: Verify OTP and login/register user"""
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
    """API: Complete registration with username and password"""
    permission_classes = [AllowAny]
    
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
    """API: User login with username/password"""
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
    """API: Teacher login with username/password"""
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
    """API: Complete teacher registration with username and password"""
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
    """API: Send OTP to user email"""
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
    """API: Verify OTP and login user via email"""
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
    """API: Send OTP to teacher email"""
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
    """API: Verify OTP and login teacher via email"""
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
    """API: Check if username is available"""
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
    """API: Fetch current user data with token (GET only)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user information"""
        serializer = UserProfileSerializer(request.user)
        return Response({
            "success": True,
            "user": serializer.data
        }, status=status.HTTP_200_OK)


class UserProfileAPIView(APIView):
    """API: Update user profile (both user and teacher)"""
    permission_classes = [IsAuthenticated]
    
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





class PromoteToTeacherAPIView(APIView):
    """API: Promote user to teacher role"""
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
    """API: Change user password"""
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
    """API: Logout user (blacklist refresh token)"""
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
    """API: List all FAQs"""
    permission_classes = [AllowAny]
    queryset = FAQ.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = FAQSerializer


class AboutAPIView(APIView):
    """API: Get about page content"""
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
    """API: List all terms"""
    permission_classes = [AllowAny]
    queryset = Term.objects.all().order_by('-created_at')
    serializer_class = TermSerializer


class PrivacyListAPIView(generics.ListAPIView):
    """API: List all privacy policies"""
    permission_classes = [AllowAny]
    queryset = Privacy.objects.all().order_by('-created_at')
    serializer_class = PrivacySerializer


class ContactListAPIView(generics.ListAPIView):
    """API: List all contact information"""
    permission_classes = [AllowAny]
    queryset = Contact.objects.all().order_by('type')
    serializer_class = ContactSerializer


class ContactPhoneAPIView(APIView):
    """API: Get first phone contact"""
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

