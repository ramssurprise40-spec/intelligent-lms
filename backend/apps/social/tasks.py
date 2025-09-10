"""
Celery tasks for social features, collaboration, and community analytics.
"""

from celery import shared_task
from django.conf import settings
import logging
import requests
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='apps.social.tasks.generate_study_group_recommendations')
def generate_study_group_recommendations(self, user_id, course_id):
    """
    Generate study group recommendations for a user based on learning patterns.
    
    Args:
        user_id (int): ID of the user
        course_id (int): ID of the course
    
    Returns:
        dict: Study group recommendations
    """
    try:
        logger.info(f"Generating study group recommendations for user {user_id} in course {course_id}")
        
        # Get user's learning profile and course data
        try:
            user_profile_response = requests.get(
                f"http://localhost:8000/api/users/{user_id}/profile/",
                timeout=30
            )
            user_profile_response.raise_for_status()
            user_profile = user_profile_response.json()
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            user_profile = {"learning_style": "mixed", "skill_level": "intermediate"}
        
        # Call AI service for intelligent matching
        ai_service_url = "http://localhost:8001/recommend-study-groups"
        
        payload = {
            "user_id": user_id,
            "course_id": course_id,
            "user_profile": user_profile,
            "matching_criteria": [
                "learning_style_compatibility",
                "skill_level_balance",
                "schedule_overlap",
                "learning_goals_alignment"
            ]
        }
        
        try:
            response = requests.post(ai_service_url, json=payload, timeout=45)
            response.raise_for_status()
            recommendations = response.json()
        except Exception as e:
            logger.error(f"Failed to generate AI recommendations: {e}")
            # Fallback recommendations
            recommendations = {
                "suggested_groups": [
                    {
                        "group_id": 1,
                        "group_name": "Python Study Circle",
                        "members_count": 4,
                        "compatibility_score": 0.85,
                        "matching_factors": ["similar learning pace", "complementary strengths"],
                        "meeting_schedule": "Tuesdays 7PM"
                    },
                    {
                        "group_id": 2,
                        "group_name": "Advanced Algorithms Group",
                        "members_count": 3,
                        "compatibility_score": 0.78,
                        "matching_factors": ["similar skill level", "shared learning goals"],
                        "meeting_schedule": "Saturdays 2PM"
                    }
                ],
                "create_new_group_suggestion": {
                    "suggested_name": "Data Structures Learning Group",
                    "recommended_size": 4,
                    "potential_members": [101, 102, 103]
                }
            }
        
        logger.info(f"Generated {len(recommendations['suggested_groups'])} study group recommendations for user {user_id}")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'course_id': course_id,
            'recommendations': recommendations,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Study group recommendation failed for user {user_id}: {exc}")
        self.retry(countdown=60, max_retries=3, exc=exc)

