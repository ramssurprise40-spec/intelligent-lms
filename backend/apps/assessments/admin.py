"""
Django admin configuration for assessment models.
"""

from django.contrib import admin
from django.utils import timezone

from .models import (
    Assessment, Question, AssessmentSubmission, QuestionResponse,
    GradingRubric, PeerReview, AssessmentAnalytics
)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ['order', 'question_type', 'points', 'difficulty_level']
    ordering = ['order']


class SubmissionInline(admin.TabularInline):
    model = AssessmentSubmission
    extra = 0
    fields = ['student', 'attempt_number', 'status', 'score', 'submitted_at', 'graded_at']
    readonly_fields = ['submitted_at', 'graded_at']


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'assessment_type', 'status', 'due_date', 'max_score', 'created_at']
    list_filter = ['assessment_type', 'status', 'course', 'created_at', 'due_date']
    search_fields = ['title', 'description', 'course__title']
    inlines = [QuestionInline, SubmissionInline]
    readonly_fields = ['created_at', 'updated_at', 'published_at']
    
    actions = ['publish_assessments']

    def publish_assessments(self, request, queryset):
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f"{updated} assessments published.")
    publish_assessments.short_description = 'Publish selected assessments'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'order', 'question_type', 'points', 'difficulty_level']
    list_filter = ['question_type', 'difficulty_level', 'assessment__course']
    search_fields = ['question_text', 'assessment__title']
    ordering = ['assessment', 'order']


class QuestionResponseInline(admin.TabularInline):
    model = QuestionResponse
    extra = 0
    fields = ['question', 'score', 'manual_score', 'is_correct']


@admin.register(AssessmentSubmission)
class AssessmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'student', 'attempt_number', 'status', 'score', 'submitted_at', 'graded_at']
    list_filter = ['status', 'assessment__course', 'assessment__assessment_type']
    search_fields = ['assessment__title', 'student__username']
    readonly_fields = ['started_at', 'submitted_at', 'graded_at']
    inlines = [QuestionResponseInline]


@admin.register(GradingRubric)
class GradingRubricAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'title', 'total_points', 'ai_assisted', 'updated_at']
    list_filter = ['ai_assisted']
    search_fields = ['assessment__title', 'title']


@admin.register(PeerReview)
class PeerReviewAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'reviewer', 'reviewed_submission', 'status', 'score', 'due_date', 'completed_at']
    list_filter = ['status', 'assessment__course']
    search_fields = ['assessment__title', 'reviewer__username']


@admin.register(AssessmentAnalytics)
class AssessmentAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'total_submissions', 'average_score', 'pass_rate', 'last_calculated']
    search_fields = ['assessment__title']
