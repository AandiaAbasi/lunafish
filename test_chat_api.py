#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chat API Test Script
Tests all chat endpoints and models
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fofofish.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from classroom.models import ChatRoom, ChatParticipant, Message, MessageReaction, TeachingSubject
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import Client
import json

User = get_user_model()

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def get_auth_header(user):
    """Generate JWT token for user"""
    refresh = RefreshToken.for_user(user)
    return {'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'}

def setup_test_data():
    """Create test data"""
    print_header("Setting Up Test Data")
    
    # Create or get users
    teacher, created = User.objects.get_or_create(
        username='test_teacher',
        defaults={'name': 'علی معلم', 'role': 'teacher', 'phone': '+989111111111'}
    )
    print_info(f"Teacher: {teacher.name} {'(created)' if created else '(existing)'}")
    
    student, created = User.objects.get_or_create(
        username='test_student',
        defaults={'name': 'فاطمه دانش‌آموز', 'role': 'student', 'phone': '+989122222222'}
    )
    print_info(f"Student: {student.name} {'(created)' if created else '(existing)'}")
    
    admin, created = User.objects.get_or_create(
        username='test_admin',
        defaults={'name': 'احمد ادمین', 'role': 'admin', 'phone': '+989133333333'}
    )
    print_info(f"Admin: {admin.name} {'(created)' if created else '(existing)'}")
    
    # Create teaching subject for classroom chat
    teaching_subject, created = TeachingSubject.objects.get_or_create(
        title='English for Beginners',
        teacher=teacher,
        defaults={
            'description': 'آموزش انگلیسی برای مبتدیان',
            'level': 'beginner'
        }
    )
    print_info(f"Teaching Subject: {teaching_subject.title} {'(created)' if created else '(existing)'}")
    
    # Create support chat room
    support_chat, created = ChatRoom.objects.get_or_create(
        type='support',
        teaching_subject=None,
        defaults={}
    )
    print_success(f"Support Chat Room: {support_chat.id} {'(created)' if created else '(existing)'}")
    
    # Create classroom chat room
    classroom_chat, created = ChatRoom.objects.get_or_create(
        type='classroom',
        teaching_subject=teaching_subject,
        defaults={}
    )
    print_success(f"Classroom Chat Room: {classroom_chat.id} {'(created)' if created else '(existing)'}")
    
    # Add participants to support chat
    ChatParticipant.objects.get_or_create(
        chat_room=support_chat,
        user=teacher,
        defaults={'role': 'teacher'}
    )
    ChatParticipant.objects.get_or_create(
        chat_room=support_chat,
        user=admin,
        defaults={'role': 'admin'}
    )
    print_success("Support chat participants added")
    
    # Add participants to classroom chat
    ChatParticipant.objects.get_or_create(
        chat_room=classroom_chat,
        user=teacher,
        defaults={'role': 'teacher'}
    )
    ChatParticipant.objects.get_or_create(
        chat_room=classroom_chat,
        user=student,
        defaults={'role': 'student'}
    )
    print_success("Classroom chat participants added")
    
    return {
        'teacher': teacher,
        'student': student,
        'admin': admin,
        'support_chat': support_chat,
        'classroom_chat': classroom_chat,
        'teaching_subject': teaching_subject
    }

def test_chat_history(client, users):
    """Test GET /api/chat/<id>/"""
    print_header("Testing: Get Chat History")
    
    chat_id = users['classroom_chat'].id
    auth = get_auth_header(users['teacher'])
    
    response = client.get(
        f'/api/chat/{chat_id}/',
        **auth
    )
    
    if response.status_code == 200:
        messages = response.json()
        print_success(f"Retrieved {len(messages)} messages from chat {chat_id}")
        for msg in messages:
            print_info(f"  Message {msg['id']}: {msg['message_type']} by {msg['sender_name']}")
    else:
        print_error(f"Failed: {response.status_code}")
        print_error(f"Response: {response.content}")

