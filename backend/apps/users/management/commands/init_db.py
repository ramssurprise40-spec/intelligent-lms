"""
Django management command for database initialization.
This command sets up initial data, creates admin users, and populates sample content.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize database with sample data and admin users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-users',
            action='store_true',
            help='Skip creating admin users',
        )
        parser.add_argument(
            '--skip-courses',
            action='store_true',
            help='Skip creating sample courses',
        )
        parser.add_argument(
            '--skip-assessments',
            action='store_true',
            help='Skip creating sample assessments',
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting database initialization...")
        self.stdout.write("=" * 50)
        
        try:
            with transaction.atomic():
                if not options['skip_users']:
                    self.create_admin_users()
                
                if not options['skip_courses']:
                    self.create_sample_courses()
                
                if not options['skip_assessments']:
                    self.create_sample_assessments()
                
                self.create_sample_communications()
                
                self.stdout.write("=" * 50)
                self.stdout.write(
                    self.style.SUCCESS("Database initialization completed successfully!")
                )
                self.stdout.write(
                    self.style.WARNING("Default credentials:")
                )
                self.stdout.write("Admin user: admin / admin123")
                self.stdout.write("Instructor user: instructor_demo / instructor123")
                self.stdout.write("Student user: student_demo / student123")
                self.stdout.write(
                    self.style.WARNING("Remember to change default passwords in production!")
                )
                
        except Exception as e:
            raise CommandError(f'Database initialization failed: {e}')

    def create_admin_users(self):
        """Create initial admin users."""
        self.stdout.write("Creating admin users...")
        
        # Main system administrator
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@intelligent-lms.local',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'is_verified': True,
            }
        )
        if created:
            admin_user.set_password('admin123')  # Change this in production
            admin_user.save()
            self.stdout.write(f"  Created admin user: {admin_user.username}")
        else:
            self.stdout.write(f"  Admin user already exists: {admin_user.username}")
        
        # Sample instructor
        instructor_user, created = User.objects.get_or_create(
            username='instructor_demo',
            defaults={
                'email': 'instructor@intelligent-lms.local',
                'first_name': 'Demo',
                'last_name': 'Instructor',
                'role': 'instructor',
                'is_staff': False,
                'is_active': True,
                'is_verified': True,
                'bio': 'Experienced instructor with expertise in computer science and AI.',
            }
        )
        if created:
            instructor_user.set_password('instructor123')
            instructor_user.save()
            self.stdout.write(f"  Created instructor user: {instructor_user.username}")
        else:
            self.stdout.write(f"  Instructor user already exists: {instructor_user.username}")
        
        # Sample student
        student_user, created = User.objects.get_or_create(
            username='student_demo',
            defaults={
                'email': 'student@intelligent-lms.local',
                'first_name': 'Demo',
                'last_name': 'Student',
                'role': 'student',
                'is_active': True,
                'is_verified': True,
                'student_id': 'STU001',
                'bio': 'Enthusiastic learner passionate about technology.',
            }
        )
        if created:
            student_user.set_password('student123')
            student_user.save()
            self.stdout.write(f"  Created student user: {student_user.username}")
        else:
            self.stdout.write(f"  Student user already exists: {student_user.username}")

    def create_sample_courses(self):
        """Create sample courses with modules and lessons."""
        self.stdout.write("Creating sample courses...")
        
        from apps.courses.models import Course, CourseModule, Lesson, CourseTag, CourseTagging
        
        # Get instructor for courses
        instructor = User.objects.filter(role='instructor').first()
        if not instructor:
            self.stdout.write("  No instructor found. Creating default instructor...")
            instructor = User.objects.create_user(
                username='default_instructor',
                email='default@intelligent-lms.local',
                first_name='Default',
                last_name='Instructor',
                role='instructor',
                is_active=True,
                is_verified=True
            )
        
        # Create course tags
        tags_data = [
            {'name': 'Programming', 'description': 'Programming and software development', 'color': '#007bff'},
            {'name': 'AI/ML', 'description': 'Artificial Intelligence and Machine Learning', 'color': '#28a745'},
            {'name': 'Web Development', 'description': 'Web development and frontend/backend technologies', 'color': '#ffc107'},
            {'name': 'Data Science', 'description': 'Data analysis, statistics, and data visualization', 'color': '#dc3545'},
            {'name': 'Beginner Friendly', 'description': 'Suitable for beginners with no prior experience', 'color': '#17a2b8'},
            {'name': 'Hands-on', 'description': 'Practical, project-based learning approach', 'color': '#6c757d'},
            {'name': 'Interactive', 'description': 'Interactive lessons and exercises', 'color': '#6f42c1'},
        ]
        
        for tag_data in tags_data:
            CourseTag.objects.get_or_create(
                name=tag_data['name'],
                defaults={
                    'slug': tag_data['name'].lower().replace('/', '-').replace(' ', '-'),
                    'description': tag_data['description'],
                    'color': tag_data['color']
                }
            )
        
        # Sample Course 1: Introduction to Python Programming
        python_course, created = Course.objects.get_or_create(
            title='Introduction to Python Programming',
            defaults={
                'slug': 'introduction-to-python-programming',
                'description': 'Learn Python programming from basics to advanced concepts. Perfect for beginners and those looking to strengthen their programming foundation.',
                'short_description': 'Learn Python from scratch with hands-on projects.',
                'instructor': instructor,
                'difficulty_level': 'beginner',
                'status': 'published',
                'estimated_hours': 40,
                'learning_objectives': [
                    'Understand Python syntax and basic programming concepts',
                    'Work with data types, variables, and control structures',
                    'Create and use functions effectively',
                    'Handle errors and exceptions',
                    'Work with files and data'
                ],
            }
        )
        
        if created:
            self.stdout.write(f"  Created course: {python_course.title}")
            
            # Add tags to course
            python_tags = CourseTag.objects.filter(name__in=['Programming', 'Beginner Friendly', 'Hands-on'])
            for tag in python_tags:
                CourseTagging.objects.get_or_create(
                    course=python_course,
                    tag=tag,
                    defaults={'relevance_score': 1.0}
                )
            
            # Create modules for Python course
            modules_data = [
                {
                    'title': 'Getting Started with Python',
                    'description': 'Introduction to Python, installation, and basic concepts',
                    'order': 1,
                    'lessons': [
                        {'title': 'What is Python?', 'lesson_type': 'video', 'duration_minutes': 15},
                        {'title': 'Installing Python and IDE Setup', 'lesson_type': 'text', 'duration_minutes': 20},
                        {'title': 'Your First Python Program', 'lesson_type': 'interactive', 'duration_minutes': 25},
                        {'title': 'Python Syntax Basics', 'lesson_type': 'video', 'duration_minutes': 30},
                    ]
                },
                {
                    'title': 'Variables and Data Types',
                    'description': 'Learn about Python data types and variables',
                    'order': 2,
                    'lessons': [
                        {'title': 'Numbers and Strings', 'lesson_type': 'video', 'duration_minutes': 25},
                        {'title': 'Lists and Dictionaries', 'lesson_type': 'text', 'duration_minutes': 35},
                        {'title': 'Working with Data - Practice', 'lesson_type': 'assignment', 'duration_minutes': 45},
                    ]
                }
            ]
            
            for module_data in modules_data:
                lessons_data = module_data.pop('lessons')
                module = CourseModule.objects.create(
                    course=python_course,
                    **module_data
                )
                
                # Create lessons for the module
                for i, lesson_data in enumerate(lessons_data, 1):
                    Lesson.objects.create(
                        module=module,
                        slug=lesson_data['title'].lower().replace(' ', '-').replace('?', '').replace('/', '-'),
                        order=i,
                        estimated_minutes=lesson_data.pop('duration_minutes', 30),
                        content=f"This is the content for {lesson_data['title']}. In a real implementation, this would contain the actual lesson content.",
                        **lesson_data
                    )
            
            self.stdout.write(f"  Created {len(modules_data)} modules with lessons for {python_course.title}")

    def create_sample_assessments(self):
        """Create sample assessments and questions."""
        self.stdout.write("Creating sample assessments...")
        
        from apps.assessments.models import Assessment, Question
        from apps.courses.models import Course
        
        # Get a course to attach assessments to
        course = Course.objects.filter(title='Introduction to Python Programming').first()
        if not course:
            self.stdout.write("  No course found for assessments")
            return
        
        # Get instructor for assessment creator
        instructor = User.objects.filter(role='instructor').first()
        if not instructor:
            instructor = User.objects.filter(is_staff=True).first()
        
        # Create a quiz assessment
        quiz, created = Assessment.objects.get_or_create(
            title='Python Basics Quiz',
            defaults={
                'course': course,
                'creator': instructor,
                'assessment_type': 'quiz',
                'description': 'Test your understanding of Python basics',
                'status': 'published',
                'max_score': 100.0,
                'passing_score': 70.0,
                'time_limit_minutes': 30,
                'max_attempts': 3,
                'instructions': 'Answer all questions to the best of your ability. You have 30 minutes to complete this quiz.',
            }
        )
        
        if created:
            self.stdout.write(f"  Created assessment: {quiz.title}")
            
            # Create sample questions
            questions_data = [
                {
                    'question_text': 'What is the correct way to create a variable in Python?',
                    'question_type': 'multiple_choice',
                    'points': 10.0,
                    'question_data': {
                        'choices': [
                            {'text': 'var x = 5', 'is_correct': False},
                            {'text': 'x = 5', 'is_correct': True},
                            {'text': 'int x = 5', 'is_correct': False},
                            {'text': 'declare x = 5', 'is_correct': False}
                        ],
                        'correct_answer': 'x = 5',
                        'explanation': 'In Python, variables are created by simply assigning a value to a name.'
                    }
                },
                {
                    'question_text': 'Which data type is used to store text in Python?',
                    'question_type': 'multiple_choice',
                    'points': 10.0,
                    'question_data': {
                        'choices': [
                            {'text': 'int', 'is_correct': False},
                            {'text': 'float', 'is_correct': False},
                            {'text': 'str', 'is_correct': True},
                            {'text': 'bool', 'is_correct': False}
                        ],
                        'correct_answer': 'str',
                        'explanation': 'The str (string) data type is used to store text in Python.'
                    }
                }
            ]
            
            for i, q_data in enumerate(questions_data, 1):
                Question.objects.create(
                    assessment=quiz,
                    order=i,
                    **q_data
                )
            
            self.stdout.write(f"  Created {len(questions_data)} questions for {quiz.title}")

    def create_sample_communications(self):
        """Create sample forum posts and communication data."""
        self.stdout.write("Creating sample communications...")
        
        from apps.communications.models import Forum, ForumTopic, ForumPost
        from apps.courses.models import Course
        
        # Get users and course
        instructor = User.objects.filter(role='instructor').first()
        student = User.objects.filter(role='student').first()
        course = Course.objects.first()
        
        if not all([instructor, student, course]):
            self.stdout.write("  Missing required data for communications")
            return
        
        # Create course forum
        forum, created = Forum.objects.get_or_create(
            title=f'{course.title} - Discussion',
            course=course,
            defaults={
                'description': f'Discussion forum for {course.title}',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(f"  Created forum: {forum.title}")
            
            # Create a topic
            topic = ForumTopic.objects.create(
                forum=forum,
                title='Welcome to Python Programming!',
                author=instructor,
                is_sticky=True
            )
            
            # Create posts
            post1 = ForumPost.objects.create(
                topic=topic,
                author=instructor,
                content='Welcome to the Python Programming course! Please introduce yourself and let us know what you hope to learn.',
                post_number=1
            )
            
            post2 = ForumPost.objects.create(
                topic=topic,
                author=student,
                content='Hi everyone! I\'m excited to learn Python. I hope to use it for data analysis in my field.',
                post_number=2
            )
            
            # Update topic statistics
            topic.post_count = 2
            topic.last_post_by = student
            topic.save()
            
            self.stdout.write(f"  Created topic and posts in {forum.title}")
