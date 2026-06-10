import logging

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from zoneinfo import ZoneInfo
from . import conf
from .broadcast import publish_to_class, publish_to_user
from .models import ClassEnrollment, ClassMessage, ClassReaction, HandRaise, OnlineClass
from .serializers import (
    ClassEnrollmentSerializer,
    ClassMessageSerializer,
    ClassReactionSerializer,
    HandRaiseSerializer,
    OnlineClassSerializer,
    UserBasicSerializer,
    NextOnlineClassSerializer
)
from .signals import (
    class_cancelled,
    class_created,
    class_ended,
    class_started,
    hand_acknowledged,
    hand_lowered,
    hand_raised,
    message_deleted,
    message_sent,
    mic_granted,
    mic_revoked,
    reaction_sent,
    student_enrolled,
    student_joined,
    student_kicked,
    student_left,
    student_spotlighted,
)
from .tokens import (
    generate_centrifugo_connection_token,
    generate_rtc_token,
    generate_whiteboard_subscription_token,
)
from .utils import is_teacher


User = get_user_model()
logger = logging.getLogger(__name__)


class OnlineClassViewSet(viewsets.ModelViewSet):
    serializer_class = OnlineClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = OnlineClass.objects.select_related('teacher').prefetch_related('enrollments')
        if is_teacher(user):
            return queryset.filter(teacher=user)
        return queryset.filter(enrollments__student=user).distinct()

    def perform_create(self, serializer):
        teacher = serializer.validated_data.get('teacher') or self.request.user
        if not is_teacher(self.request.user) and teacher != self.request.user:
            raise PermissionDenied('Only teachers can create online classes.')
        if not is_teacher(teacher):
            raise PermissionDenied('Class owner must be a teacher.')
        class_instance = serializer.save(teacher=teacher)
        class_created.send(sender=OnlineClass, class_instance=class_instance, created_by=self.request.user)

    def _get_participant_context(self, class_instance):
        user = self.request.user
        teacher_participant = class_instance.teacher_id == user.id
        enrollment = None
        if not teacher_participant:
            enrollment = ClassEnrollment.objects.filter(
                class_session=class_instance,
                student=user,
                left_at__isnull=True,
            ).first()
        return teacher_participant, enrollment

    def _ensure_participant(self, class_instance):
        teacher_participant, enrollment = self._get_participant_context(class_instance)
        if not teacher_participant and enrollment is None:
            return None, None, Response({'error': 'Not enrolled'}, status=status.HTTP_403_FORBIDDEN)
        return teacher_participant, enrollment, None

    def _ensure_teacher(self, class_instance):
        if class_instance.teacher_id != self.request.user.id:
            return Response({'error': 'Only class teacher can perform this action'}, status=status.HTTP_403_FORBIDDEN)
        return None

    def _ensure_joinable(self, class_instance):
        if class_instance.status != OnlineClass.STATUS_ACTIVE:
            return Response({'error': 'Only active classes can be joined'}, status=status.HTTP_400_BAD_REQUEST)
        return None

    def _class_payload(self, class_instance):
        return {
            'id': str(class_instance.id),
            'title': class_instance.title,
            'description': class_instance.description,
            'teacher': UserBasicSerializer(class_instance.teacher).data,
            'status': class_instance.status,
            'settings': {
                'allowStudentChat': class_instance.allow_student_chat,
                'allowStudentReactions': class_instance.allow_student_reactions,
                'allowStudentVideo': True,
                'enableRecording': class_instance.enable_recording,
                'requireApprovalToJoin': class_instance.require_approval_to_join,
            },
            'scheduledStart': class_instance.scheduled_start.isoformat() if class_instance.scheduled_start else None,
            'scheduledEnd': class_instance.scheduled_end.isoformat() if class_instance.scheduled_end else None,
            'actualStart': class_instance.actual_start.isoformat() if class_instance.actual_start else None,
            'actualEnd': class_instance.actual_end.isoformat() if class_instance.actual_end else None,
            'roomId': str(class_instance.room_id),
            'enrolledCount': class_instance.enrolled_count,
            'maxStudents': class_instance.max_students,
        }

    def _message_payload(self, message):
        return {
            'id': str(message.id),
            'sender': UserBasicSerializer(message.sender).data,
            'content': message.content,
            'isPrivate': message.is_private,
            'recipient': UserBasicSerializer(message.recipient).data if message.recipient else None,
            'isDeleted': message.is_deleted,
            'deletedBy': UserBasicSerializer(message.deleted_by).data if message.deleted_by else None,
            'deletedAt': message.deleted_at.isoformat() if message.deleted_at else None,
            'createdAt': message.created_at.isoformat() if message.created_at else None,
        }

    def _hand_payload(self, hand):
        return {
            'id': str(hand.id),
            'student': UserBasicSerializer(hand.student).data,
            'raisedAt': hand.raised_at.isoformat() if hand.raised_at else None,
            'loweredAt': hand.lowered_at.isoformat() if hand.lowered_at else None,
            'acknowledgedBy': UserBasicSerializer(hand.acknowledged_by).data if hand.acknowledged_by else None,
            'acknowledgedAt': hand.acknowledged_at.isoformat() if hand.acknowledged_at else None,
            'isActive': hand.lowered_at is None,
            'isAcknowledged': hand.acknowledged_at is not None,
            'durationSeconds': hand.duration_seconds,
        }

    def _participant_payload(self, user, role, enrollment=None, class_instance=None):
        if class_instance is None and enrollment is not None:
            class_instance = enrollment.class_session
        return {
            'id': str(user.id),
            'user': UserBasicSerializer(user).data,
            'role': role,
            'isHandRaised': HandRaise.objects.filter(
                class_session=class_instance,
                student=user,
                lowered_at__isnull=True,
            ).exists() if class_instance else False,
            'isMuted': True,
            'isVideoOn': False,
            'isScreenSharing': False,
            'isSpotlighted': False,
            'canUnmute': True if role == 'teacher' else bool(enrollment and enrollment.can_unmute),
            'canShareVideo': True if role == 'teacher' else bool(enrollment and enrollment.can_share_video),
            'canShareScreen': True if role == 'teacher' else bool(enrollment and enrollment.can_share_screen),
            'canDrawOnWhiteboard': role == 'teacher',
        }

    def _participants(self, class_instance):
        participants = [
            self._participant_payload(class_instance.teacher, 'teacher', class_instance=class_instance),
        ]
        enrollments = class_instance.enrollments.select_related('student').filter(left_at__isnull=True)
        for enrollment in enrollments:
            participants.append(self._participant_payload(enrollment.student, 'student', enrollment, class_instance))
        return participants

    @action(detail=False, methods=['post'], url_path='reset')
    def reset_sessions(self, request):
        ClassEnrollment.objects.update(joined_at=None, left_at=None)
        HandRaise.objects.all().delete()
        return Response({'ok': True, 'message': 'All sessions cleared'})

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        try:
            class_instance.start()
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        data = OnlineClassSerializer(class_instance, context={'request': request}).data
        publish_to_class(str(class_instance.id), 'class.started', self._class_payload(class_instance))
        class_started.send(sender=OnlineClass, class_instance=class_instance)
        return Response(data)

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        try:
            class_instance.end()
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        data = OnlineClassSerializer(class_instance, context={'request': request}).data
        publish_to_class(str(class_instance.id), 'class.ended', self._class_payload(class_instance))
        class_ended.send(sender=OnlineClass, class_instance=class_instance, duration_minutes=class_instance.actual_duration_minutes)
        return Response(data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        try:
            class_instance.cancel()
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        data = OnlineClassSerializer(class_instance, context={'request': request}).data
        publish_to_class(str(class_instance.id), 'class.cancelled', self._class_payload(class_instance))
        class_cancelled.send(sender=OnlineClass, class_instance=class_instance, cancelled_by=request.user)
        return Response(data)

    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        class_instance = self.get_object()
        _, _, error = self._ensure_participant(class_instance)
        if error:
            return error
        return Response({'results': self._participants(class_instance)})

    @action(detail=True, methods=['get'])
    def enrollments(self, request, pk=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        enrollments = class_instance.enrollments.select_related('student').all()
        return Response({'results': ClassEnrollmentSerializer(enrollments, many=True).data})

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error

        serializer = ClassEnrollmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.validated_data.get('student')
        if not student:
            return Response({'student_id': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if class_instance.is_full:
            return Response({'error': 'Class is full'}, status=status.HTTP_400_BAD_REQUEST)

        enrollment, created = ClassEnrollment.objects.update_or_create(
            class_session=class_instance,
            student=student,
            defaults={
                'can_unmute': serializer.validated_data.get('can_unmute', False),
                'can_share_video': serializer.validated_data.get('can_share_video', False),
                'can_share_screen': serializer.validated_data.get('can_share_screen', False),
                'is_moderator': serializer.validated_data.get('is_moderator', False),
                'left_at': None,
            },
        )
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        student_enrolled.send(sender=ClassEnrollment, class_instance=class_instance, student=student)
        publish_to_user(student.id, 'class.enrolled', {'class_id': str(class_instance.id)})
        return Response(ClassEnrollmentSerializer(enrollment).data, status=response_status)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        class_instance = self.get_object()
        user = request.user
        
        # Check if teacher
        teacher_participant = class_instance.teacher_id == user.id
        enrollment = None
        
        if not teacher_participant:
            # Look for any enrollment (including previously left ones) to allow rejoin
            enrollment = ClassEnrollment.objects.filter(
                class_session=class_instance,
                student=user,
            ).first()
            
            if enrollment and enrollment.left_at is not None:
                # Re-activate the enrollment (allow rejoin)
                enrollment.left_at = None
                enrollment.save(update_fields=['left_at'])
            
            if not enrollment:
                return Response({'error': 'Not enrolled'}, status=status.HTTP_403_FORBIDDEN)
        
        joinable_error = self._ensure_joinable(class_instance)
        if joinable_error:
            return joinable_error

        role = 'teacher' if teacher_participant else 'student'
        if enrollment:
            enrollment.join()

        if teacher_participant:
            permissions = {
                'consume': True,
                'produceAudio': True,
                'produceVideo': True,
                'produceScreen': True,
                'manageRecording': True,
            }
            can_draw = True
        else:
            permissions = {
                'consume': True,
                'produceAudio': enrollment.can_unmute,
                'produceVideo': enrollment.can_share_video,
                'produceScreen': enrollment.can_share_screen,
                'manageRecording': False,
            }
            can_draw = False

        publish_to_class(
            str(class_instance.id),
            'participant.joined',
            self._participant_payload(user, role, enrollment, class_instance=class_instance),
        )
        participants = self._participants(class_instance)
        student_joined.send(sender=ClassEnrollment, class_instance=class_instance, student=user)

        return Response({
            'class': self._class_payload(class_instance),
            'rtc': {
                'token': generate_rtc_token(
                    user.id,
                    class_instance.room_id,
                    permissions,
                    call_id=class_instance.id,
                    session_id=f'{class_instance.id}:{user.id}',
                    call_type='classroom',
                ),
                'wsUrl': conf.RTC_WS_URL,
                'roomId': str(class_instance.room_id),
                'iceServers': conf.RTC_ICE_SERVERS,
                'permissions': permissions,
            },
            'realtime': {
                'token': generate_centrifugo_connection_token(user.id),
                'wsUrl': conf.CENTRIFUGO_WS_URL,
                'channels': [
                    f'class:{class_instance.id}',
                    f'user:{user.id}',
                    *([f'class:{class_instance.id}:control'] if teacher_participant else []),
                ],
            },
            'whiteboard': {
                'subscriptionToken': generate_whiteboard_subscription_token(user.id, str(class_instance.id), can_draw),
                'channel': f'whiteboard:class:{class_instance.id}',
                'canDraw': can_draw,
            },
            'user': UserBasicSerializer(user).data,
            'participants': participants,
        })

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        class_instance = self.get_object()
        _, enrollment, error = self._ensure_participant(class_instance)
        if error:
            return error
        if enrollment:
            enrollment.leave()
        publish_to_class(str(class_instance.id), 'participant.left', {'user_id': str(request.user.id)})
        student_left.send(sender=ClassEnrollment, class_instance=class_instance, student=request.user)
        return Response({'ok': True})

    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        class_instance = self.get_object()
        is_teacher_user, _, error = self._ensure_participant(class_instance)
        if error:
            return error

        if request.method == 'GET':
            limit = int(request.query_params.get('limit', conf.MESSAGE_HISTORY_LIMIT))
            limit = max(1, min(limit, conf.MESSAGE_HISTORY_LIMIT))
            messages = class_instance.messages.select_related('sender', 'recipient', 'deleted_by').filter(
                is_deleted=False,
            ).filter(
                Q(is_private=False)
                | Q(sender=request.user)
                | Q(recipient=request.user)
                | Q(class_session__teacher=request.user)
            ).order_by('-created_at')[:limit]
            return Response({'results': [self._message_payload(message) for message in reversed(list(messages))]})

        if not is_teacher_user and not class_instance.allow_student_chat:
            return Response({'error': 'Student chat is disabled'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ClassMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        content = serializer.validated_data.get('content', '').strip()
        if not content:
            raise ValidationError({'content': 'This field is required.'})

        recipient = serializer.validated_data.get('recipient')
        is_private = serializer.validated_data.get('is_private', False)
        if recipient and recipient == request.user:
            raise ValidationError({'recipient_id': 'Recipient must be another user.'})
        if is_private and recipient:
            allowed_user_ids = {class_instance.teacher_id}
            allowed_user_ids.update(class_instance.enrollments.filter(left_at__isnull=True).values_list('student_id', flat=True))
            if recipient.id not in allowed_user_ids:
                raise ValidationError({'recipient_id': 'Recipient must be a class participant.'})

        message = ClassMessage.objects.create(
            class_session=class_instance,
            sender=request.user,
            content=content,
            is_private=is_private,
            recipient=recipient,
        )
        message_data = self._message_payload(message)
        publish_to_class(str(class_instance.id), 'chat.message', message_data)
        message_sent.send(sender=ClassMessage, class_instance=class_instance, message=message)
        return Response(message_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='messages/(?P<message_id>[^/.]+)')
    def delete_message(self, request, pk=None, message_id=None):
        class_instance = self.get_object()
        message = ClassMessage.objects.filter(class_session=class_instance, pk=message_id).first()
        if not message:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
        if message.sender_id != request.user.id and class_instance.teacher_id != request.user.id:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        message.soft_delete(request.user)
        publish_to_class(str(class_instance.id), 'chat.deleted', {'message_id': str(message.id)})
        message_deleted.send(sender=ClassMessage, class_instance=class_instance, message=message, deleted_by=request.user)
        return Response({'ok': True})

    @action(detail=True, methods=['post'], url_path='hand/raise')
    def raise_hand(self, request, pk=None):
        class_instance = self.get_object()
        is_teacher_user, _, error = self._ensure_participant(class_instance)
        if error:
            return error
        if is_teacher_user:
            return Response({'error': 'Teacher cannot raise hand'}, status=status.HTTP_400_BAD_REQUEST)

        hand = HandRaise.objects.filter(class_session=class_instance, student=request.user, lowered_at__isnull=True).first()
        if hand is None:
            hand = HandRaise.objects.create(class_session=class_instance, student=request.user)
        hand_data = self._hand_payload(hand)
        publish_to_class(str(class_instance.id), 'hand.raised', hand_data)
        hand_raised.send(sender=HandRaise, class_instance=class_instance, student=request.user, hand_raise=hand)
        return Response(hand_data)

    @action(detail=True, methods=['post'], url_path='hand/lower')
    def lower_hand(self, request, pk=None):
        class_instance = self.get_object()
        _, _, error = self._ensure_participant(class_instance)
        if error:
            return error
        HandRaise.objects.filter(class_session=class_instance, student=request.user, lowered_at__isnull=True).update(lowered_at=timezone.now())
        publish_to_class(str(class_instance.id), 'hand.lowered', {'user_id': str(request.user.id)})
        hand_lowered.send(sender=HandRaise, class_instance=class_instance, student=request.user, hand_raise=None)
        return Response({'ok': True})

    @action(detail=True, methods=['post'], url_path='hands/(?P<user_id>[^/.]+)/acknowledge')
    def acknowledge_hand(self, request, pk=None, user_id=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        hand = HandRaise.objects.filter(class_session=class_instance, student_id=user_id, lowered_at__isnull=True).first()
        if not hand:
            return Response({'error': 'Active hand raise not found'}, status=status.HTTP_404_NOT_FOUND)
        hand.acknowledge(request.user)
        publish_to_class(str(class_instance.id), 'hand.acknowledged', {
            'user_id': str(user_id),
            'acknowledged_by': UserBasicSerializer(request.user).data,
        })
        hand_acknowledged.send(sender=HandRaise, class_instance=class_instance, student=hand.student, hand_raise=hand, acknowledged_by=request.user)
        return Response(self._hand_payload(hand))

    @action(detail=True, methods=['get'], url_path='hands')
    def hand_queue(self, request, pk=None):
        class_instance = self.get_object()
        _, _, error = self._ensure_participant(class_instance)
        if error:
            return error
        hands = HandRaise.objects.select_related('student', 'acknowledged_by').filter(class_session=class_instance, lowered_at__isnull=True)
        return Response({'results': [self._hand_payload(hand) for hand in hands]})

    @action(detail=True, methods=['post'], url_path='reactions')
    def send_reaction(self, request, pk=None):
        class_instance = self.get_object()
        is_teacher_user, _, error = self._ensure_participant(class_instance)
        if error:
            return error
        if not is_teacher_user and not class_instance.allow_student_reactions:
            return Response({'error': 'Student reactions are disabled'}, status=status.HTTP_403_FORBIDDEN)
        if conf.REACTION_RATE_LIMIT:
            recent_reactions = ClassReaction.objects.filter(
                class_session=class_instance,
                student=request.user,
                created_at__gte=timezone.now() - timezone.timedelta(minutes=1),
            ).count()
            if recent_reactions >= conf.REACTION_RATE_LIMIT:
                return Response({'error': 'Reaction rate limit exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        serializer = ClassReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reaction = ClassReaction.objects.create(
            class_session=class_instance,
            student=request.user,
            emoji=serializer.validated_data['emoji'],
            message=serializer.validated_data.get('message'),
        )
        reaction_data = {
            'user': UserBasicSerializer(request.user).data,
            'emoji': reaction.emoji,
            'timestamp': reaction.created_at.isoformat() if reaction.created_at else None,
        }
        publish_to_class(str(class_instance.id), 'reaction.added', reaction_data)
        reaction_sent.send(sender=ClassReaction, class_instance=class_instance, reaction=reaction)
        return Response({'ok': True})

    @action(detail=True, methods=['post'], url_path='grant-mic/(?P<user_id>[^/.]+)')
    def grant_mic(self, request, pk=None, user_id=None):
        return self._update_student_permission(pk, user_id, 'can_unmute', True, 'mic.granted', 'canUnmute')

    @action(detail=True, methods=['post'], url_path='revoke-mic/(?P<user_id>[^/.]+)')
    def revoke_mic(self, request, pk=None, user_id=None):
        return self._update_student_permission(pk, user_id, 'can_unmute', False, 'mic.revoked', 'canUnmute')

    @action(detail=True, methods=['post'], url_path='grant-camera/(?P<user_id>[^/.]+)')
    def grant_camera(self, request, pk=None, user_id=None):
        return self._update_student_permission(pk, user_id, 'can_share_video', True, 'camera.granted', 'canShareVideo')

    @action(detail=True, methods=['post'], url_path='revoke-camera/(?P<user_id>[^/.]+)')
    def revoke_camera(self, request, pk=None, user_id=None):
        return self._update_student_permission(pk, user_id, 'can_share_video', False, 'camera.revoked', 'canShareVideo')

    @action(detail=True, methods=['post'], url_path='grant-screen/(?P<user_id>[^/.]+)')
    def grant_screen(self, request, pk=None, user_id=None):
        return self._update_student_permission(pk, user_id, 'can_share_screen', True, 'screen.granted', 'canShareScreen')

    @action(detail=True, methods=['post'], url_path='revoke-screen/(?P<user_id>[^/.]+)')
    def revoke_screen(self, request, pk=None, user_id=None):
        return self._update_student_permission(pk, user_id, 'can_share_screen', False, 'screen.revoked', 'canShareScreen')

    def _update_student_permission(self, pk, user_id, field, value, private_event, public_field):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        updated = ClassEnrollment.objects.filter(class_session=class_instance, student_id=user_id).update(**{field: value})
        if not updated:
            return Response({'error': 'Enrollment not found'}, status=status.HTTP_404_NOT_FOUND)
        publish_to_user(user_id, private_event, {'class_id': str(pk)})
        publish_to_class(str(pk), 'participant.updated', {'user_id': str(user_id), public_field: value})
        signal = mic_granted if value else mic_revoked
        signal.send(sender=ClassEnrollment, class_instance=class_instance, student_id=user_id, granted_by=self.request.user, revoked_by=self.request.user)
        return Response({'ok': True})

    @action(detail=True, methods=['post'], url_path='kick/(?P<user_id>[^/.]+)')
    def kick_user(self, request, pk=None, user_id=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        if str(class_instance.teacher_id) == str(user_id):
            return Response({'error': 'Teacher cannot be kicked'}, status=status.HTTP_400_BAD_REQUEST)
        reason = request.data.get('reason', '')
        updated = ClassEnrollment.objects.filter(class_session=class_instance, student_id=user_id).update(left_at=timezone.now())
        if not updated:
            return Response({'error': 'Enrollment not found'}, status=status.HTTP_404_NOT_FOUND)
        publish_to_user(user_id, 'kicked', {'class_id': str(pk), 'reason': reason})
        publish_to_class(str(pk), 'participant.left', {'user_id': str(user_id)})
        student_kicked.send(sender=ClassEnrollment, class_instance=class_instance, student_id=user_id, kicked_by=request.user, reason=reason)
        return Response({'ok': True})

    @action(detail=True, methods=['post'], url_path='spotlight/(?P<user_id>[^/.]+)')
    def spotlight_user(self, request, pk=None, user_id=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        publish_to_class(str(pk), 'spotlight.changed', {'user_id': str(user_id)})
        publish_to_user(user_id, 'spotlight.enabled', {'class_id': str(pk)})
        student_spotlighted.send(sender=OnlineClass, class_instance=class_instance, student_id=user_id, spotlighted_by=request.user)
        return Response({'ok': True})

    @action(detail=True, methods=['post'], url_path='whiteboard/grant/(?P<user_id>[^/.]+)')
    def whiteboard_grant(self, request, pk=None, user_id=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        publish_to_user(user_id, 'whiteboard.granted', {'class_id': str(pk)})
        publish_to_class(str(pk), 'whiteboard.permission_changed', {'user_id': str(user_id), 'can_draw': True})
        return Response({'ok': True})

    @action(detail=True, methods=['post'], url_path='whiteboard/revoke/(?P<user_id>[^/.]+)')
    def whiteboard_revoke(self, request, pk=None, user_id=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        publish_to_user(user_id, 'whiteboard.revoked', {'class_id': str(pk)})
        publish_to_class(str(pk), 'whiteboard.permission_changed', {'user_id': str(user_id), 'can_draw': False})
        return Response({'ok': True})

    @action(detail=True, methods=['post'], url_path='whiteboard/clear')
    def whiteboard_clear(self, request, pk=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        publish_to_class(str(pk), 'whiteboard.cleared', {})
        return Response({'ok': True})
    
    @action(detail=False, methods=['get'], url_path='next')
    def next_class(self, request):
            user = request.user

            if getattr(user, 'role', None) != 'user':
                return Response(
                    {'detail': 'Only students can use this endpoint.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

            now_tehran = timezone.now().astimezone(
                ZoneInfo("Asia/Tehran")
            )

            active_class = (
                OnlineClass.objects
                .filter(
                    booking__student=user,
                    status=OnlineClass.STATUS_ACTIVE,
                )
                .select_related(
                    'teacher',
                    'booking',
                    'booking__availability',
                )
                .first()
            )

            if active_class:
                next_class = active_class
            else:
                next_class = (
                    OnlineClass.objects
                    .filter(
                        booking__student=user,
                        status=OnlineClass.STATUS_SCHEDULED,
                        scheduled_start__gt=now_tehran,
                    )
                    .select_related(
                        'teacher',
                        'booking',
                        'booking__availability',
                    )
                    .order_by('scheduled_start')
                    .first()
                )

            if not next_class:
                return Response(
                    {'detail': 'No upcoming class found.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = NextOnlineClassSerializer(
                next_class,
                context={'request': request},
            )

            return Response(serializer.data)

# ========== Internal RTC Events API View ==========
import hashlib
import hmac
import time
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.conf import settings

class InternalRTCEventAPIView(APIView):
    """
    Internal endpoint for RTC server to notify about participant presence events.
    This endpoint is called by the mediasoup RTC server when participants join/leave.
    """
    permission_classes = [AllowAny]  # Internal endpoint, secured by signature
    
    def verify_signature(self, timestamp, signature, raw_body):
        """Verify HMAC-SHA256 signature from RTC server."""
        secret = getattr(settings, 'INTERNAL_CALLBACK_SECRET', None)
        if not secret:
            logger.warning('INTERNAL_CALLBACK_SECRET not set, signature verification disabled')
            return True  # Allow if no secret configured
        
        # Check timestamp (prevent replay attacks)
        current_time = int(time.time())
        if abs(current_time - int(timestamp)) > 300:  # 5 minutes tolerance
            logger.warning(f'Timestamp expired: {timestamp}, current: {current_time}')
            return False
        
        # Compute expected signature
        message = f'{timestamp}.{raw_body}'
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)
    
    def post(self, request):
        """Handle RTC presence events."""
        # Get signature headers
        timestamp = request.headers.get('x-internal-timestamp')
        signature = request.headers.get('x-internal-signature')
        
        if not timestamp or not signature:
            logger.warning('Missing signature headers in RTC event request')
            return Response({'error': 'Missing signature headers'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Verify signature
        raw_body = request.body.decode('utf-8')
        if not self.verify_signature(timestamp, signature, raw_body):
            logger.warning(f'Invalid signature for RTC event: {request.data}')
            return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Process the event
        data = request.data
        event_type = data.get('event')
        call_id = data.get('call_id')
        room_id = data.get('room_id')
        user_id = data.get('user_id')
        peer_id = data.get('peer_id')
        
        logger.info(f'RTC event received: {event_type} call_id={call_id} room_id={room_id} user_id={user_id} peer_id={peer_id}')
        
        # Handle different event types
        if event_type == 'participant_joined':
            # Participant joined the RTC room
            # You could update database or trigger other actions here
            pass
        elif event_type == 'participant_left':
            # Participant left the RTC room
            pass
        
        # Always return success for now
        return Response({'ok': True, 'received': True})
