"""
Assessment API serializers for the Intelligent LMS system.

This module provides serializers for assessment management, submission processing,
grading, and analytics.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    Assessment, Question, AssessmentSubmission, QuestionResponse,
    GradingRubric, PeerReview, AssessmentAnalytics
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for assessment contexts."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']
        read_only_fields = ['id', 'username', 'email']


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for assessment questions."""
    
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'question_type', 'order', 'points',
            'difficulty_level', 'question_data', 'auto_generated', 'topics',
            'learning_objectives', 'average_score', 'answer_distribution',
            'discrimination_index', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'average_score', 'answer_distribution', 'discrimination_index',
            'created_at', 'updated_at'
        ]

    def validate_question_data(self, value):
        """Validate question data based on question type."""
        question_type = self.initial_data.get('question_type')
        
        if question_type == 'multiple_choice':
            if 'choices' not in value or 'correct_answer' not in value:
                raise serializers.ValidationError(
                    "Multiple choice questions must have 'choices' and 'correct_answer' fields"
                )
        elif question_type == 'true_false':
            if 'correct_answer' not in value:
                raise serializers.ValidationError(
                    "True/false questions must have 'correct_answer' field"
                )
        
        return value


class QuestionResponseSerializer(serializers.ModelSerializer):
    """Serializer for question responses."""
    question = QuestionSerializer(read_only=True)
    
    class Meta:
        model = QuestionResponse
        fields = [
            'id', 'question', 'response_data', 'response_text', 'score',
            'is_correct', 'ai_score', 'ai_feedback', 'confidence_score',
            'manual_score', 'manual_feedback', 'graded_by', 'answered_at',
            'graded_at'
        ]
        read_only_fields = [
            'id', 'ai_score', 'ai_feedback', 'confidence_score',
            'answered_at', 'graded_at'
        ]


class AssessmentSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for assessment submissions."""
    student = UserSerializer(read_only=True)
    responses = QuestionResponseSerializer(many=True, read_only=True)
    graded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = AssessmentSubmission
        fields = [
            'id', 'attempt_number', 'status', 'started_at', 'submitted_at',
            'graded_at', 'time_spent', 'score', 'percentage', 'grade',
            'plagiarism_score', 'plagiarism_sources', 'ai_feedback',
            'learning_gaps', 'instructor_feedback', 'graded_by',
            'is_late', 'needs_review', 'student', 'responses'
        ]
        read_only_fields = [
            'id', 'started_at', 'submitted_at', 'graded_at', 'time_spent',
            'plagiarism_score', 'plagiarism_sources', 'ai_feedback',
            'learning_gaps', 'student', 'responses'
        ]


class AssessmentListSerializer(serializers.ModelSerializer):
    """Serializer for assessment list view."""
    creator = UserSerializer(read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    question_count = serializers.SerializerMethodField()
    submission_count = serializers.SerializerMethodField()
    user_submission = serializers.SerializerMethodField()
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'description', 'assessment_type', 'status',
            'available_from', 'due_date', 'time_limit_minutes', 'max_score',
            'max_attempts', 'creator', 'course_title', 'question_count',
            'submission_count', 'user_submission', 'created_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'creator', 'course_title', 'question_count',
            'submission_count', 'user_submission', 'created_at', 'published_at'
        ]
    
    def get_question_count(self, obj):
        """Get the number of questions in this assessment."""
        return obj.questions.count()
    
    def get_submission_count(self, obj):
        """Get the number of submissions for this assessment."""
        return obj.submissions.filter(status__in=['submitted', 'graded']).count()
    
    def get_user_submission(self, obj):
        """Get current user's submission status."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            submission = obj.submissions.filter(
                student=request.user
            ).order_by('-attempt_number').first()
            
            if submission:
                return {
                    'id': submission.id,
                    'attempt_number': submission.attempt_number,
                    'status': submission.status,
                    'score': submission.score,
                    'percentage': submission.percentage,
                    'submitted_at': submission.submitted_at
                }
        return None


class AssessmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed assessment view."""
    creator = UserSerializer(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    user_submissions = serializers.SerializerMethodField()
    analytics = serializers.SerializerMethodField()
    can_submit = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    is_past_due = serializers.ReadOnlyField()
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'description', 'assessment_type', 'status',
            'grading_method', 'available_from', 'due_date', 'time_limit_minutes',
            'max_score', 'passing_score', 'weight', 'max_attempts',
            'allow_late_submission', 'late_penalty_percent', 'auto_generate_feedback',
            'plagiarism_check', 'difficulty_analysis', 'instructions', 'resources',
            'rubric', 'creator', 'course_title', 'questions', 'user_submissions',
            'analytics', 'can_submit', 'is_available', 'is_past_due',
            'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'difficulty_analysis', 'creator', 'course_title', 'questions',
            'user_submissions', 'analytics', 'can_submit', 'is_available',
            'is_past_due', 'created_at', 'updated_at', 'published_at'
        ]
    
    def get_user_submissions(self, obj):
        """Get current user's submissions for this assessment."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            submissions = obj.submissions.filter(
                student=request.user
            ).order_by('-attempt_number')[:5]  # Last 5 attempts
            
            return AssessmentSubmissionSerializer(
                submissions, many=True, context=self.context
            ).data
        return []
    
    def get_analytics(self, obj):
        """Get assessment analytics for instructors."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if user is instructor or staff
            if (hasattr(obj.course, 'instructor') and obj.course.instructor == request.user) or request.user.is_staff:
                try:
                    analytics = obj.analytics
                    return AssessmentAnalyticsSerializer(analytics).data
                except AssessmentAnalytics.DoesNotExist:
                    pass
        return None


class AssessmentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating assessments."""
    questions = QuestionSerializer(many=True, required=False)
    
    class Meta:
        model = Assessment
        fields = [
            'title', 'description', 'assessment_type', 'status', 'grading_method',
            'available_from', 'due_date', 'time_limit_minutes', 'max_score',
            'passing_score', 'weight', 'max_attempts', 'allow_late_submission',
            'late_penalty_percent', 'auto_generate_feedback', 'plagiarism_check',
            'instructions', 'resources', 'rubric', 'questions'
        ]
    
    def create(self, validated_data):
        """Create assessment with questions."""
        questions_data = validated_data.pop('questions', [])
        validated_data['creator'] = self.context['request'].user
        
        assessment = Assessment.objects.create(**validated_data)
        
        # Create questions
        for i, question_data in enumerate(questions_data):
            question_data['order'] = i + 1
            Question.objects.create(assessment=assessment, **question_data)
        
        return assessment
    
    def update(self, instance, validated_data):
        """Update assessment and questions."""
        questions_data = validated_data.pop('questions', None)
        
        # Update assessment
        assessment = super().update(instance, validated_data)
        
        if questions_data is not None:
            # Clear existing questions and create new ones
            assessment.questions.all().delete()
            for i, question_data in enumerate(questions_data):
                question_data['order'] = i + 1
                Question.objects.create(assessment=assessment, **question_data)
        
        return assessment


