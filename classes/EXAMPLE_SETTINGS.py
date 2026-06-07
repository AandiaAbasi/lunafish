# Classes app settings for fofofish

INSTALLED_APPS = [
    # ...
    'rest_framework',
    'classes',
]

# fofofish uses account.User.role:
# - teacher => teacher
# - user => student/customer
CLASSES_USER_ROLE_FIELD = 'role'
CLASSES_TEACHER_ROLE_VALUE = 'teacher'
CLASSES_STUDENT_ROLE_VALUE = 'user'

CLASSES_MAX_STUDENTS_DEFAULT = 100
CLASSES_MAX_STUDENTS_HARD_LIMIT = 500
CLASSES_MESSAGE_HISTORY_LIMIT = 300
CLASSES_REACTION_RATE_LIMIT = 10

CENTRIFUGO_TOKEN_SECRET = 'change-me'
CENTRIFUGO_API_KEY = 'change-me'
CENTRIFUGO_API_URL = 'http://centrifugo:8000/api'
CENTRIFUGO_WS_URL = 'wss://example.com/realtime/connection/websocket'

RTC_JWT_SECRET = 'change-me'
RTC_WS_URL = 'wss://example.com/rtc/ws'
RTC_TOKEN_TTL_SECONDS = 3600
RTC_ICE_SERVERS = [
    {'urls': ['stun:stun.l.google.com:19302']},
]

# urls.py
# path('api/v1/classes/', include('classes.urls'))