def test_send_text_message(client, users):
    """Test POST /api/chat/<id>/send/ with text"""
    print_header("Testing: Send Text Message")
    
    chat_id = users['classroom_chat'].id
    auth = get_auth_header(users['teacher'])
    
    payload = {
        'message_type': 'text',
        'text': 'سلام دانش‌آموزان! امروز درس جدید شروع می‌کنیم'
    }
    
    response = client.post(
        f'/api/chat/{chat_id}/send/',
        data=json.dumps(payload),
        content_type='application/json',
        **auth
    )
    
    if response.status_code == 201:
        message = response.json()
        print_success(f"Message sent: {message['id']}")
        print_info(f"  Type: {message['message_type']}")
        print_info(f"  Text: {message['text']}")
        print_info(f"  Sender: {message['sender_name']}")
        return message['id']
    else:
        print_error(f"Failed: {response.status_code}")
        print_error(f"Response: {response.content}")
        return None

def test_send_with_file(client, users):
    """Test POST /api/chat/<id>/send/ with image"""
    print_header("Testing: Send Image Message")
    
    # Create a simple test image
    from io import BytesIO
    from PIL import Image
    
    # Create image in memory
    img = Image.new('RGB', (100, 100), color='red')
    img_io = BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    
    chat_id = users['classroom_chat'].id
    auth = get_auth_header(users['student'])
    
    data = {
        'message_type': 'image',
        'file': img_io
    }
    
    response = client.post(
        f'/api/chat/{chat_id}/send/',
        data=data,
        **auth
    )
    
    if response.status_code == 201:
        message = response.json()
        print_success(f"Image message sent: {message['id']}")
        print_info(f"  Type: {message['message_type']}")
        print_info(f"  File: {message['file']}")
        print_info(f"  Sender: {message['sender_name']}")
        return message['id']
    else:
        print_error(f"Failed: {response.status_code}")
        print_error(f"Response: {response.content}")
        return None

def test_add_reaction(client, users, message_id):
    """Test POST /api/chat/message/<id>/react/"""
    print_header("Testing: Add Reaction to Message")
    
    if not message_id:
        print_error("No message ID provided")
        return
    
    auth = get_auth_header(users['student'])
    
    payload = {
        'reaction_type': 'like'
    }
    
    response = client.post(
        f'/api/chat/message/{message_id}/react/',
        data=json.dumps(payload),
        content_type='application/json',
        **auth
    )
    
    if response.status_code == 201:
        reaction = response.json()
        print_success(f"Reaction added: {reaction['id']}")
        print_info(f"  Type: {reaction['reaction_type']}")
        print_info(f"  User: {reaction['user_name']}")
    elif response.status_code == 204:
        print_success("Reaction toggled (removed)")
    else:
        print_error(f"Failed: {response.status_code}")
        print_error(f"Response: {response.content}")

def test_add_multiple_reactions(client, users, message_id):
    """Test multiple reactions on same message"""
    print_header("Testing: Multiple Reactions")
    
    if not message_id:
        print_error("No message ID provided")
        return
    
    reaction_types = ['like', 'heart', 'clap']
    
    for i, reaction_type in enumerate(reaction_types):
        # Use different users
        if i % 2 == 0:
            auth = get_auth_header(users['teacher'])
        else:
            auth = get_auth_header(users['student'])
        
        payload = {'reaction_type': reaction_type}
        
        response = client.post(
            f'/api/chat/message/{message_id}/react/',
            data=json.dumps(payload),
            content_type='application/json',
            **auth
        )
        
        if response.status_code == 201:
            reaction = response.json()
            print_success(f"Added {reaction_type} reaction by {reaction['user_name']}")
        else:
            print_error(f"Failed to add {reaction_type}: {response.status_code}")

def test_list_participants(client, users):
    """Test GET /api/chat/<id>/participants/"""
    print_header("Testing: List Chat Participants")
    
    chat_id = users['classroom_chat'].id
    auth = get_auth_header(users['teacher'])
    
    response = client.get(
        f'/api/chat/{chat_id}/participants/',
        **auth
    )
    
    if response.status_code == 200:
        participants = response.json()
        print_success(f"Retrieved {len(participants)} participants")
        for participant in participants:
            print_info(f"  {participant['user_name']} ({participant['role']})")
    else:
        print_error(f"Failed: {response.status_code}")
        print_error(f"Response: {response.content}")

