# Online Class Architecture Proposal

## Overview
Extend the existing video-call infrastructure to support online classroom features using Centrifugo for all realtime interactions.

## Architecture Components

### 1. Media Layer (Mediasoup - video-call-server)
**Unchanged - already handles:**
- Audio/video streaming
- Screen sharing
- Recording capabilities
- SFU routing (Selective Forwarding Unit)
- Simulcast for quality adaptation

**Permissions to add:**
```javascript
// Extended permissions in RTC token
{
  consume: true,              // Watch streams
  produceAudio: false,        // Muted by default for students
  produceVideo: true,         // Camera allowed
  produceScreen: false,       // Screen sharing (teacher only)
  manageRecording: false      // Recording controls (teacher only)
}
```

### 2. Realtime Layer (Centrifugo)
**New service for all classroom interactions**

#### Channel Structure

```javascript
// Main classroom channel - all participants
class:{class_id}
  Events:
    - chat.message
    - reaction.added (👍, ❤️, 👏, 🎉, 🤔, 😮)
    - hand.raised
    - hand.lowered
    - poll.started
    - poll.response
    - screen_share.started
    - screen_share.stopped
    - breakout.assigned

// Teacher control channel
class:{class_id}:control
  Events (teacher-only):
    - hand_queue.updated
    - moderation.flag
    - attendance.updated

// Personal student channel
$user:{user_id}
  Events (private):
    - mic.granted
    - mic.revoked
    - spotlight.enabled
    - kicked
    - breakout.moved
    - question.answered
```

### 3. Control Layer (Django - video-call-control)
**Extended models and APIs**

#### New Models

```python
# django-project/loop/models.py additions

class OnlineClass(models.Model):
    """Scheduled class session"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    teacher = models.ForeignKey(User, related_name='classes_teaching')
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True)
    actual_end = models.DateTimeField(null=True)
    
    # Mediasoup room
    room_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Settings
    max_students = models.IntegerField(default=100)
    allow_student_chat = models.BooleanField(default=True)
    allow_student_reactions = models.BooleanField(default=True)
    require_approval_to_join = models.BooleanField(default=False)
    enable_recording = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled')
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)


class ClassEnrollment(models.Model):
    """Student enrollment in class"""
    class_session = models.ForeignKey(OnlineClass, related_name='enrollments')
    student = models.ForeignKey(User, related_name='enrolled_classes')
    
    # Permissions
    can_unmute = models.BooleanField(default=False)
    can_share_video = models.BooleanField(default=True)
    is_moderator = models.BooleanField(default=False)
    
    # Status
    joined_at = models.DateTimeField(null=True)
    left_at = models.DateTimeField(null=True)
    
    class Meta:
        unique_together = ('class_session', 'student')


class HandRaise(models.Model):
    """Track raised hands queue"""
    class_session = models.ForeignKey(OnlineClass, related_name='raised_hands')
    student = models.ForeignKey(User, related_name='hand_raises')
    raised_at = models.DateTimeField(auto_now_add=True)
    lowered_at = models.DateTimeField(null=True)
    acknowledged_by = models.ForeignKey(User, null=True, related_name='acknowledged_hands')
    acknowledged_at = models.DateTimeField(null=True)
    
    class Meta:
        ordering = ['raised_at']


class ClassMessage(models.Model):
    """Class chat messages"""
    class_session = models.ForeignKey(OnlineClass, related_name='messages')
    sender = models.ForeignKey(User, related_name='class_messages')
    content = models.TextField()
    
    # Optional private message to teacher
    is_private = models.BooleanField(default=False)
    recipient = models.ForeignKey(User, null=True, related_name='received_class_messages')
    
    # Moderation
    is_deleted = models.BooleanField(default=False)
    deleted_by = models.ForeignKey(User, null=True, related_name='deleted_class_messages')
    deleted_at = models.DateTimeField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)


class ClassReaction(models.Model):
    """Real-time reactions during class"""
    class_session = models.ForeignKey(OnlineClass, related_name='reactions')
    student = models.ForeignKey(User, related_name='class_reactions')
    emoji = models.CharField(max_length=10)  # 👍, ❤️, 👏, 🎉, 🤔, 😮
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: react to specific message
    message = models.ForeignKey(ClassMessage, null=True, related_name='reactions')
```

