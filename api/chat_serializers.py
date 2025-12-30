# -*- coding: utf-8 -*-
from rest_framework import serializers
from classroom.models import ChatRoom, ChatParticipant, Message, MessageReaction
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatRoomSerializer(serializers.ModelSerializer):
    teaching_subject_title = serializers.CharField(
        source='teaching_subject.title',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'type', 'teaching_subject', 'teaching_subject_title', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatParticipantSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source='user.name',
        read_only=True
    )
    user_avatar = serializers.CharField(
        source='user.avatar',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = ChatParticipant
        fields = ['id', 'user', 'user_name', 'user_avatar', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class MessageReactionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source='user.name',
        read_only=True
    )
    
    class Meta:
        model = MessageReaction
        fields = ['id', 'user', 'user_name', 'reaction_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(
        source='sender.name',
        read_only=True,
        allow_null=True
    )
    sender_avatar = serializers.CharField(
        source='sender.avatar',
        read_only=True,
        allow_null=True
    )
    reactions = MessageReactionSerializer(
        many=True,
        read_only=True
    )
    reactions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id',
            'chat_room',
            'sender',
            'sender_name',
            'sender_avatar',
            'message_type',
            'text',
            'file',
            'reactions',
            'reactions_count',
            'is_deleted',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_reactions_count(self, obj):
        """تعداد واکنش‌های متفاوت برای پیام"""
        return obj.reactions.filter(is_deleted=False).values('reaction_type').distinct().count()


class ChatRoomDetailSerializer(serializers.ModelSerializer):
    """Serializer برای جزئیات اتاق چت با شرکت‌کنندگان"""
    participants = ChatParticipantSerializer(many=True, read_only=True)
    teaching_subject_title = serializers.CharField(
        source='teaching_subject.title',
        read_only=True,
        allow_null=True
    )
    messages_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'type',
            'teaching_subject',
            'teaching_subject_title',
            'participants',
            'messages_count',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_messages_count(self, obj):
        """تعداد پیام‌های غیرحذف‌شده"""
        return obj.messages.filter(is_deleted=False).count()
