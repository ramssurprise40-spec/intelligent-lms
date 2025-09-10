"""
Social models for the Intelligent LMS system.
Includes study groups, peer interactions, and social learning features.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class StudyGroup(models.Model):
    """
    Study groups for collaborative learning.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Group properties
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='study_groups')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_private = models.BooleanField(default=False)
    max_members = models.IntegerField(default=10)
    
    # Members
    members = models.ManyToManyField(User, related_name='study_groups', through='StudyGroupMembership')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_study_groups')
    
    # AI matching data
    matching_criteria = models.JSONField(default=dict, blank=True)
    compatibility_scores = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_studygroup'
        
    def __str__(self):
        return f"{self.name} ({self.course.title})"


class StudyGroupMembership(models.Model):
    """
    Through model for study group memberships.
    """
    MEMBER_ROLES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('leader', 'Leader'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=MEMBER_ROLES, default='member')
    
    # Participation metrics
    contribution_score = models.FloatField(default=0.0)
    last_activity = models.DateTimeField(auto_now_add=True)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_studygroup_membership'
        unique_together = ['user', 'study_group']


class PeerConnection(models.Model):
    """
    Track peer connections and relationships.
    """
    CONNECTION_TYPES = [
        ('study_partner', 'Study Partner'),
        ('mentor', 'Mentor'),
        ('mentee', 'Mentee'),
        ('friend', 'Friend'),
        ('classmate', 'Classmate'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outgoing_connections')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incoming_connections')
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPES)
    
    # Connection strength (AI-calculated)
    strength_score = models.FloatField(default=0.0)
    interaction_frequency = models.FloatField(default=0.0)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_mutual = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_peerconnection'
        unique_together = ['from_user', 'to_user', 'connection_type']
        
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.get_connection_type_display()})"


class CollaborationSession(models.Model):
    """
    Track collaborative learning sessions.
    """
    SESSION_TYPES = [
        ('study', 'Study Session'),
        ('project_work', 'Project Work'),
        ('problem_solving', 'Problem Solving'),
        ('peer_review', 'Peer Review'),
        ('discussion', 'Discussion'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    
    # Participants
    participants = models.ManyToManyField(User, related_name='collaboration_sessions')
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_sessions')
    
    # Context  
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='collaboration_sessions')
    related_lesson = models.ForeignKey('courses.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    # related_assessment = models.ForeignKey('assessments.Assessment', on_delete=models.SET_NULL, null=True, blank=True)  # Commented temporarily
    
    # Session details
    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    location = models.CharField(max_length=200, blank=True)  # Virtual room link or physical location
    
    # AI Analysis
    effectiveness_score = models.FloatField(null=True, blank=True)
    collaboration_quality = models.JSONField(default=dict, blank=True)
    learning_outcomes = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_collaborationsession'
        
    def __str__(self):
        return f"{self.title} - {self.scheduled_at.strftime('%Y-%m-%d %H:%M')}"


class PeerReview(models.Model):
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='social_peer_reviews_given'  # Fixed conflict
    )
    reviewee = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='social_peer_reviews_received'
    )
    content = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    criteria = models.JSONField(default=dict)
    feedback = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_peer_reviews'
        unique_together = ['reviewer', 'reviewee']
    
    def __str__(self):
        return f"Review by {self.reviewer} for {self.reviewee}"


class ProjectGroup(models.Model):
    """
    Project groups for collaborative assignments.
    """
    STATUS_CHOICES = [
        ('forming', 'Forming'),
        ('active', 'Active'),
        ('completing', 'Completing'),
        ('completed', 'Completed'),
        ('disbanded', 'Disbanded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Group details
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='project_groups')
    # assignment = models.ForeignKey('assessments.Assessment', on_delete=models.CASCADE, related_name='project_groups')  # Commented out - will fix later
    members = models.ManyToManyField(User, related_name='project_groups', through='ProjectGroupMembership')
    
    # Group properties
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='forming')
    max_members = models.IntegerField(default=5)
    is_self_selected = models.BooleanField(default=True)
    
    # Progress tracking
    progress_percentage = models.FloatField(default=0.0)
    milestones_completed = models.JSONField(default=list, blank=True)
    current_milestone = models.CharField(max_length=200, blank=True)
    
    # AI Insights
    collaboration_effectiveness = models.FloatField(null=True, blank=True)
    risk_factors = models.JSONField(default=list, blank=True)
    success_predictors = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_projectgroup'
        
    def __str__(self):
        return f"{self.name} - {self.course.title}"


