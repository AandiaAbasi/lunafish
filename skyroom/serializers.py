"""Serializers for Skyroom API"""
from rest_framework import serializers
from .models import Service, Room, SkyroomUser, RoomUserAccess, LoginUrl


# ========== Service Serializers ==========

class ServiceSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'skyroom_id', 'title', 'status', 'status_display',
            'user_limit', 'video_limit', 'time_limit', 'time_usage',
            'start_time', 'stop_time', 'created_at_display', 'updated_at_display'
        ]
        read_only_fields = ['id', 'created_at_display', 'updated_at_display']


class ServiceDetailSerializer(ServiceSerializer):
    rooms_count = serializers.SerializerMethodField()
    
    class Meta(ServiceSerializer.Meta):
        fields = ServiceSerializer.Meta.fields + ['rooms_count']
    
    def get_rooms_count(self, obj):
        return obj.rooms.count()


# ========== Room Serializers ==========

class RoomListSerializer(serializers.ModelSerializer):
    service_title = serializers.CharField(source='service.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Room
        fields = [
            'id', 'skyroom_id', 'name', 'title', 'service', 'service_title',
            'status', 'status_display', 'max_users', 'guest_login'
        ]
        read_only_fields = ['id']


class RoomSerializer(serializers.ModelSerializer):
    service_title = serializers.CharField(source='service.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Room
        fields = [
            'id', 'skyroom_id', 'name', 'title', 'description', 'service', 'service_title',
            'status', 'status_display', 'guest_login', 'guest_limit', 'op_login_first',
            'max_users', 'session_duration', 'time_limit', 'time_usage', 'time_total',
            'created_at_display', 'updated_at_display'
        ]
        read_only_fields = ['id', 'created_at_display', 'updated_at_display']


class RoomCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = [
            'skyroom_id', 'name', 'title', 'description', 'service',
            'status', 'guest_login', 'guest_limit', 'op_login_first',
            'max_users', 'session_duration', 'time_limit'
        ]


# ========== SkyroomUser Serializers ==========

class SkyroomUserListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    
    class Meta:
        model = SkyroomUser
        fields = [
            'id', 'skyroom_id', 'username', 'nickname', 'status', 'status_display',
            'gender', 'gender_display', 'is_public', 'email'
        ]
        read_only_fields = ['id']


class SkyroomUserSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    
    class Meta:
        model = SkyroomUser
        fields = [
            'id', 'skyroom_id', 'username', 'nickname', 'email', 'fname', 'lname',
            'status', 'status_display', 'gender', 'gender_display', 'is_public',
            'concurrent', 'time_limit', 'time_usage', 'time_total', 'expiry_date',
            'created_at_display', 'updated_at_display'
        ]
        read_only_fields = ['id', 'created_at_display', 'updated_at_display']


class SkyroomUserCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkyroomUser
        fields = [
            'skyroom_id', 'username', 'password', 'nickname', 'email',
            'fname', 'lname', 'gender', 'status', 'is_public', 'concurrent',
            'time_limit', 'expiry_date'
        ]


# ========== RoomUserAccess Serializers ==========

class RoomUserAccessSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    access_display = serializers.CharField(source='get_access_display', read_only=True)
    
    class Meta:
        model = RoomUserAccess
        fields = [
            'id', 'room', 'room_name', 'user', 'username', 'user_nickname',
            'access', 'access_display', 'created_at_display', 'updated_at_display'
        ]
        read_only_fields = ['id', 'created_at_display', 'updated_at_display']


class RoomUserAccessCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomUserAccess
        fields = ['room', 'user', 'access']


# ========== LoginUrl Serializers ==========

class LoginUrlSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.name', read_only=True)
    access_display = serializers.CharField(source='get_access_display', read_only=True)
    
    class Meta:
        model = LoginUrl
        fields = [
            'id', 'room', 'room_name', 'user_id', 'nickname', 'access', 'access_display',
            'concurrent', 'url', 'ttl', 'is_active', 'expires_at', 'created_at_display', 'updated_at_display'
        ]
        read_only_fields = ['id', 'url', 'created_at_display', 'updated_at_display']


class LoginUrlCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginUrl
        fields = ['room', 'user_id', 'nickname', 'access', 'concurrent', 'ttl', 'is_active']
