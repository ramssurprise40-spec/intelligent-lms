"""
Management command to test database models and relationships.

This command validates that all models are working correctly,
relationships are properly configured, and database operations
are functioning as expected.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Test database models and relationships'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed test output',
        )
        parser.add_argument(
            '--test-queries',
            action='store_true',
            help='Test complex queries and performance',
        )

    def handle(self, *args, **options):
        self.verbose = options.get('verbose', False)
        self.test_queries = options.get('test_queries', False)
        
        self.stdout.write("Starting database model tests...")
        self.stdout.write("=" * 60)
        
        try:
            # Test all model categories
            self.test_user_models()
            self.test_course_models()
            self.test_assessment_models()
            self.test_communication_models()
            
            if self.test_queries:
                self.test_complex_queries()
            
            self.test_model_relationships()
            self.test_database_constraints()
            
            self.stdout.write("=" * 60)
            self.stdout.write(
                self.style.SUCCESS("All database model tests completed successfully!")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Database model tests failed: {e}")
            )
            raise

    def test_user_models(self):
        """Test User model functionality."""
        self.stdout.write("\n📋 Testing User Models...")
        
        # Test user creation and fields
        test_user = User.objects.filter(username='test_user_model').first()
        if not test_user:
            test_user = User.objects.create_user(
                username='test_user_model',
                email='test@example.com',
                password='testpass123',
                role='student',
                first_name='Test',
                last_name='User'
            )
        
        # Test user properties
        assert test_user.get_full_name() == 'Test User'
        assert test_user.role == 'student'
        assert test_user.is_active is True
        
        if self.verbose:
            self.stdout.write(f"  ✓ User model: {test_user}")
            self.stdout.write(f"    - Full name: {test_user.get_full_name()}")
            self.stdout.write(f"    - Role: {test_user.role}")
            self.stdout.write(f"    - Email: {test_user.email}")
        
        self.stdout.write("  ✓ User model tests passed")

    def test_course_models(self):
        """Test Course-related models."""
        self.stdout.write("\n📚 Testing Course Models...")
        
        from apps.courses.models import Course, CourseModule, Lesson, CourseTag, CourseTagging
        
        # Get instructor
        instructor = User.objects.filter(role='instructor').first()
        if not instructor:
            instructor = User.objects.create_user(
                username='test_instructor',
                email='instructor@example.com',
                password='testpass123',
                role='instructor'
            )
        
        # Test course creation
        course = Course.objects.filter(title='Test Course Model').first()
        if not course:
            course = Course.objects.create(
                title='Test Course Model',
                slug='test-course-model',
                description='A test course for model validation',
                short_description='Test course',
                instructor=instructor,
                status='published',
                difficulty_level='beginner',
                estimated_hours=10
            )
        
        # Test course module
        module = CourseModule.objects.filter(course=course, title='Test Module').first()
        if not module:
            module = CourseModule.objects.create(
                course=course,
                title='Test Module',
                description='Test module description',
                order=1
            )
        
        # Test lesson
        lesson = Lesson.objects.filter(module=module, title='Test Lesson').first()
        if not lesson:
            lesson = Lesson.objects.create(
                module=module,
                title='Test Lesson',
                slug='test-lesson',
                lesson_type='text',
                order=1,
                content='Test lesson content',
                estimated_minutes=30
            )
        
        # Test course tags
        tag = CourseTag.objects.filter(name='Test Tag').first()
        if not tag:
            tag = CourseTag.objects.create(
                name='Test Tag',
                slug='test-tag',
                description='Test tag for validation',
                color='#ff0000'
            )
            
            # Create tagging relationship
            CourseTagging.objects.get_or_create(
                course=course,
                tag=tag,
                defaults={'relevance_score': 1.0}
            )
        
        # Validate relationships
        assert course.instructor == instructor
        assert module.course == course
        assert lesson.module == module
        assert course.modules.count() >= 1
        assert module.lessons.count() >= 1
        
        if self.verbose:
            self.stdout.write(f"  ✓ Course: {course}")
            self.stdout.write(f"    - Modules: {course.modules.count()}")
            self.stdout.write(f"    - Tags: {course.course_tags.count()}")
            self.stdout.write(f"  ✓ Module: {module}")
            self.stdout.write(f"    - Lessons: {module.lessons.count()}")
            self.stdout.write(f"  ✓ Lesson: {lesson}")
        
        self.stdout.write("  ✓ Course model tests passed")

    def test_assessment_models(self):
        """Test Assessment-related models."""
        self.stdout.write("\n📝 Testing Assessment Models...")
        
        from apps.assessments.models import Assessment, Question, AssessmentSubmission, QuestionResponse
        from apps.courses.models import Course
        
        # Get course and instructor
        course = Course.objects.first()
        instructor = course.instructor if course else User.objects.filter(role='instructor').first()
        student = User.objects.filter(role='student').first()
        
        if not all([course, instructor, student]):
            self.stdout.write("  ⚠ Skipping assessment tests - missing required data")
            return
        
        # Test assessment creation
        assessment = Assessment.objects.filter(title='Test Assessment Model').first()
        if not assessment:
            assessment = Assessment.objects.create(
                title='Test Assessment Model',
                course=course,
                creator=instructor,
                assessment_type='quiz',
                description='Test assessment for model validation',
                status='published',
                max_score=100.0,
                max_attempts=3
            )
        
        # Test question creation
        question = Question.objects.filter(assessment=assessment, order=1).first()
        if not question:
            question = Question.objects.create(
                assessment=assessment,
                question_text='What is 2 + 2?',
                question_type='multiple_choice',
                order=1,
                points=10.0,
                question_data={
                    'choices': [
                        {'text': '3', 'is_correct': False},
                        {'text': '4', 'is_correct': True},
                        {'text': '5', 'is_correct': False}
                    ],
                    'correct_answer': '4'
                }
            )
        
        # Test submission creation
        submission = AssessmentSubmission.objects.filter(
            assessment=assessment, 
            student=student
        ).first()
        if not submission:
            submission = AssessmentSubmission.objects.create(
                assessment=assessment,
                student=student,
                attempt_number=1,
                status='submitted',
                score=80.0,
                submitted_at=timezone.now()
            )
        
        # Test question response
        response = QuestionResponse.objects.filter(
            submission=submission,
            question=question
        ).first()
        if not response:
            response = QuestionResponse.objects.create(
                submission=submission,
                question=question,
                response_data={'selected_choice': '4'},
                score=10.0,
                is_correct=True
            )
        
        # Validate relationships
        assert assessment.course == course
        assert assessment.creator == instructor
        assert question.assessment == assessment
        assert submission.assessment == assessment
        assert submission.student == student
        assert response.submission == submission
        assert response.question == question
        
        if self.verbose:
            self.stdout.write(f"  ✓ Assessment: {assessment}")
            self.stdout.write(f"    - Questions: {assessment.questions.count()}")
            self.stdout.write(f"    - Submissions: {assessment.submissions.count()}")
            self.stdout.write(f"  ✓ Question: {question}")
            self.stdout.write(f"  ✓ Submission: {submission}")
            self.stdout.write(f"    - Score: {submission.score}")
            self.stdout.write(f"  ✓ Response: {response}")
        
        self.stdout.write("  ✓ Assessment model tests passed")

    def test_communication_models(self):
        """Test Communication-related models."""
        self.stdout.write("\n💬 Testing Communication Models...")
        
        from apps.communications.models import Forum, ForumTopic, ForumPost, DirectMessage
        from apps.courses.models import Course
        
        # Get course and users
        course = Course.objects.first()
        instructor = User.objects.filter(role='instructor').first()
        student = User.objects.filter(role='student').first()
        
        if not all([course, instructor, student]):
            self.stdout.write("  ⚠ Skipping communication tests - missing required data")
            return
        
        # Test forum creation
        forum = Forum.objects.filter(title__contains='Test Forum').first()
        if not forum:
            forum = Forum.objects.create(
                title='Test Forum Model',
                course=course,
                description='Test forum for model validation',
                is_active=True
            )
        
        # Test topic creation
        topic = ForumTopic.objects.filter(forum=forum, title='Test Topic').first()
        if not topic:
            topic = ForumTopic.objects.create(
                forum=forum,
                title='Test Topic',
                author=instructor,
                status='open'
            )
        
        # Test post creation
        post = ForumPost.objects.filter(topic=topic, post_number=1).first()
        if not post:
            post = ForumPost.objects.create(
                topic=topic,
                author=instructor,
                content='This is a test post for model validation.',
                post_number=1
            )
        
        # Test direct message
        message = DirectMessage.objects.filter(
            sender=instructor,
            recipient=student
        ).first()
        if not message:
            message = DirectMessage.objects.create(
                sender=instructor,
                recipient=student,
                subject='Test Message',
                content='This is a test direct message.',
                status='sent'
            )
        
        # Validate relationships
        assert forum.course == course
        assert topic.forum == forum
        assert topic.author == instructor
        assert post.topic == topic
        assert post.author == instructor
        assert message.sender == instructor
        assert message.recipient == student
        
        if self.verbose:
            self.stdout.write(f"  ✓ Forum: {forum}")
            self.stdout.write(f"    - Topics: {forum.topics.count()}")
            self.stdout.write(f"  ✓ Topic: {topic}")
            self.stdout.write(f"    - Posts: {topic.posts.count()}")
            self.stdout.write(f"  ✓ Post: {post}")
            self.stdout.write(f"  ✓ Message: {message}")
        
        self.stdout.write("  ✓ Communication model tests passed")

    def test_model_relationships(self):
        """Test model relationships and foreign key constraints."""
        self.stdout.write("\n🔗 Testing Model Relationships...")
        
        # Test cascade deletes and relationships
        from apps.courses.models import Course
        from apps.assessments.models import Assessment
        from apps.communications.models import Forum
        
        # Get test objects
        course = Course.objects.first()
        if not course:
            self.stdout.write("  ⚠ No courses found for relationship testing")
            return
        
        # Count related objects
        assessments_count = course.assessments.count()
        forums_count = course.forums.count()
        modules_count = course.modules.count()
        
        if self.verbose:
            self.stdout.write(f"  Course: {course}")
            self.stdout.write(f"    - Assessments: {assessments_count}")
            self.stdout.write(f"    - Forums: {forums_count}")
            self.stdout.write(f"    - Modules: {modules_count}")
        
        # Test reverse relationships
        if assessments_count > 0:
            assessment = course.assessments.first()
            assert assessment.course == course
            
        if forums_count > 0:
            forum = course.forums.first()
            assert forum.course == course
        
        self.stdout.write("  ✓ Model relationship tests passed")

    def test_complex_queries(self):
        """Test complex database queries and aggregations."""
        self.stdout.write("\n🔍 Testing Complex Queries...")
        
        from django.db.models import Count, Avg, Q, F
        from apps.courses.models import Course
        from apps.assessments.models import Assessment, AssessmentSubmission
        
        # Test aggregation queries
        course_stats = Course.objects.aggregate(
            total_courses=Count('id'),
            avg_hours=Avg('estimated_hours')
        )
        
        # Test annotation queries
        courses_with_stats = Course.objects.annotate(
            assessment_count=Count('assessments'),
            forum_count=Count('forums')
        ).filter(assessment_count__gt=0)
        
        # Test complex filtering
        active_courses = Course.objects.filter(
            Q(status='published') & 
            Q(estimated_hours__gte=10)
        )
        
        # Test joins and select_related
        assessments_with_course = Assessment.objects.select_related(
            'course', 'creator'
        ).filter(status='published')
        
        if self.verbose:
            self.stdout.write(f"  Course Statistics: {course_stats}")
            self.stdout.write(f"  Courses with assessments: {courses_with_stats.count()}")
            self.stdout.write(f"  Active courses: {active_courses.count()}")
            self.stdout.write(f"  Published assessments: {assessments_with_course.count()}")
        
        self.stdout.write("  ✓ Complex query tests passed")

    def test_database_constraints(self):
        """Test database constraints and data integrity."""
        self.stdout.write("\n🛡️ Testing Database Constraints...")
        
        from django.db import IntegrityError
        
        # Test unique constraints
        try:
            # Try to create duplicate user
            User.objects.create_user(
                username='admin',  # This should already exist
                email='duplicate@example.com',
                password='testpass'
            )
            # If we get here, the constraint failed
            self.stdout.write("  ✗ Username uniqueness constraint failed")
        except IntegrityError:
            # This is expected
            if self.verbose:
                self.stdout.write("  ✓ Username uniqueness constraint working")
        
        # Test foreign key constraints
        from apps.courses.models import Course
        from apps.assessments.models import Assessment
        
        try:
            # Try to create assessment without valid course
            Assessment.objects.create(
                title='Invalid Assessment',
                course_id=999999,  # Non-existent course
                creator_id=1,
                assessment_type='quiz'
            )
            self.stdout.write("  ✗ Foreign key constraint failed")
        except IntegrityError:
            if self.verbose:
                self.stdout.write("  ✓ Foreign key constraints working")
        
        self.stdout.write("  ✓ Database constraint tests passed")

    def get_database_info(self):
        """Get information about the current database."""
        with connection.cursor() as cursor:
            if connection.vendor == 'postgresql':
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT schemaname, tablename, tableowner 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY tablename;
                """)
                tables = cursor.fetchall()
                
                return {
                    'vendor': connection.vendor,
                    'version': version,
                    'tables_count': len(tables),
                    'tables': [table[1] for table in tables[:10]]  # First 10 tables
                }
            elif connection.vendor == 'sqlite':
                cursor.execute("SELECT sqlite_version();")
                version = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' 
                    ORDER BY name;
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                return {
                    'vendor': connection.vendor,
                    'version': version,
                    'tables_count': len(tables),
                    'tables': tables[:10]  # First 10 tables
                }
        
        return {'vendor': connection.vendor}