#### API Endpoints

```python
# django-project/loop/views_classes.py

# Class management
POST   /api/v1/classes/                      # Create class
GET    /api/v1/classes/                      # List my classes (as teacher or student)
GET    /api/v1/classes/{id}/                 # Get class details
PATCH  /api/v1/classes/{id}/                 # Update class settings
DELETE /api/v1/classes/{id}/                 # Cancel class

POST   /api/v1/classes/{id}/start/           # Teacher starts class
POST   /api/v1/classes/{id}/end/             # Teacher ends class

# Enrollment
POST   /api/v1/classes/{id}/enroll/          # Student enrolls
DELETE /api/v1/classes/{id}/unenroll/        # Student leaves
GET    /api/v1/classes/{id}/participants/    # List participants

# Joining
POST   /api/v1/classes/{id}/join/            # Join class (get RTC + Centrifugo tokens)
POST   /api/v1/classes/{id}/leave/           # Leave class

# Chat
POST   /api/v1/classes/{id}/messages/        # Send message
GET    /api/v1/classes/{id}/messages/        # Get message history
DELETE /api/v1/classes/{id}/messages/{msg_id}/ # Delete message (teacher)

# Hand raising
POST   /api/v1/classes/{id}/hand/raise/      # Raise hand
POST   /api/v1/classes/{id}/hand/lower/      # Lower hand
GET    /api/v1/classes/{id}/hands/           # Get hand queue (teacher)
POST   /api/v1/classes/{id}/hands/{user_id}/acknowledge/ # Acknowledge hand

# Reactions
POST   /api/v1/classes/{id}/reactions/       # Send reaction (emoji)

# Teacher controls
POST   /api/v1/classes/{id}/grant-mic/{user_id}/    # Allow student to unmute
POST   /api/v1/classes/{id}/revoke-mic/{user_id}/   # Mute student
POST   /api/v1/classes/{id}/kick/{user_id}/         # Remove student
POST   /api/v1/classes/{id}/spotlight/{user_id}/    # Pin student video

# Realtime tokens
GET    /api/v1/classes/{id}/realtime-token/  # Get Centrifugo token for class channels
```

### 4. Centrifugo Configuration

```json
{
  "engine": "redis",
  "redis_address": "redis:6379",
  "redis_password": "${REDIS_PASSWORD}",
  "redis_db": 3,
  
  "presence": true,
  "history_size": 300,
  "history_ttl": "1800s",
  
  "namespaces": [
    {
      "name": "class",
      "presence": true,
      "history_size": 300,
      "history_ttl": "1800s",
      "join_leave": true,
      "force_recovery": true
    },
    {
      "name": "user",
      "presence": false,
      "history_size": 50,
      "history_ttl": "300s"
    }
  ],
  
  "allowed_origins": ["*"],
  "log_level": "info"
}
```

## Implementation Flow

### Student Joining a Class