class ProjectGroupMembership(models.Model):
    """
    Through model for project group memberships.
    """
    MEMBER_ROLES = [
        ('member', 'Member'),
        ('leader', 'Project Leader'),
        ('coordinator', 'Coordinator'),
        ('specialist', 'Subject Specialist'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project_group = models.ForeignKey(ProjectGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=15, choices=MEMBER_ROLES, default='member')
    
    # Contribution tracking
    contribution_percentage = models.FloatField(default=0.0)
    tasks_assigned = models.IntegerField(default=0)
    tasks_completed = models.IntegerField(default=0)
    peer_rating = models.FloatField(null=True, blank=True)
    
    # Activity metrics
    last_activity = models.DateTimeField(auto_now=True)
    total_contributions = models.IntegerField(default=0)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_projectgroup_membership'
        unique_together = ['user', 'project_group']


class SocialInteraction(models.Model):
    """
    Track all social interactions for analytics and AI insights.
    """
    INTERACTION_TYPES = [
        ('message', 'Direct Message'),
        ('forum_post', 'Forum Post'),
        ('forum_reply', 'Forum Reply'),
        ('chat_message', 'Chat Message'),
        ('peer_review', 'Peer Review'),
        ('collaboration', 'Collaboration'),
        ('study_session', 'Study Session'),
        ('project_work', 'Project Work'),
        ('help_request', 'Help Request'),
        ('help_response', 'Help Response'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Participants
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_interactions_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_interactions_received', null=True, blank=True)
    
    # Interaction details
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    content_summary = models.TextField(blank=True)
    
    # Context
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='social_interactions')
    related_object_type = models.CharField(max_length=50, blank=True)  # ContentType name
    related_object_id = models.UUIDField(null=True, blank=True)
    
    # AI Analysis
    sentiment_score = models.FloatField(null=True, blank=True)
    engagement_level = models.FloatField(null=True, blank=True)
    learning_value = models.FloatField(null=True, blank=True)
    
    # Metadata
    duration_minutes = models.IntegerField(null=True, blank=True)
    participants_count = models.IntegerField(default=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_interaction'
        indexes = [
            models.Index(fields=['from_user', 'interaction_type', '-created_at']),
            models.Index(fields=['course', 'interaction_type', '-created_at']),
        ]
        
    def __str__(self):
        return f"{self.from_user.username} - {self.get_interaction_type_display()}"


class LearningCircle(models.Model):
    """
    Learning circles for peer-to-peer knowledge sharing.
    """
    CIRCLE_TYPES = [
        ('subject_focused', 'Subject Focused'),
        ('skill_building', 'Skill Building'),
        ('exam_prep', 'Exam Preparation'),
        ('career_oriented', 'Career Oriented'),
        ('research', 'Research Group'),
    ]
    
    STATUS_CHOICES = [
        ('forming', 'Forming'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    circle_type = models.CharField(max_length=20, choices=CIRCLE_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='forming')
    
    # Members and leadership
    members = models.ManyToManyField(User, related_name='learning_circles')
    facilitator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='facilitated_circles')
    
    # Circle properties
    max_members = models.IntegerField(default=15)
    is_public = models.BooleanField(default=True)
    meeting_frequency = models.CharField(max_length=50, blank=True)  # e.g., "Weekly", "Bi-weekly"
    
    # Learning goals
    learning_objectives = models.JSONField(default=list)
    success_metrics = models.JSONField(default=dict, blank=True)
    
    # AI Matching
    recommended_participants = models.JSONField(default=list, blank=True)
    compatibility_matrix = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_learningcircle'
        
    def __str__(self):
        return f"{self.name} ({self.get_circle_type_display()})"


class SkillExchange(models.Model):
    """
    Platform for students to offer and request skill sharing.
    """
    EXCHANGE_TYPES = [
        ('offer', 'Skill Offer'),
        ('request', 'Skill Request'),
        ('matched', 'Matched Exchange'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Exchange details
    exchange_type = models.CharField(max_length=15, choices=EXCHANGE_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    
    # Participants
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_exchanges_created')
    participants = models.ManyToManyField(User, related_name='skill_exchanges', blank=True)
    
    # Skills
    skills_offered = models.JSONField(default=list)
    skills_requested = models.JSONField(default=list)
    proficiency_level = models.CharField(max_length=20, blank=True)  # Beginner, Intermediate, Advanced
    
    # Matching
    potential_matches = models.JSONField(default=list, blank=True)
    match_score = models.FloatField(null=True, blank=True)
    
    # Logistics
    preferred_format = models.CharField(max_length=50, blank=True)  # Online, In-person, Hybrid
    time_commitment = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_skillexchange'
        
    def __str__(self):
        return f"{self.title} by {self.creator.username}"


class MentorshipRelationship(models.Model):
    """
    Formal mentorship relationships between users.
    """
    STATUS_CHOICES = [
        ('proposed', 'Proposed'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('terminated', 'Terminated'),
    ]
    
    MENTORSHIP_TYPES = [
        ('academic', 'Academic Mentorship'),
        ('career', 'Career Guidance'),
        ('peer', 'Peer Mentorship'),
        ('technical', 'Technical Skills'),
        ('research', 'Research Guidance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentee_relationships')
    mentee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentor_relationships')
    
    # Relationship details
    mentorship_type = models.CharField(max_length=20, choices=MENTORSHIP_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='proposed')
    
    # Goals and progress
    learning_goals = models.JSONField(default=list)
    progress_milestones = models.JSONField(default=list, blank=True)
    success_metrics = models.JSONField(default=dict, blank=True)
    
    # Meeting schedule
    meeting_frequency = models.CharField(max_length=50, blank=True)
    next_meeting = models.DateTimeField(null=True, blank=True)
    total_meetings = models.IntegerField(default=0)
    
    # AI Insights
    relationship_effectiveness = models.FloatField(null=True, blank=True)
    compatibility_score = models.FloatField(null=True, blank=True)
    progress_assessment = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_mentorshiprelationship'
        unique_together = ['mentor', 'mentee', 'mentorship_type']
        
    def __str__(self):
        return f"{self.mentor.username} mentors {self.mentee.username} ({self.get_mentorship_type_display()})"


class SocialLearningEvent(models.Model):
    """
    Social learning events like workshops, meetups, and collaborative sessions.
    """
    EVENT_TYPES = [
        ('workshop', 'Workshop'),
        ('study_session', 'Study Session'),
        ('networking', 'Networking Event'),
        ('presentation', 'Student Presentation'),
        ('hackathon', 'Hackathon'),
        ('book_club', 'Book Club'),
        ('discussion', 'Discussion Panel'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('open_registration', 'Open for Registration'),
        ('full', 'Full'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    
    # Event details
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    facilitators = models.ManyToManyField(User, related_name='facilitated_events', blank=True)
    participants = models.ManyToManyField(User, related_name='social_events', blank=True)
    
    # Logistics
    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    location = models.CharField(max_length=200, blank=True)
    virtual_link = models.URLField(blank=True)
    max_participants = models.IntegerField(default=50)
    
    # Content and learning
    learning_objectives = models.JSONField(default=list, blank=True)
    required_materials = models.JSONField(default=list, blank=True)
    prerequisites = models.TextField(blank=True)
    
    # Registration
    registration_required = models.BooleanField(default=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    
    # Post-event analysis
    attendance_rate = models.FloatField(null=True, blank=True)
    satisfaction_score = models.FloatField(null=True, blank=True)
    learning_outcomes_achieved = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'social_learningevent'
        
    def __str__(self):
        return f"{self.title} - {self.scheduled_at.strftime('%Y-%m-%d %H:%M')}"
