"""Tests for Skyroom App"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from .models import Service, Room, SkyroomUser, RoomUserAccess, LoginUrl

User = get_user_model()


class ServiceModelTest(TestCase):
    """Test Service Model"""
    
    def setUp(self):
        self.service = Service.objects.create(
            skyroom_id=1,
            title='Test Service',
            status=1,
            user_limit=10,
            video_limit=8,
            start_time=int(timezone.now().timestamp()),
            stop_time=int((timezone.now() + timedelta(days=365)).timestamp())
        )
    
    def test_service_creation(self):
        self.assertEqual(self.service.title, 'Test Service')
        self.assertEqual(self.service.status, 1)


class RoomModelTest(TestCase):
    """Test Room Model"""
    
    def setUp(self):
        self.service = Service.objects.create(
            skyroom_id=1,
            title='Test Service',
            status=1,
            user_limit=10,
            video_limit=8,
            start_time=int(timezone.now().timestamp()),
            stop_time=int((timezone.now() + timedelta(days=365)).timestamp())
        )
        self.room = Room.objects.create(
            skyroom_id=1,
            service=self.service,
            name='test-room',
            title='Test Room',
            status=1
        )
    
    def test_room_creation(self):
        self.assertEqual(self.room.name, 'test-room')
        self.assertEqual(self.room.service, self.service)


class SkyroomUserModelTest(TestCase):
    """Test SkyroomUser Model"""
    
    def setUp(self):
        self.user = SkyroomUser.objects.create(
            skyroom_id=1,
            username='testuser',
            nickname='Test User',
            password='hashed_password',
            status=1
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.status, 1)
