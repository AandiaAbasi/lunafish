from django.dispatch import Signal


class_created = Signal()
class_started = Signal()
class_ended = Signal()
class_cancelled = Signal()

student_enrolled = Signal()
student_unenrolled = Signal()
student_joined = Signal()
student_left = Signal()

hand_raised = Signal()
hand_lowered = Signal()
hand_acknowledged = Signal()
message_sent = Signal()
message_deleted = Signal()
reaction_sent = Signal()

mic_granted = Signal()
mic_revoked = Signal()
student_kicked = Signal()
student_spotlighted = Signal()