def test_permission_denied(client, users):
    """Test that non-participants can't access chat"""
    print_header("Testing: Permission Denied (Non-participant)")
    
    # Create another user not in chat
    other_user, _ = User.objects.get_or_create(
        username='non_participant',
        defaults={'name': 'کاربر غریب', 'role': 'student', 'phone': '+989144444444'}
    )
    
    chat_id = users['classroom_chat'].id
    auth = get_auth_header(other_user)
    
    response = client.get(
        f'/api/chat/{chat_id}/',
        **auth
    )
    
    if response.status_code == 403:
        print_success("Correctly denied access to non-participant")
    else:
        print_error(f"Expected 403, got {response.status_code}")

def test_invalid_message_type(client, users):
    """Test invalid message type"""
    print_header("Testing: Invalid Message Type")
    
    chat_id = users['classroom_chat'].id
    auth = get_auth_header(users['teacher'])
    
    payload = {
        'message_type': 'invalid_type',
        'text': 'This should fail'
    }
    
    response = client.post(
        f'/api/chat/{chat_id}/send/',
        data=json.dumps(payload),
        content_type='application/json',
        **auth
    )
    
    if response.status_code == 400:
        print_success("Correctly rejected invalid message type")
    else:
        print_error(f"Expected 400, got {response.status_code}")

def test_support_chat(client, users):
    """Test support chat operations"""
    print_header("Testing: Support Chat Operations")
    
    chat_id = users['support_chat'].id
    auth = get_auth_header(users['teacher'])
    
    # Send message in support chat
    payload = {
        'message_type': 'text',
        'text': 'سلام، من مشکلی دارم'
    }
    
    response = client.post(
        f'/api/chat/{chat_id}/send/',
        data=json.dumps(payload),
        content_type='application/json',
        **auth
    )
    
    if response.status_code == 201:
        print_success("Support chat message sent successfully")
    else:
        print_error(f"Failed to send support message: {response.status_code}")

def test_reaction_toggle(client, users, message_id):
    """Test reaction toggle (add then remove)"""
    print_header("Testing: Reaction Toggle")
    
    if not message_id:
        print_error("No message ID provided")
        return
    
    auth = get_auth_header(users['teacher'])
    payload = {'reaction_type': 'star'}
    
    # First: Add reaction
    response1 = client.post(
        f'/api/chat/message/{message_id}/react/',
        data=json.dumps(payload),
        content_type='application/json',
        **auth
    )
    
    if response1.status_code == 201:
        print_success("Reaction added")
    else:
        print_error(f"Failed to add reaction: {response1.status_code}")
        return
    
    # Second: Toggle off (remove)
    response2 = client.post(
        f'/api/chat/message/{message_id}/react/',
        data=json.dumps(payload),
        content_type='application/json',
        **auth
    )
    
    if response2.status_code == 204:
        print_success("Reaction removed (toggled off)")
    else:
        print_error(f"Failed to toggle reaction: {response2.status_code}")

def main():
    """Run all tests"""
    print("\n" + "█"*60)
    print("█  FOFOFISH CHAT API TEST SUITE")
    print("█"*60)
    
    try:
        # Setup
        users = setup_test_data()
        client = Client()
        
        # Run tests
        test_chat_history(client, users)
        msg_id_1 = test_send_text_message(client, users)
        msg_id_2 = test_send_with_file(client, users)
        test_add_reaction(client, users, msg_id_1)
        test_add_multiple_reactions(client, users, msg_id_1)
        test_list_participants(client, users)
        test_permission_denied(client, users)
        test_invalid_message_type(client, users)
        test_support_chat(client, users)
        test_reaction_toggle(client, users, msg_id_1)
        
        print_header("✅ ALL TESTS COMPLETED")
        
    except Exception as e:
        print_error(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
