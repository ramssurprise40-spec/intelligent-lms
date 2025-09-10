"""
API views for analytics and insights.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Avg, Count, Sum, Max, Min
from datetime import datetime, timedelta
import json
import logging

from .models import (
    LearningAnalytics, CourseAnalytics, PerformanceReport,
    PredictiveModel, StudentProgress, LearningPath
)
from .serializers import (
    LearningAnalyticsSerializer, CourseAnalyticsSerializer,
    PerformanceReportSerializer, DashboardDataSerializer
)
from .services import AnalyticsService, PredictiveAnalyticsService

logger = logging.getLogger(__name__)


class LearningAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for learning analytics data.
    """
    serializer_class = LearningAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return LearningAnalytics.objects.all()
        return LearningAnalytics.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_analytics(self, request):
        """
        Get current user's learning analytics.
        """
        analytics, created = LearningAnalytics.objects.get_or_create(
            user=request.user
        )
        
        # Update analytics if stale
        if analytics.last_updated < timezone.now() - timedelta(hours=6):
            analytics_service = AnalyticsService()
            analytics_service.update_user_analytics(request.user.id)
            analytics.refresh_from_db()
        
        serializer = self.get_serializer(analytics)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def learning_trends(self, request):
        """
        Get learning trends and patterns.
        """
        days = int(request.query_params.get('days', 30))
        
        analytics_service = AnalyticsService()
        trends_data = analytics_service.get_learning_trends(
            user_id=request.user.id,
            days=days
        )
        
        return Response({
            'user_id': request.user.id,
            'period_days': days,
            'trends': trends_data,
            'generated_at': timezone.now().isoformat()
        })
    
    @action(detail=False, methods=['post'])
    def generate_insights(self, request):
        """
        Generate AI-powered learning insights.
        """
        try:
            predictive_service = PredictiveAnalyticsService()
            insights = predictive_service.generate_learning_insights(request.user.id)
            
            return Response({
                'user_id': request.user.id,
                'insights': insights,
                'generated_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error generating insights for user {request.user.id}: {e}")
            return Response(
                {'error': 'Unable to generate insights at this time'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CourseAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for course analytics data.
    """
    serializer_class = CourseAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return CourseAnalytics.objects.all()
        # Students can only see analytics for courses they're enrolled in
        return CourseAnalytics.objects.filter(
            course__enrollments__user=self.request.user
        )
    
    @action(detail=True, methods=['get'])
    def engagement_metrics(self, request, pk=None):
        """
        Get detailed engagement metrics for a course.
        """
        course_analytics = self.get_object()
        
        analytics_service = AnalyticsService()
        engagement_data = analytics_service.get_course_engagement_metrics(
            course_id=course_analytics.course.id
        )
        
        return Response({
            'course_id': str(course_analytics.course.id),
            'engagement_metrics': engagement_data,
            'generated_at': timezone.now().isoformat()
        })
    
    @action(detail=True, methods=['get'])
    def learning_outcomes(self, request, pk=None):
        """
        Get learning outcomes analysis for a course.
        """
        course_analytics = self.get_object()
        
        analytics_service = AnalyticsService()
        outcomes_data = analytics_service.analyze_learning_outcomes(
            course_id=course_analytics.course.id
        )
        
        return Response({
            'course_id': str(course_analytics.course.id),
            'learning_outcomes': outcomes_data,
            'analyzed_at': timezone.now().isoformat()
        })


class PerformanceReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for performance reports.
    """
    serializer_class = PerformanceReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return PerformanceReport.objects.all()
        return PerformanceReport.objects.filter(
            Q(user=self.request.user) | Q(course__enrollments__user=self.request.user)
        ).distinct()
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """
        Generate a new performance report.
        """
        try:
            report_type = request.data.get('report_type', 'individual')
            period = request.data.get('period', 'monthly')
            course_id = request.data.get('course_id')
            
            analytics_service = AnalyticsService()
            report = analytics_service.generate_performance_report(
                user_id=request.user.id,
                report_type=report_type,
                period=period,
                course_id=course_id
            )
            
            serializer = self.get_serializer(report)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return Response(
                {'error': 'Unable to generate report at this time'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@csrf_exempt
@require_http_methods(["GET"])
@login_required
def dashboard_overview(request):
    """
    Get comprehensive dashboard overview data.
    """
    try:
        analytics_service = AnalyticsService()
        
        # Get overview data
        overview_data = analytics_service.get_dashboard_overview(
            user_id=request.user.id
        )
        
        return JsonResponse({
            'status': 'success',
            'data': overview_data,
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Dashboard overview error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def predict_performance(request):
    """
    Generate performance predictions using AI.
    """
    try:
        data = json.loads(request.body)
        course_id = data.get('course_id')
        prediction_type = data.get('prediction_type', 'completion')
        
        predictive_service = PredictiveAnalyticsService()
        predictions = predictive_service.predict_performance(
            user_id=request.user.id,
            course_id=course_id,
            prediction_type=prediction_type
        )
        
        return JsonResponse({
            'status': 'success',
            'predictions': predictions,
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Performance prediction error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@login_required
def learning_path_recommendations(request):
    """
    Get AI-powered learning path recommendations.
    """
    try:
        course_id = request.GET.get('course_id')
        
        predictive_service = PredictiveAnalyticsService()
        recommendations = predictive_service.recommend_learning_paths(
            user_id=request.user.id,
            course_id=course_id
        )
        
        return JsonResponse({
            'status': 'success',
            'recommendations': recommendations,
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Learning path recommendation error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@login_required
def real_time_alerts(request):
    """
    Get real-time learning alerts and notifications.
    """
    try:
        analytics_service = AnalyticsService()
        alerts = analytics_service.get_real_time_alerts(
            user_id=request.user.id
        )
        
        return JsonResponse({
            'status': 'success',
            'alerts': alerts,
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Real-time alerts error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@login_required
def progress_visualization(request):
    """
    Get data for progress visualization charts.
    """
    try:
        chart_type = request.GET.get('chart_type', 'progress')
        time_range = request.GET.get('time_range', '30')
        course_id = request.GET.get('course_id')
        
        analytics_service = AnalyticsService()
        visualization_data = analytics_service.get_visualization_data(
            user_id=request.user.id,
            chart_type=chart_type,
            time_range=int(time_range),
            course_id=course_id
        )
        
        return JsonResponse({
            'status': 'success',
            'visualization_data': visualization_data,
            'chart_type': chart_type,
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Progress visualization error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