@shared_task(bind=True, name='apps.social.tasks.analyze_collaboration_patterns')
def analyze_collaboration_patterns(self, group_id, analysis_period_days=30):
    """
    Analyze collaboration patterns within a study group.
    
    Args:
        group_id (int): ID of the study group
        analysis_period_days (int): Number of days to analyze
    
    Returns:
        dict: Collaboration analysis results
    """
    try:
        logger.info(f"Analyzing collaboration patterns for group {group_id}")
        
        # Get group activity data
        try:
            activity_response = requests.get(
                f"http://localhost:8000/api/social/groups/{group_id}/activity/",
                params={"days": analysis_period_days},
                timeout=30
            )
            activity_response.raise_for_status()
            activity_data = activity_response.json()
        except Exception as e:
            logger.error(f"Failed to get group activity: {e}")
            activity_data = {"interactions": [], "sessions": [], "shared_resources": []}
        
        # Call AI service for collaboration analysis
        ai_service_url = "http://localhost:8001/analyze-collaboration"
        
        payload = {
            "group_id": group_id,
            "activity_data": activity_data,
            "analysis_metrics": [
                "participation_balance",
                "knowledge_sharing",
                "peer_support",
                "group_dynamics",
                "learning_outcomes"
            ]
        }
        
        try:
            response = requests.post(ai_service_url, json=payload, timeout=60)
            response.raise_for_status()
            analysis = response.json()
        except Exception as e:
            logger.error(f"Failed to analyze collaboration: {e}")
            # Fallback analysis
            analysis = {
                "collaboration_score": 0.75,
                "participation_metrics": {
                    "most_active_member": {"user_id": 101, "participation_rate": 0.9},
                    "least_active_member": {"user_id": 103, "participation_rate": 0.4},
                    "average_participation": 0.68
                },
                "knowledge_sharing": {
                    "resources_shared": 15,
                    "questions_answered": 28,
                    "peer_explanations": 12
                },
                "group_dynamics": {
                    "communication_style": "collaborative",
                    "conflict_incidents": 0,
                    "support_instances": 22
                },
                "recommendations": [
                    "Encourage quieter members to participate more",
                    "Schedule regular check-ins",
                    "Create structured study sessions"
                ]
            }
        
        logger.info(f"Collaboration analysis completed for group {group_id}: score {analysis['collaboration_score']}")
        
        return {
            'status': 'success',
            'group_id': group_id,
            'analysis_period_days': analysis_period_days,
            'analysis': analysis,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Collaboration analysis failed for group {group_id}: {exc}")
        self.retry(countdown=60, max_retries=2, exc=exc)

@shared_task(bind=True, name='apps.social.tasks.generate_peer_feedback')
def generate_peer_feedback(self, submission_id, reviewer_ids, review_criteria):
    """
    Coordinate peer review process and generate aggregate feedback.
    
    Args:
        submission_id (int): ID of the submission to review
        reviewer_ids (list): List of peer reviewer IDs
        review_criteria (dict): Review criteria and rubric
    
    Returns:
        dict: Peer feedback results
    """
    try:
        logger.info(f"Generating peer feedback for submission {submission_id} with {len(reviewer_ids)} reviewers")
        
        peer_reviews = []
        
        # Collect reviews from each peer
        for reviewer_id in reviewer_ids:
            try:
                # In a real implementation, you'd get the actual peer review
                # Here we simulate the peer review process
                
                review_data = {
                    "reviewer_id": reviewer_id,
                    "submission_id": submission_id,
                    "scores": {
                        "content_quality": 8.5,
                        "organization": 7.8,
                        "creativity": 8.2,
                        "technical_accuracy": 8.0
                    },
                    "written_feedback": f"Good work overall. Reviewer {reviewer_id} feedback...",
                    "suggestions": [
                        "Strengthen the conclusion",
                        "Add more supporting examples"
                    ],
                    "review_timestamp": datetime.now().isoformat()
                }
                
                peer_reviews.append(review_data)
                
            except Exception as e:
                logger.error(f"Failed to get review from peer {reviewer_id}: {e}")
        
        # Generate aggregate feedback using AI
        ai_service_url = "http://localhost:8001/aggregate-peer-feedback"
        
        payload = {
            "submission_id": submission_id,
            "peer_reviews": peer_reviews,
            "review_criteria": review_criteria,
            "aggregation_method": "weighted_consensus"
        }
        
        try:
            response = requests.post(ai_service_url, json=payload, timeout=45)
            response.raise_for_status()
            aggregate_feedback = response.json()
        except Exception as e:
            logger.error(f"Failed to generate aggregate feedback: {e}")
            # Fallback aggregation
            avg_scores = {}
            for criterion in review_criteria.get("criteria", []):
                scores = [review["scores"].get(criterion, 0) for review in peer_reviews]
                avg_scores[criterion] = sum(scores) / len(scores) if scores else 0
            
            aggregate_feedback = {
                "overall_score": sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0,
                "criterion_scores": avg_scores,
                "consensus_feedback": "Aggregate feedback based on peer reviews",
                "common_suggestions": ["Review common themes", "Address peer concerns"],
                "feedback_reliability": 0.8,
                "reviewer_agreement_score": 0.75
            }
        
        logger.info(f"Peer feedback generated for submission {submission_id}: overall score {aggregate_feedback['overall_score']}")
        
        return {
            'status': 'success',
            'submission_id': submission_id,
            'peer_reviews_count': len(peer_reviews),
            'aggregate_feedback': aggregate_feedback,
            'individual_reviews': peer_reviews,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Peer feedback generation failed for submission {submission_id}: {exc}")
        self.retry(countdown=60, max_retries=2, exc=exc)

@shared_task(bind=True, name='apps.social.tasks.moderate_forum_content')
def moderate_forum_content(self, post_id, content, author_id, forum_id):
    """
    Moderate forum content for inappropriate material and community guidelines.
    
    Args:
        post_id (int): ID of the forum post
        content (str): Post content to moderate
        author_id (int): ID of the post author
        forum_id (int): ID of the forum
    
    Returns:
        dict: Moderation results
    """
    try:
        logger.info(f"Moderating forum post {post_id} in forum {forum_id}")
        
        # Call AI service for content moderation
        ai_service_url = "http://localhost:8003/moderate-content"
        
        payload = {
            "content": content,
            "content_type": "forum_post",
            "author_id": author_id,
            "moderation_rules": [
                "inappropriate_language",
                "harassment",
                "spam",
                "academic_dishonesty",
                "off_topic",
                "personal_information"
            ]
        }
        
        try:
            response = requests.post(ai_service_url, json=payload, timeout=30)
            response.raise_for_status()
            moderation_result = response.json()
        except Exception as e:
            logger.error(f"Failed to moderate content: {e}")
            # Fallback moderation
            moderation_result = {
                "is_approved": True,
                "confidence_score": 0.9,
                "flags": [],
                "content_category": "educational_discussion",
                "action_required": None,
                "suggested_edits": []
            }
        
        # Take action based on moderation results
        action_taken = None
        if not moderation_result["is_approved"]:
            if moderation_result.get("flags"):
                if "harassment" in moderation_result["flags"]:
                    action_taken = "content_hidden_pending_review"
                    logger.warning(f"Post {post_id} flagged for harassment and hidden")
                elif "spam" in moderation_result["flags"]:
                    action_taken = "content_marked_as_spam"
                    logger.warning(f"Post {post_id} marked as spam")
                else:
                    action_taken = "content_flagged_for_review"
                    logger.info(f"Post {post_id} flagged for manual review")
        
        # Notify administrators if serious violations detected
        if action_taken and any(flag in ["harassment", "academic_dishonesty"] for flag in moderation_result.get("flags", [])):
            # Send notification to moderators
            logger.warning(f"Serious violation detected in post {post_id}, notifying administrators")
        
        logger.info(f"Content moderation completed for post {post_id}: {'approved' if moderation_result['is_approved'] else 'flagged'}")
        
        return {
            'status': 'success',
            'post_id': post_id,
            'forum_id': forum_id,
            'moderation_result': moderation_result,
            'action_taken': action_taken,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Content moderation failed for post {post_id}: {exc}")
        self.retry(countdown=30, max_retries=2, exc=exc)

@shared_task(bind=True, name='apps.social.tasks.generate_community_insights')
def generate_community_insights(self, course_id, insight_type='engagement'):
    """
    Generate insights about community engagement and learning dynamics.
    
    Args:
        course_id (int): ID of the course community to analyze
        insight_type (str): Type of insights to generate
    
    Returns:
        dict: Community insights
    """
    try:
        logger.info(f"Generating {insight_type} insights for course community {course_id}")
        
        # Gather community data
        try:
            community_response = requests.get(
                f"http://localhost:8000/api/courses/{course_id}/community-stats/",
                timeout=30
            )
            community_response.raise_for_status()
            community_data = community_response.json()
        except Exception as e:
            logger.error(f"Failed to get community data: {e}")
            community_data = {
                "total_members": 50,
                "active_members": 35,
                "forum_posts": 120,
                "study_groups": 8
            }
        
        # Call AI service for insight generation
        ai_service_url = "http://localhost:8001/generate-community-insights"
        
        payload = {
            "course_id": course_id,
            "community_data": community_data,
            "insight_type": insight_type,
            "time_period": "last_30_days"
        }
        
        try:
            response = requests.post(ai_service_url, json=payload, timeout=45)
            response.raise_for_status()
            insights = response.json()
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            # Fallback insights
            insights = {
                "engagement_metrics": {
                    "participation_rate": 0.7,
                    "average_interactions_per_user": 8.5,
                    "content_sharing_frequency": 2.3,
                    "peer_help_instances": 45
                },
                "learning_dynamics": {
                    "collaborative_learning_score": 0.78,
                    "knowledge_sharing_index": 0.82,
                    "peer_support_level": "high",
                    "community_cohesion": 0.75
                },
                "trends": [
                    "Increasing participation in study groups",
                    "High-quality peer discussions",
                    "Active knowledge sharing"
                ],
                "recommendations": [
                    "Encourage more peer reviews",
                    "Create topic-specific discussion threads",
                    "Recognize active community contributors"
                ]
            }
        
        logger.info(f"Community insights generated for course {course_id}: participation rate {insights['engagement_metrics']['participation_rate']}")
        
        return {
            'status': 'success',
            'course_id': course_id,
            'insight_type': insight_type,
            'insights': insights,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Community insights generation failed for course {course_id}: {exc}")
        self.retry(countdown=60, max_retries=2, exc=exc)

@shared_task(bind=True, name='apps.social.tasks.update_user_reputation')
def update_user_reputation(self, user_id, activity_type, activity_data):
    """
    Update user reputation based on community contributions.
    
    Args:
        user_id (int): ID of the user
        activity_type (str): Type of activity (helpful_answer, quality_post, etc.)
        activity_data (dict): Details about the activity
    
    Returns:
        dict: Reputation update results
    """
    try:
        logger.info(f"Updating reputation for user {user_id} based on {activity_type}")
        
        # Define reputation scoring rules
        reputation_rules = {
            "helpful_answer": {"base_points": 10, "multiplier_factors": ["upvotes", "acceptance"]},
            "quality_post": {"base_points": 5, "multiplier_factors": ["engagement", "clarity"]},
            "peer_review": {"base_points": 8, "multiplier_factors": ["thoroughness", "constructiveness"]},
            "resource_sharing": {"base_points": 6, "multiplier_factors": ["usefulness", "originality"]},
            "mentoring_activity": {"base_points": 15, "multiplier_factors": ["impact", "consistency"]},
            "negative_behavior": {"base_points": -20, "multiplier_factors": ["severity", "frequency"]}
        }
        
        # Calculate reputation change
        base_points = reputation_rules.get(activity_type, {}).get("base_points", 0)
        multiplier = 1.0
        
        # Apply multipliers based on activity quality
        for factor in reputation_rules.get(activity_type, {}).get("multiplier_factors", []):
            factor_value = activity_data.get(factor, 1.0)
            if isinstance(factor_value, (int, float)):
                multiplier *= max(0.1, min(2.0, factor_value))  # Clamp multiplier
        
        reputation_change = int(base_points * multiplier)
        
        # Get current reputation
        try:
            reputation_response = requests.get(
                f"http://localhost:8000/api/users/{user_id}/reputation/",
                timeout=30
            )
            reputation_response.raise_for_status()
            current_reputation = reputation_response.json().get("reputation", 0)
        except Exception as e:
            logger.error(f"Failed to get current reputation: {e}")
            current_reputation = 100  # Default starting reputation
        
        # Calculate new reputation
        new_reputation = max(0, current_reputation + reputation_change)
        
        # Update user reputation in database
        try:
            update_response = requests.patch(
                f"http://localhost:8000/api/users/{user_id}/reputation/",
                json={"reputation": new_reputation, "activity": activity_type},
                timeout=30
            )
            update_response.raise_for_status()
            update_successful = True
        except Exception as e:
            logger.error(f"Failed to update reputation: {e}")
            update_successful = False
        
        # Check for reputation milestones and badges
        milestones_achieved = []
        reputation_thresholds = [100, 250, 500, 1000, 2500, 5000]
        
        for threshold in reputation_thresholds:
            if current_reputation < threshold <= new_reputation:
                milestones_achieved.append({
                    "milestone": threshold,
                    "badge": f"Reputation {threshold}",
                    "description": f"Achieved {threshold} reputation points"
                })
        
        logger.info(f"Reputation updated for user {user_id}: {current_reputation} -> {new_reputation} ({reputation_change:+d})")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'activity_type': activity_type,
            'reputation_change': reputation_change,
            'current_reputation': current_reputation,
            'new_reputation': new_reputation,
            'milestones_achieved': milestones_achieved,
            'update_successful': update_successful,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Reputation update failed for user {user_id}: {exc}")
        self.retry(countdown=30, max_retries=2, exc=exc)
