"""
Agora SDK Integration Service & Quiz Logic Service
"""
import time
import hashlib
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from .models import (
    StudentQuizAttempt, StudentQuestionResponse, Quiz, QuizQuestion
)


class QuizService:
    """Quiz management and scoring service"""
    
    @staticmethod
    def calculate_attempt_score(attempt: StudentQuizAttempt) -> dict:
        """
        Calculate score for a quiz attempt
        
        Args:
            attempt: StudentQuizAttempt instance
        
        Returns:
            Dictionary with score details
        """
        responses = attempt.responses.all()
        total_points = 0
        earned_points = 0
        correct_count = 0
        wrong_count = 0
        
        for response in responses:
            question_points = response.question.points
            total_points += question_points
            
            if response.is_correct:
                earned_points += question_points
                correct_count += 1
            else:
                wrong_count += 1
        
        # Calculate percentage
        if total_points > 0:
            score = int((earned_points / total_points) * 100)
        else:
            score = 0
        
        return {
            'score': score,
            'total_points': total_points,
            'earned_points': earned_points,
            'correct_count': correct_count,
            'wrong_count': wrong_count,
            'passed': score >= attempt.quiz.passing_score
        }
    
    @staticmethod
    def submit_attempt(attempt: StudentQuizAttempt, method: str = 'manual') -> StudentQuizAttempt:
        """
        Submit a quiz attempt and calculate final score
        
        Args:
            attempt: StudentQuizAttempt instance
            method: 'manual' or 'automatic'
        
        Returns:
            Updated StudentQuizAttempt instance
        """
        if attempt.is_submitted:
            raise ValueError("This attempt has already been submitted")
        
        # Calculate score
        score_data = QuizService.calculate_attempt_score(attempt)
        
        # Update attempt
        attempt.submitted_at = timezone.now()
        attempt.is_submitted = True
        attempt.submission_status = 'submitted'
        attempt.submission_method = method
        attempt.score = score_data['score']
        attempt.total_points = score_data['total_points']
        attempt.earned_points = score_data['earned_points']
        attempt.passed = score_data['passed']
        
        # Calculate time taken
        if attempt.started_at and attempt.submitted_at:
            time_delta = attempt.submitted_at - attempt.started_at
            attempt.time_taken_minutes = Decimal(time_delta.total_seconds()) / Decimal(60)
        
        attempt.save()
        return attempt
    
    @staticmethod
    def can_attempt_quiz(quiz: Quiz, student, attempts_made: int = 0) -> tuple:
        """
        Check if student can attempt the quiz
        
        Args:
            quiz: Quiz instance
            student: User instance
            attempts_made: Number of previous attempts
        
        Returns:
            Tuple of (can_attempt: bool, reason: str)
        """
        if not quiz.is_active:
            return False, "Quiz is not active"
        
        if attempts_made >= quiz.max_attempts:
            return False, f"Maximum {quiz.max_attempts} attempts reached"
        
        return True, "OK"
    
    @staticmethod
    def auto_submit_on_timeout(attempt: StudentQuizAttempt) -> StudentQuizAttempt:
        """
        Auto-submit attempt when time expires
        
        Args:
            attempt: StudentQuizAttempt instance
        
        Returns:
            Updated StudentQuizAttempt instance
        """
        if attempt.quiz.time_limit_minutes:
            elapsed = (timezone.now() - attempt.started_at).total_seconds() / 60
            
            if elapsed >= attempt.quiz.time_limit_minutes:
                attempt.submission_status = 'timeout'
                return QuizService.submit_attempt(attempt, method='automatic')
        
        return attempt
    
    @staticmethod
    def get_response_summary(attempt: StudentQuizAttempt) -> dict:
        """
        Get detailed summary of attempt responses
        
        Args:
            attempt: StudentQuizAttempt instance
        
        Returns:
            Dictionary with response summary
        """
        responses = attempt.responses.all()
        
        summary = {
            'attempt_id': attempt.id,
            'quiz_title': attempt.quiz.title,
            'student': attempt.student.username,
            'score': attempt.score,
            'passed': attempt.passed,
            'questions': []
        }
        
        for response in responses:
            summary['questions'].append({
                'question_id': response.question.id,
                'question_text': response.question.question_text,
                'question_type': response.question.question_type,
                'selected_answer': response.selected_answer.answer_text if response.selected_answer else None,
                'text_response': response.text_response,
                'is_correct': response.is_correct,
                'points_earned': response.points_earned,
                'explanation': response.question.explanation,
                'response_time_seconds': response.response_time_seconds
            })
        
        return summary


class AgoraService:
    """Agora API wrapper for token generation and channel management"""
    
    def __init__(self):
        self.app_id = settings.AGORA_APP_ID
        self.app_certificate = settings.AGORA_APP_CERTIFICATE
    
    def generate_token(self, channel: str, uid: int, privilege: str = 'publisher', ttl: int = 3600):
        """
        Generate Agora RTC token
        
        Args:
            channel: Channel name
            uid: User ID
            privilege: 'publisher' or 'subscriber'
            ttl: Token time-to-live in seconds (default 1 hour)
        
        Returns:
            Access token string
        """
        try:
            from agora_token_builder import RtcTokenBuilder
            
            token = RtcTokenBuilder.build_token_with_uid(
                self.app_id,
                self.app_certificate,
                channel,
                uid,
                self._get_role(privilege),
                int(time.time()) + ttl
            )
            
            return token
        except ImportError:
            # Fallback: return a placeholder token if agora_token_builder is not installed
            import hashlib
            token_data = f"{self.app_id}{channel}{uid}{int(time.time())}"
            return hashlib.sha256(token_data.encode()).hexdigest()
    
    def _get_role(self, privilege: str):
        """Convert privilege string to Agora role"""
        try:
            from agora_token_builder import Role
            
            if privilege == 'publisher':
                return Role.ROLE_PUBLISHER
            return Role.ROLE_SUBSCRIBER
        except ImportError:
            # Fallback roles if library not available
            return 1 if privilege == 'publisher' else 2
    
    def revoke_token(self, token: str):
        """Revoke a token (blacklist it)"""
        # This would typically involve storing revoked tokens in cache/db
        pass