class GradingRubricSerializer(serializers.ModelSerializer):
    """Serializer for grading rubrics."""
    
    class Meta:
        model = GradingRubric
        fields = [
            'id', 'title', 'description', 'criteria', 'total_points',
            'ai_assisted', 'consistency_check', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PeerReviewSerializer(serializers.ModelSerializer):
    """Serializer for peer reviews."""
    reviewer = UserSerializer(read_only=True)
    reviewed_submission = AssessmentSubmissionSerializer(read_only=True)
    
    class Meta:
        model = PeerReview
        fields = [
            'id', 'status', 'score', 'feedback', 'detailed_ratings',
            'review_quality_score', 'reviewer', 'reviewed_submission',
            'assigned_at', 'due_date', 'completed_at'
        ]
        read_only_fields = [
            'id', 'review_quality_score', 'reviewer', 'reviewed_submission',
            'assigned_at', 'completed_at'
        ]


class AssessmentAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for assessment analytics."""
    
    class Meta:
        model = AssessmentAnalytics
        fields = [
            'id', 'total_submissions', 'average_score', 'median_score',
            'pass_rate', 'average_completion_time', 'median_completion_time',
            'question_analytics', 'difficult_questions', 'learning_gaps_identified',
            'improvement_suggestions', 'last_calculated'
        ]
        read_only_fields = ['id', 'last_calculated']


class SubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new submissions."""
    responses = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = AssessmentSubmission
        fields = ['responses']
    
    def create(self, validated_data):
        """Create submission with responses."""
        assessment = self.context['assessment']
        student = self.context['request'].user
        responses_data = validated_data.pop('responses', [])
        
        # Check if student can submit
        if not assessment.can_submit:
            raise serializers.ValidationError("Assessment is not accepting submissions")
        
        # Check attempt limits
        existing_attempts = AssessmentSubmission.objects.filter(
            assessment=assessment,
            student=student
        ).count()
        
        if existing_attempts >= assessment.max_attempts:
            raise serializers.ValidationError("Maximum attempts exceeded")
        
        # Create submission
        submission = AssessmentSubmission.objects.create(
            assessment=assessment,
            student=student,
            attempt_number=existing_attempts + 1
        )
        
        # Create responses
        for response_data in responses_data:
            question_id = response_data.get('question_id')
            try:
                question = assessment.questions.get(id=question_id)
                QuestionResponse.objects.create(
                    submission=submission,
                    question=question,
                    response_data=response_data.get('response_data', {}),
                    response_text=response_data.get('response_text', '')
                )
            except Question.DoesNotExist:
                continue
        
        return submission


class GradeSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for grading submissions."""
    response_grades = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    
    class Meta:
        model = AssessmentSubmission
        fields = ['score', 'grade', 'instructor_feedback', 'response_grades']
    
    def update(self, instance, validated_data):
        """Update submission with grades and feedback."""
        response_grades = validated_data.pop('response_grades', [])
        
        # Update submission
        instance.status = 'graded'
        instance.graded_at = timezone.now()
        instance.graded_by = self.context['request'].user
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update individual response grades
        for grade_data in response_grades:
            response_id = grade_data.get('response_id')
            try:
                response = instance.responses.get(id=response_id)
                response.manual_score = grade_data.get('score')
                response.manual_feedback = grade_data.get('feedback', '')
                response.graded_by = self.context['request'].user
                response.graded_at = timezone.now()
                response.save()
            except QuestionResponse.DoesNotExist:
                continue
        
        # Calculate final score
        final_score = instance.calculate_grade()
        if final_score is not None:
            instance.score = final_score
        
        instance.save()
        return instance


class AssessmentStatsSerializer(serializers.Serializer):
    """Serializer for assessment statistics."""
    total_assessments = serializers.IntegerField()
    published_assessments = serializers.IntegerField()
    draft_assessments = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    pending_grading = serializers.IntegerField()
    average_score = serializers.FloatField()
    recent_submissions = AssessmentSubmissionSerializer(many=True)
