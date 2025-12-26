"""API Views for Skyroom Integration"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta

from .models import Service, Room, SkyroomUser, RoomUserAccess, LoginUrl
from .serializers import (
    ServiceSerializer, ServiceDetailSerializer,
    RoomListSerializer, RoomSerializer, RoomCreateUpdateSerializer,
    SkyroomUserListSerializer, SkyroomUserSerializer, SkyroomUserCreateUpdateSerializer,
    RoomUserAccessSerializer, RoomUserAccessCreateSerializer,
    LoginUrlSerializer, LoginUrlCreateSerializer
)


# ========== Service ViewSet ==========

class ServiceViewSet(viewsets.ModelViewSet):
    """
    Service Management API
    
    Manages Skyroom service plans with user and video limits.
    
    list:
        Get all available services with filtering and search capabilities.
        
    retrieve:
        Get detailed information about a specific service.
        
    create:
        Create a new service plan.
        
    update:
        Update an existing service plan.
        
    partial_update:
        Partially update a service plan.
        
    destroy:
        Delete a service plan.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'skyroom_id']
    ordering_fields = ['id', 'title', 'status', 'updated_at']
    ordering = ['-updated_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ServiceDetailSerializer
        return ServiceSerializer


# ========== Room ViewSet ==========

class RoomViewSet(viewsets.ModelViewSet):
    """
    Room Management API
    
    Manages virtual meeting rooms with access control, guest settings, and time limits.
    Supports room user access management through custom actions.
    
    list:
        Get all rooms with filtering by service, status, and guest login settings.
        
    retrieve:
        Get detailed information about a specific room.
        
    create:
        Create a new virtual room.
        
    update:
        Update an existing room's settings.
        
    partial_update:
        Partially update a room's settings.
        
    destroy:
        Delete a room and all associated data.
        
    users:
        Get all users who have access to this room with their access levels.
        
    add_users:
        Add one or more users to a room with specific access levels.
        Expects: {"users": [{"user_id": 1, "access": 1}]}
        
    remove_users:
        Remove users from a room.
        Expects: {"users": [1, 2, 3]}
    """
    queryset = Room.objects.select_related('service').all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['service', 'status', 'guest_login']
    search_fields = ['name', 'title', 'skyroom_id']
    ordering_fields = ['id', 'name', 'title', 'status', 'updated_at']
    ordering = ['-updated_at']
    
    def get_serializer_class(self):
        if self.action in ['list']:
            return RoomListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RoomCreateUpdateSerializer
        return RoomSerializer
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Get all users with access to this room"""
        room = self.get_object()
        accesses = room.user_accesses.all()
        serializer = RoomUserAccessSerializer(accesses, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_users(self, request, pk=None):
        """Add users to room"""
        room = self.get_object()
        users_data = request.data.get('users', [])
        
        created_count = 0
        for user_data in users_data:
            user_id = user_data.get('user_id')
            access = user_data.get('access', 1)
            
            obj, created = RoomUserAccess.objects.get_or_create(
                room=room,
                user_id=user_id,
                defaults={'access': access}
            )
            if created:
                created_count += 1
        
        return Response({
            'success': True,
            'message': _('Users added successfully'),
            'count': created_count
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def remove_users(self, request, pk=None):
        """Remove users from room"""
        room = self.get_object()
        user_ids = request.data.get('users', [])
        
        deleted_count, _ = RoomUserAccess.objects.filter(
            room=room,
            user_id__in=user_ids
        ).delete()
        
        return Response({
            'success': True,
            'message': _('Users removed successfully'),
            'count': deleted_count
        })


# ========== SkyroomUser ViewSet ==========

class SkyroomUserViewSet(viewsets.ModelViewSet):
    """
    Skyroom User Management API
    
    Manages Skyroom user accounts with credentials, personal info, and room access.
    Supports user-room access management through custom actions.
    
    list:
        Get all Skyroom users with filtering by status, public flag, and gender.
        
    retrieve:
        Get detailed information about a specific user including credentials and usage stats.
        
    create:
        Create a new Skyroom user account.
        
    update:
        Update an existing user's information.
        
    partial_update:
        Partially update a user's information.
        
    destroy:
        Delete a user account.
        
    rooms:
        Get all rooms that this user has access to with their access levels.
        
    add_rooms:
        Add user to one or more rooms with specific access levels.
        Expects: {"rooms": [{"room_id": 1, "access": 2}]}
        
    remove_rooms:
        Remove user from specific rooms.
        Expects: {"rooms": [1, 2, 3]}
    """
    queryset = SkyroomUser.objects.all()
    serializer_class = SkyroomUserSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'is_public', 'gender']
    search_fields = ['username', 'nickname', 'email', 'skyroom_id']
    ordering_fields = ['id', 'username', 'nickname', 'status', 'updated_at']
    ordering = ['-updated_at']
    
    def get_serializer_class(self):
        if self.action in ['list']:
            return SkyroomUserListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SkyroomUserCreateUpdateSerializer
        return SkyroomUserSerializer
    
    @action(detail=True, methods=['get'])
    def rooms(self, request, pk=None):
        """Get all rooms this user has access to"""
        user = self.get_object()
        accesses = user.room_accesses.all()
        serializer = RoomUserAccessSerializer(accesses, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_rooms(self, request, pk=None):
        """Add rooms to user"""
        user = self.get_object()
        rooms_data = request.data.get('rooms', [])
        
        created_count = 0
        for room_data in rooms_data:
            room_id = room_data.get('room_id')
            access = room_data.get('access', 1)
            
            obj, created = RoomUserAccess.objects.get_or_create(
                room_id=room_id,
                user=user,
                defaults={'access': access}
            )
            if created:
                created_count += 1
        
        return Response({
            'success': True,
            'message': _('Rooms added successfully'),
            'count': created_count
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def remove_rooms(self, request, pk=None):
        """Remove rooms from user"""
        user = self.get_object()
        room_ids = request.data.get('rooms', [])
        
        deleted_count, _ = RoomUserAccess.objects.filter(
            user=user,
            room_id__in=room_ids
        ).delete()
        
        return Response({
            'success': True,
            'message': _('Rooms removed successfully'),
            'count': deleted_count
        })


# ========== RoomUserAccess ViewSet ==========

class RoomUserAccessViewSet(viewsets.ModelViewSet):
    """
    Room User Access Management API
    
    Manages access permissions between rooms and users.
    Allows setting and modifying user access levels (1=Normal, 2=Presenter, 3=Operator).
    
    list:
        Get all room-user access records with filtering by room, user, or access level.
        
    retrieve:
        Get detailed access information for a specific room-user relationship.
        
    create:
        Create a new room-user access record.
        
    update:
        Update a user's access level to a room.
        
    partial_update:
        Partially update access information.
        
    destroy:
        Remove a user's access to a room.
    """
    queryset = RoomUserAccess.objects.select_related('room', 'user').all()
    serializer_class = RoomUserAccessSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['room', 'user', 'access']
    search_fields = ['user__username', 'room__name']
    ordering_fields = ['id', 'access', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create']:
            return RoomUserAccessCreateSerializer
        return RoomUserAccessSerializer


# ========== LoginUrl ViewSet ==========

class LoginUrlViewSet(viewsets.ModelViewSet):
    """
    Login URL Management API
    
    Generates and manages direct login URLs for quick access to rooms without credentials.
    URLs can be configured with TTL (time to live), access levels, and concurrent user limits.
    
    list:
        Get all generated login URLs with filtering by room and active status.
        
    retrieve:
        Get detailed information about a specific login URL.
        
    create:
        Generate a new login URL for a room with optional TTL and access parameters.
        
    update:
        Update login URL settings.
        
    partial_update:
        Partially update login URL configuration.
        
    destroy:
        Delete a login URL permanently.
        
    expired:
        Get all expired login URLs (past expiry time).
        
    active:
        Get all active and valid login URLs.
        
    revoke:
        Immediately revoke and deactivate a login URL.
        Prevents future use even if TTL hasn't expired.
    """
    queryset = LoginUrl.objects.select_related('room').all()
    serializer_class = LoginUrlSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['room', 'access', 'is_active']
    search_fields = ['user_id', 'room__name', 'nickname']
    ordering_fields = ['id', 'created_at', 'expires_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create']:
            return LoginUrlCreateSerializer
        return LoginUrlSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a login URL"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ttl = serializer.validated_data.get('ttl', 3600)
        expires_at = timezone.now() + timedelta(seconds=ttl)
        
        # Generate login URL (placeholder - would be actual Skyroom API call)
        login_url = self._generate_login_url(serializer.validated_data)
        
        serializer.validated_data['url'] = login_url
        serializer.validated_data['expires_at'] = expires_at
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Get expired login URLs"""
        expired_urls = self.queryset.filter(expires_at__lt=timezone.now())
        serializer = self.get_serializer(expired_urls, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active login URLs"""
        active_urls = self.queryset.filter(
            is_active=True,
            expires_at__gte=timezone.now()
        )
        serializer = self.get_serializer(active_urls, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke a login URL"""
        login_url = self.get_object()
        login_url.is_active = False
        login_url.save()
        
        serializer = self.get_serializer(login_url)
        return Response(serializer.data)
    
    def _generate_login_url(self, data):
        """Generate login URL (placeholder)"""
        # This would call the actual Skyroom API
        return "https://www.skyroom.online/ch/sample/room/t/token"