```javascript
// 1. Student calls join API
POST /api/v1/classes/{id}/join/

Response:
{
  "class": {
    "id": "class-uuid",
    "title": "Math 101",
    "teacher": {...},
    "settings": {
      "allow_chat": true,
      "allow_reactions": true
    }
  },
  "rtc": {
    "room_id": "room-uuid",
    "ws_url": "wss://smartinhub.ir/rtc/ws",
    "token": "rtc-jwt-token",
    "ice_servers": [...],
    "permissions": {
      "consume": true,
      "produceAudio": false,  // Muted by default
      "produceVideo": true,
      "produceScreen": false
    }
  },
  "realtime": {
    "ws_url": "wss://smartinhub.ir/realtime/connection/websocket",
    "token": "centrifugo-jwt-token",
    "channels": [
      "class:class-uuid",
      "$user:student-id"
    ]
  }
}

// 2. Student connects to Centrifugo
const centrifuge = new Centrifuge(response.realtime.ws_url, {
  token: response.realtime.token
});

// Subscribe to class channel
const classChannel = centrifuge.newSubscription(`class:${classId}`);

classChannel.on('publication', (ctx) => {
  const { event, data } = ctx.data;
  
  switch(event) {
    case 'chat.message':
      // Display chat message
      addMessageToUI(data);
      break;
      
    case 'reaction.added':
      // Show flying emoji animation
      showReaction(data.emoji, data.user);
      break;
      
    case 'hand.raised':
      // Update hand queue UI
      updateHandQueue(data.user_id, 'raised');
      break;
      
    case 'screen_share.started':
      // Teacher started screen sharing
      showScreenShare(data.producer_id);
      break;
  }
});

classChannel.subscribe();

// Subscribe to personal channel
const personalChannel = centrifuge.newSubscription(`$user:${userId}`);

personalChannel.on('publication', (ctx) => {
  const { event, data } = ctx.data;
  
  switch(event) {
    case 'mic.granted':
      // Teacher allowed you to unmute
      showNotification('You can now unmute your microphone');
      enableMicButton();
      break;
      
    case 'spotlight.enabled':
      // Teacher pinned your video
      showNotification('Your video is now spotlighted');
      break;
      
    case 'kicked':
      // Teacher removed you from class
      showNotification('You have been removed from the class');
      leaveClass();
      break;
  }
});

personalChannel.subscribe();
centrifuge.connect();

// 3. Student connects to Mediasoup for A/V
const rtcClient = new MediasoupClient(response.rtc.ws_url);
await rtcClient.connect(response.rtc.token);
await rtcClient.joinRoom(response.rtc.room_id);

// Consume teacher's audio/video
rtcClient.on('producerAdded', (producer) => {
  rtcClient.consume(producer.producerId).then((consumer) => {
    displayVideo(consumer.track, producer.userId);
  });
});
```

### Teacher Controls

```javascript
// Grant mic permission to student
async function grantMic(studentId) {
  await fetch(`/api/v1/classes/${classId}/grant-mic/${studentId}/`, {
    method: 'POST'
  });
  // Django publishes to student's personal channel:
  // publish_to_user(student_id, "mic.granted", {...})
}

// Acknowledge raised hand
async function acknowledgeHand(studentId) {
  await fetch(`/api/v1/classes/${classId}/hands/${studentId}/acknowledge/`, {
    method: 'POST'
  });
  // Django publishes to class channel:
  // publish_to_class(class_id, "hand.acknowledged", {user_id, acknowledged_at})
}

// Kick student
async function kickStudent(studentId) {
  await fetch(`/api/v1/classes/${classId}/kick/${studentId}/`, {
    method: 'POST'
  });
  // Django publishes to student's personal channel:
  // publish_to_user(student_id, "kicked", {reason, kicked_by})
}
```

### Student Actions

```javascript
// Send chat message
async function sendMessage(message) {
  const response = await fetch(`/api/v1/classes/${classId}/messages/`, {
    method: 'POST',
    body: JSON.stringify({ content: message })
  });
  // Django saves to DB and publishes to class channel:
  // publish_to_class(class_id, "chat.message", {msg_id, sender, content, timestamp})
}

// Raise hand
async function raiseHand() {
  await fetch(`/api/v1/classes/${classId}/hand/raise/`, {
    method: 'POST'
  });
  // Django publishes to class channel AND teacher control channel:
  // publish_to_class(class_id, "hand.raised", {user_id, user_name, timestamp})
  // publish(f"class:{class_id}:control", {"event": "hand.raised", ...})
}

// Send reaction
async function sendReaction(emoji) {
  await fetch(`/api/v1/classes/${classId}/reactions/`, {
    method: 'POST',
    body: JSON.stringify({ emoji })
  });
  // Django publishes immediately (no DB save needed):
  // publish_to_class(class_id, "reaction.added", {user_id, emoji, timestamp})
}
```

