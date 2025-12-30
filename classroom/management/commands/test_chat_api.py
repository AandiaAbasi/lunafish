#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Django Management Command to test Chat API
Usage: python manage.py test_chat_api
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from classroom.models import ChatRoom, ChatParticipant, Message, MessageReaction, TeachingSubject
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Test all Chat API endpoints'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '█'*60))
        self.stdout.write(self.style.SUCCESS('█  FOFOFISH CHAT API TEST SUITE'))
        self.stdout.write(self.style.SUCCESS('█'*60 + '\n'))
        
        try:
            # Setup test data
            self.setup_test_data()
            
            # Run tests
            self.test_get_chat_history()
            msg_id = self.test_send_message()
            self.test_add_reaction(msg_id)
            self.test_list_participants()
            self.test_permissions()
            
            self.stdout.write(self.style.SUCCESS('\n✅ ALL TESTS COMPLETED!\n'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Test failed: {str(e)}\n'))
            import traceback
            traceback.print_exc()
    
    def setup_test_data(self):
        """Create test data"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('  Setting Up Test Data')
        self.stdout.write('='*60)
        
        # Create users
        self.teacher, _ = User.objects.get_or_create(
            username='chat_test_teacher',
            defaults={'name': 'علی معلم', 'role': 'teacher', 'phone_number': '09111111111'}
        )
        
        self.student, _ = User.objects.get_or_create(
            username='chat_test_student',
            defaults={'name': 'فاطمه دانش‌آموز', 'role': 'student', 'phone_number': '09122222222'}
        )
        
        self.admin, _ = User.objects.get_or_create(
            username='chat_test_admin',
            defaults={'name': 'احمد ادمین', 'role': 'admin', 'phone_number': '09133333333'}
        )
        
        self.stdout.write(f'✅ Teacher: {self.teacher.name}')
        self.stdout.write(f'✅ Student: {self.student.name}')
        self.stdout.write(f'✅ Admin: {self.admin.name}')
        
        # Create teaching subject
        self.subject, _ = TeachingSubject.objects.get_or_create(
            title='English Test',
            teacher=self.teacher,
            defaults={
                'description': 'آموزش انگلیسی',
                'level': 'beginner'
            }
        )
        self.stdout.write(f'✅ Teaching Subject: {self.subject.title}')
        
        # Create chat rooms
        self.support_chat, _ = ChatRoom.objects.get_or_create(
            type='support',
            teaching_subject=None
        )
        
        self.classroom_chat, _ = ChatRoom.objects.get_or_create(
            type='classroom',
            teaching_subject=self.subject
        )
        
        self.stdout.write(f'✅ Support Chat: {self.support_chat.id}')
        self.stdout.write(f'✅ Classroom Chat: {self.classroom_chat.id}')
        
        # Add participants
        ChatParticipant.objects.get_or_create(
            chat_room=self.classroom_chat,
            user=self.teacher,
            defaults={'role': 'teacher'}
        )
        ChatParticipant.objects.get_or_create(
            chat_room=self.classroom_chat,
            user=self.student,
            defaults={'role': 'student'}
        )
        
        self.stdout.write('✅ Chat participants added\n')
    
    def get_token(self, user):
        """Get JWT token for user"""
        return str(RefreshToken.for_user(user).access_token)
    
    def test_get_chat_history(self):
        """Test GET /api/chat/<id>/"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('  Testing: Get Chat History')
        self.stdout.write('='*60)
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.teacher)}')
        
        response = client.get(f'/api/chat/{self.classroom_chat.id}/')
        
        if response.status_code == 200:
            messages = response.json()
            self.stdout.write(self.style.SUCCESS(f'✅ Retrieved {len(messages)} messages'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {response.status_code}'))
    
    def test_send_message(self):
        """Test POST /api/chat/<id>/send/"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('  Testing: Send Message')
        self.stdout.write('='*60)
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.teacher)}')
        
        payload = {
            'message_type': 'text',
            'text': 'سلام! این یک پیام تستی است'
        }
        
        response = client.post(
            f'/api/chat/{self.classroom_chat.id}/send/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        if response.status_code == 201:
            message = response.json()
            self.stdout.write(self.style.SUCCESS(f'✅ Message sent: {message["id"]}'))
            self.stdout.write(f'   Type: {message["message_type"]}')
            self.stdout.write(f'   Text: {message["text"]}')
            self.stdout.write(f'   Sender: {message["sender_name"]}\n')
            return message['id']
        else:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {response.status_code}'))
            self.stdout.write(f'   Response: {response.content}')
            return None
    
    def test_add_reaction(self, message_id):
        """Test POST /api/chat/message/<id>/react/"""
        self.stdout.write('='*60)
        self.stdout.write('  Testing: Add Reactions')
        self.stdout.write('='*60)
        
        if not message_id:
            self.stdout.write(self.style.ERROR('❌ No message ID provided'))
            return
        
        client = APIClient()
        
        reaction_types = ['like', 'heart', 'clap']
        
        for reaction_type in reaction_types:
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.student)}')
            
            payload = {'reaction_type': reaction_type}
            
            response = client.post(
                f'/api/chat/message/{message_id}/react/',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            if response.status_code == 201:
                reaction = response.json()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {reaction_type} reaction by {reaction["user_name"]}')
                )
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to add {reaction_type}'))
        
        self.stdout.write('')
    
    def test_list_participants(self):
        """Test GET /api/chat/<id>/participants/"""
        self.stdout.write('='*60)
        self.stdout.write('  Testing: List Participants')
        self.stdout.write('='*60)
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.teacher)}')
        
        response = client.get(f'/api/chat/{self.classroom_chat.id}/participants/')
        
        if response.status_code == 200:
            participants = response.json()
            self.stdout.write(self.style.SUCCESS(f'✅ Retrieved {len(participants)} participants:'))
            for p in participants:
                self.stdout.write(f'   - {p["user_name"]} ({p["role"]})')
            self.stdout.write('')
        else:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {response.status_code}'))
    
    def test_permissions(self):
        """Test permission checks"""
        self.stdout.write('='*60)
        self.stdout.write('  Testing: Permission Checks')
        self.stdout.write('='*60)
        
        # Create non-participant user
        other_user, _ = User.objects.get_or_create(
            username='chat_test_other',
            defaults={'name': 'کاربر دیگر', 'role': 'student', 'phone_number': '09144444444'}
        )
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(other_user)}')
        
        response = client.get(f'/api/chat/{self.classroom_chat.id}/')
        
        if response.status_code == 403:
            self.stdout.write(self.style.SUCCESS('✅ Correctly denied non-participant access'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Expected 403, got {response.status_code}'))
        
        self.stdout.write('')
