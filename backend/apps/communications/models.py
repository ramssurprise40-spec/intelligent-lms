"""
Communication models for the Intelligent LMS system.
Includes messaging, forums, announcements, and notifications.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Forum(models.Model):
    """
    Course forums for discussions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='forums')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Forum settings
    is_active = models.BooleanField(default=True)
    is_moderated = models.BooleanField(default=True)
    allow_anonymous_posts = models.BooleanField(default=False)
    
    # Moderators
    moderators = models.ManyToManyField(User, related_name='moderated_forums', blank=True)
    
    # Statistics
    total_posts = models.IntegerField(default=0)
    total_topics = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'communications_forum'
        ordering = ['course', 'title']
        
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class ForumTopic(models.Model):
    """
    Individual topics/threads within forums.
    """
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('pinned', 'Pinned'),
        ('locked', 'Locked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_topics')
    
    # Topic properties
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    is_announcement = models.BooleanField(default=False)
    is_sticky = models.BooleanField(default=False)
    
    # Statistics
    view_count = models.IntegerField(default=0)
    post_count = models.IntegerField(default=1)  # Includes initial post
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_post_at = models.DateTimeField(auto_now_add=True)
    last_post_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='last_forum_posts')
    
    class Meta:
        db_table = 'communications_topic'
        indexes = [
            models.Index(fields=['forum', 'status', '-last_post_at']),
            models.Index(fields=['is_sticky', '-last_post_at']),
        ]
        ordering = ['-is_sticky', '-last_post_at']
        
    def __str__(self):
        return self.title


class ForumPost(models.Model):
    """
    Individual posts within forum topics.
    """
    STATUS_CHOICES = [
        ('published', 'Published'),
        ('draft', 'Draft'),
        ('moderated', 'Under Moderation'),
        ('hidden', 'Hidden'),
        ('deleted', 'Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    
    # Post content
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    
    # Post metadata
    is_solution = models.BooleanField(default=False)  # For Q&A style topics
    post_number = models.PositiveIntegerField()  # Order within topic
    
    # Engagement
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    
    # AI Analysis
    sentiment_score = models.FloatField(null=True, blank=True)
    toxicity_score = models.FloatField(null=True, blank=True)
    key_topics = models.JSONField(default=list, blank=True)
    
    # Moderation
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_posts')
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderation_reason = models.CharField(max_length=200, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'communications_post'
        unique_together = ['topic', 'post_number']
        indexes = [
            models.Index(fields=['topic', 'post_number']),
            models.Index(fields=['author', '-created_at']),
        ]
        ordering = ['topic', 'post_number']
        
    def __str__(self):
        return f"{self.topic.title} - Post #{self.post_number}"


class PostVote(models.Model):
    """
    Track user votes on forum posts.
    """
    VOTE_CHOICES = [
        ('up', 'Upvote'),
        ('down', 'Downvote'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_votes')
    vote_type = models.CharField(max_length=4, choices=VOTE_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'communications_vote'
        unique_together = ['post', 'user']
        
    def __str__(self):
        return f"{self.user.username} {self.get_vote_type_display()} on {self.post}"


class DirectMessage(models.Model):
    """
    Direct messages between users.
    """
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    
    # Message content
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    
    # Message properties
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    priority = models.CharField(
        max_length=10,
        choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High')],
        default='normal'
    )
    
    # Threading
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    thread_id = models.UUIDField(null=True, blank=True)  # For message threading
    
    # Timestamps
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Flags
    sender_archived = models.BooleanField(default=False)
    recipient_archived = models.BooleanField(default=False)
    sender_deleted = models.BooleanField(default=False)
    recipient_deleted = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'communications_message'
        indexes = [
            models.Index(fields=['sender', '-sent_at']),
            models.Index(fields=['recipient', '-sent_at']),
            models.Index(fields=['thread_id', 'sent_at']),
        ]
        ordering = ['-sent_at']
        
    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.subject or self.content[:50]}"
    
    def mark_as_read(self):
        """Mark message as read."""
        if self.status != 'read':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save()


class Announcement(models.Model):
    """
    Course or system-wide announcements.
    """
    ANNOUNCEMENT_TYPES = [
        ('course', 'Course Announcement'),
        ('system', 'System Announcement'),
        ('maintenance', 'Maintenance Notice'),
        ('emergency', 'Emergency Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Announcement properties
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    
    # Targeting
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True, related_name='announcements')
    target_users = models.ManyToManyField(User, blank=True, related_name='targeted_announcements')
    target_roles = models.JSONField(default=list, blank=True)  # Target specific user roles
    
    # Publishing
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_announcements')
    is_published = models.BooleanField(default=False)
    publish_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery settings
    send_email = models.BooleanField(default=True)
    send_push = models.BooleanField(default=True)
    pin_to_top = models.BooleanField(default=False)
    
    # Analytics
    view_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'communications_announcement'
        indexes = [
            models.Index(fields=['course', 'is_published', '-publish_at']),
            models.Index(fields=['announcement_type', 'priority']),
        ]
        ordering = ['-pin_to_top', '-publish_at']
        
    def __str__(self):
        return self.title
    
    @property
    def is_active(self):
        """Check if announcement is currently active."""
        now = timezone.now()
        if self.publish_at and now < self.publish_at:
            return False
        if self.expires_at and now > self.expires_at:
            return False
        return self.is_published


class AnnouncementView(models.Model):
    """
    Track user views of announcements.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcement_views')
    
    viewed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'communications_announcement_view'
        unique_together = ['announcement', 'user']
        
    def __str__(self):
        return f"{self.user.username} viewed {self.announcement.title}"


class ChatRoom(models.Model):
    """
    Real-time chat rooms for courses or groups.
    """
    ROOM_TYPES = [
        ('course', 'Course Chat'),
        ('study_group', 'Study Group'),
        ('office_hours', 'Office Hours'),
        ('project', 'Project Discussion'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    
    # Associations
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_rooms')
    
    # Members
    members = models.ManyToManyField(User, related_name='chat_rooms', through='ChatRoomMembership')
    moderators = models.ManyToManyField(User, related_name='moderated_chat_rooms', blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_private = models.BooleanField(default=False)
    max_members = models.IntegerField(null=True, blank=True)
    
    # AI Features
    auto_moderate = models.BooleanField(default=True)
    sentiment_tracking = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'communications_chatroom'
        
    def __str__(self):
        return self.name


class ChatRoomMembership(models.Model):
    """
    Through model for chat room memberships.
    """
    MEMBER_ROLES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Administrator'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=MEMBER_ROLES, default='member')
    
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'communications_chatroom_membership'
        unique_together = ['user', 'chat_room']


class ChatMessage(models.Model):
    """
    Individual messages within chat rooms.
    """
    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System Message'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    
    # Message content
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    
    # Thread/Reply support
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # AI Analysis
    sentiment_score = models.FloatField(null=True, blank=True)
    toxicity_score = models.FloatField(null=True, blank=True)
    
    # Status
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    sent_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'communications_chat_message'
        indexes = [
            models.Index(fields=['chat_room', '-sent_at']),
            models.Index(fields=['sender', '-sent_at']),
        ]
        ordering = ['sent_at']
        
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}..."