## Django Backend Implementation

### Publishing Helpers

```python
# django-project/loop/centrifugo_broadcast.py

def publish_to_class(class_id: str, event: str, data: dict) -> bool:
    """Publish event to class channel - all participants receive it"""
    return publish(f"class:{class_id}", {"event": event, "data": data})

def publish_to_class_control(class_id: str, event: str, data: dict) -> bool:
    """Publish to teacher control channel - only teachers receive it"""
    return publish(f"class:{class_id}:control", {"event": event, "data": data})

# Example usage in views
def grant_mic_permission(request, class_id, student_id):
    # Update enrollment
    enrollment = ClassEnrollment.objects.get(
        class_session_id=class_id,
        student_id=student_id
    )
    enrollment.can_unmute = True
    enrollment.save()
    
    # Update RTC permissions (call mediasoup API or store in DB)
    # ...
    
    # Notify student
    publish_to_user(student_id, "mic.granted", {
        "class_id": class_id,
        "granted_by": request.user.id,
        "timestamp": timezone.now().isoformat()
    })
    
    # Notify teacher control channel
    publish_to_class_control(class_id, "mic.granted", {
        "student_id": student_id,
        "granted_by": request.user.id
    })
    
    return Response({"ok": True})
```

## Performance Considerations

### Scalability
- **Centrifugo**: 100k+ concurrent connections per instance
- **Mediasoup**: 500-1000 participants per worker (use multiple workers)
- **Redis**: Pub/sub handles 100k+ messages/second

### For large classes (>100 students):
1. **Centrifugo**: Add more instances behind load balancer (Redis pub/sub handles coordination)
2. **Mediasoup**: Create multiple rooms, split students into breakout rooms
3. **Chat history**: Limit to last 300 messages (30 minutes at ~10 msg/min)

### Message rates:
- Chat: ~10 messages/minute typical
- Reactions: Up to 100/minute during active moments
- Hand raises: ~5/minute typical
- Presence updates: ~20/minute (joins/leaves)

**Total**: ~135 events/minute = ~2.25/second per class

With 100 concurrent classes: ~225 events/second (well within Redis/Centrifugo capacity)

## Migration from Current System

### Keep:
- ✅ **Mediasoup** for audio/video (no changes)
- ✅ **Django control server** (extend with class models)
- ✅ **PostgreSQL** for persistent data
- ✅ **Redis** for Centrifugo pub/sub

### Replace:
- ❌ **Node-signaling** → **Centrifugo** (for all realtime events)

### Why this works:
1. **Centrifugo** already deployed and working (Phase 0-5 completed)
2. **Same infrastructure** (VPS2, Redis, Nginx)
3. **Same authentication pattern** (JWT from Django)
4. **Proven at scale** (you've already replaced AppSync with Centrifugo)

## Next Steps

1. **Add class models** to Django (OnlineClass, ClassEnrollment, etc.)
2. **Create class management APIs** (create, join, leave)
3. **Implement chat/hand-raise/reaction endpoints** (publish via Centrifugo)
4. **Build web frontend** with Centrifugo client
5. **Test with 10-20 concurrent students**
6. **Scale testing** with 100+ students

## Conclusion

**Use Centrifugo** for your online class platform. Your node-signaling server is too limited for classroom features. Centrifugo provides:

- ✅ Chat with history
- ✅ Hand raising queue
- ✅ Reactions broadcasting
- ✅ Room presence
- ✅ Connection recovery
- ✅ Horizontal scaling
- ✅ Already deployed and working

You've already done the hard work (Phases 0-5 completed). Just extend it for classroom features.
