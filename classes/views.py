from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

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


class OnlineClassViewSet(viewsets.ModelViewSet):
    serializer_class = OnlineClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = OnlineClass.objects.select_related('teacher').prefetch_related('enrollments')
        if is_teacher(user):
            return queryset.filter(teacher=user)
        return queryset.filter(enrollments__student=user, enrollments__left_at__isnull=True).distinct()

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
        is_teacher = class_instance.teacher_id == user.id
        enrollment = None
        if not is_teacher:
            enrollment = ClassEnrollment.objects.filter(
                class_session=class_instance,
                student=user,
                left_at__isnull=True,
            ).first()
        return is_teacher, enrollment

    def _ensure_participant(self, class_instance):
        is_teacher, enrollment = self._get_participant_context(class_instance)
        if not is_teacher and enrollment is None:
            return None, None, Response({'error': 'Not enrolled'}, status=status.HTTP_403_FORBIDDEN)
        return is_teacher, enrollment, None

    def _ensure_teacher(self, class_instance):
        if class_instance.teacher_id != self.request.user.id:
            return Response({'error': 'Only class teacher can perform this action'}, status=status.HTTP_403_FORBIDDEN)
        return None

    def _participants(self, class_instance):
        participants = self._participants(class_instance)
        student_joined.send(sender=ClassEnrollment, class_instance=class_instance, student=user)
        return participants

    def _participant_payload(self, user, role, enrollment=None):
        return {
            'id': str(user.id),
            'user': UserBasicSerializer(user).data,
            'role': role,
            'isHandRaised': HandRaise.objects.filter(student=user, lowered_at__isnull=True).exists(),
            'isMuted': True,
            'isVideoOn': False,
            'isScreenSharing': False,
            'isSpotlighted': False,
            'canUnmute': True if role == 'teacher' else bool(enrollment and enrollment.can_unmute),
            'canShareVideo': True if role == 'teacher' else bool(enrollment and enrollment.can_share_video),
            'canShareScreen': True if role == 'teacher' else bool(enrollment and enrollment.can_share_screen),
            'canDrawOnWhiteboard': role == 'teacher',
        }


    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        class_instance.start()
        data = OnlineClassSerializer(class_instance, context={'request': request}).data
        publish_to_class(str(class_instance.id), 'class.started', data)
        class_started.send(sender=OnlineClass, class_instance=class_instance)
        return Response(data)

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        class_instance.end()
        data = OnlineClassSerializer(class_instance, context={'request': request}).data
        publish_to_class(str(class_instance.id), 'class.ended', data)
        class_ended.send(sender=OnlineClass, class_instance=class_instance, duration_minutes=class_instance.actual_duration_minutes)
        return Response(data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        class_instance = self.get_object()
        teacher_error = self._ensure_teacher(class_instance)
        if teacher_error:
            return teacher_error
        class_instance.cancel()
        data = OnlineClassSerializer(class_instance, context={'request': request}).data
        publish_to_class(str(class_instance.id), 'class.cancelled', data)
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
                'can_share_video': serializer.validated_data.get('can_share_video', True),
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
        is_teacher, enrollment, error = self._ensure_participant(class_instance)
        if error:
            return error

        user = request.user
        role = 'teacher' if is_teacher else 'student'
        if enrollment:
            enrollment.join()

        if is_teacher:
            permissions = {
                'consume': True,
                'produceAudio': True,
                'produceVideo': True,
                'produceScreen': True,
                'manageRecording': True,
            }
        else:
            permissions = {
                'consume': True,
                'produceAudio': enrollment.can_unmute,
                'produceVideo': enrollment.can_share_video,
                'produceScreen': enrollment.can_share_screen,
                'manageRecording': False,
            }

        publish_to_class(str(class_instance.id), 'participant.joined', self._participant_payload(user, role, enrollment))
        participants = self._participants(class_instance)
        student_joined.send(sender=ClassEnrollment, class_instance=class_instance, student=user)

        return Response({
            'class': OnlineClassSerializer(class_instance, context={'request': request}).data,
            'rtc': {
                'token': generate_rtc_token(user.id, class_instance.room_id, permissions),
                'wsUrl': conf.RTC_WS_URL,
                'roomId': str(class_instance.room_id),
                'iceServers': conf.RTC_ICE_SERVERS,
                'permissions': permissions,
            },
            'realtime': {
                'token': generate_centrifugo_connection_token(user.id),
                'wsUrl': conf.CENTRIFUGO_WS_URL,
                'channels': [f'class:{class_instance.id}', f'$user:{user.id}'],
            },
            'whiteboard': {
                'subscriptionToken': generate_whiteboard_subscription_token(user.id, str(class_instance.id), is_teacher),
                'canDraw': is_teacher,
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
        is_teacher, _, error = self._ensure_participant(class_instance)
        if error:
            return error

        if request.method == 'GET':
            limit = int(request.query_params.get('limit', conf.MESSAGE_HISTORY_LIMIT))
            limit = max(1, min(limit, conf.MESSAGE_HISTORY_LIMIT))
            messages = class_instance.messages.select_related('sender', 'recipient').filter(is_deleted=False).order_by('-created_at')[:limit]
            return Response({'results': ClassMessageSerializer(reversed(list(messages)), many=True).data})

        if not is_teacher and not class_instance.allow_student_chat:
            return Response({'error': 'Student chat is disabled'}, status=status.HTTP_403_FORBIDDEN)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'content': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)

        message = ClassMessage.objects.create(class_session=class_instance, sender=request.user, content=content)
        message_data = ClassMessageSerializer(message).data
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
        is_teacher, _, error = self._ensure_participant(class_instance)
        if error:
            return error
        if is_teacher:
            return Response({'error': 'Teacher cannot raise hand'}, status=status.HTTP_400_BAD_REQUEST)

        hand = HandRaise.objects.filter(class_session=class_instance, student=request.user, lowered_at__isnull=True).first()
        if hand is None:
            hand = HandRaise.objects.create(class_session=class_instance, student=request.user)
        hand_data = HandRaiseSerializer(hand).data
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
        return Response(HandRaiseSerializer(hand).data)

    @action(detail=True, methods=['get'], url_path='hands')
    def hand_queue(self, request, pk=None):
        class_instance = self.get_object()
        _, _, error = self._ensure_participant(class_instance)
        if error:
            return error
        hands = HandRaise.objects.select_related('student', 'acknowledged_by').filter(class_session=class_instance, lowered_at__isnull=True)
        return Response({'results': HandRaiseSerializer(hands, many=True).data})

    @action(detail=True, methods=['post'], url_path='reactions')
    def send_reaction(self, request, pk=None):
        class_instance = self.get_object()
        is_teacher, _, error = self._ensure_participant(class_instance)
        if error:
            return error
        if not is_teacher and not class_instance.allow_student_reactions:
            return Response({'error': 'Student reactions are disabled'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ClassReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reaction = ClassReaction.objects.create(
            class_session=class_instance,
            student=request.user,
            emoji=serializer.validated_data['emoji'],
            message=serializer.validated_data.get('message'),
        )
        reaction_data = ClassReactionSerializer(reaction).data
        publish_to_class(str(class_instance.id), 'reaction.added', reaction_data)
        reaction_sent.send(sender=ClassReaction, class_instance=class_instance, reaction=reaction)
        return Response(reaction_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='grant-mic/(?P<user_id>[^/.]+)')
    def grant_mic(self, request, pk=None, user_id=None):
        return self._update_student_permission(pk, user_id, 'can_unmute', True, 'mic.granted', 'canUnmute')

    @action(detail=True, methods=['post'], url_path='revoke-mic/(?P<user_id>[^/.]+)')
    def revoke_mic(self, request, pk=None, user_id=None):
        return self._update_student_permission(pk, user_id, 'can_unmute', False, 'mic.revoked', 'canUnmute')

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

