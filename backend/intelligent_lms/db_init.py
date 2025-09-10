"""
Database initialization script for Intelligent LMS.
This script sets up initial data, creates admin users, and populates sample content.
"""

import os
import django
from django.conf import settings
from django.core.management import call_command
from django.db import transaction
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intelligent_lms.settings')
django.setup()

User = get_user_model()


def create_admin_users():
    """Create initial admin users."""
    print("Creating admin users...")
    
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
        print(f"Created admin user: {admin_user.username}")
    else:
        print(f"Admin user already exists: {admin_user.username}")
    
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
        print(f"Created instructor user: {instructor_user.username}")
    else:
        print(f"Instructor user already exists: {instructor_user.username}")
    
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
        print(f"Created student user: {student_user.username}")
    else:
        print(f"Student user already exists: {student_user.username}")
    
    return admin_user, instructor_user, student_user


def create_sample_courses():
    """Create sample courses with modules and lessons."""
    print("Creating sample courses...")
    
    from apps.courses.models import Course, CourseModule, Lesson, CourseTag
    from apps.users.models import User
    
    # Get instructor for courses
    instructor = User.objects.filter(role='instructor').first()
    if not instructor:
        print("No instructor found. Creating default instructor...")
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
        {'name': 'Programming', 'category': 'technical'},
        {'name': 'AI/ML', 'category': 'technical'},
        {'name': 'Web Development', 'category': 'technical'},
        {'name': 'Data Science', 'category': 'technical'},
        {'name': 'Beginner Friendly', 'category': 'level'},
        {'name': 'Hands-on', 'category': 'format'},
        {'name': 'Interactive', 'category': 'format'},
    ]
    
    for tag_data in tags_data:
        CourseTag.objects.get_or_create(**tag_data)
    
    # Sample Course 1: Introduction to Python Programming
    python_course, created = Course.objects.get_or_create(
        title='Introduction to Python Programming',
        defaults={
            'description': 'Learn Python programming from basics to advanced concepts. Perfect for beginners and those looking to strengthen their programming foundation.',
            'instructor': instructor,
            'category': 'programming',
            'difficulty_level': 'beginner',
            'estimated_duration_hours': 40,
            'price': 0.00,  # Free course
            'is_published': True,
            'is_active': True,
            'learning_objectives': [
                'Understand Python syntax and basic programming concepts',
                'Work with data types, variables, and control structures',
                'Create and use functions effectively',
                'Handle errors and exceptions',
                'Work with files and data'
            ],
            'prerequisites': [],
            'target_audience': 'beginners',
        }
    )
    
    if created:
        print(f"Created course: {python_course.title}")
        
        # Add tags to course
        python_tags = CourseTag.objects.filter(name__in=['Programming', 'Beginner Friendly', 'Hands-on'])
        python_course.tags.set(python_tags)
        
        # Create modules for Python course
        modules_data = [
            {
                'title': 'Getting Started with Python',
                'description': 'Introduction to Python, installation, and basic concepts',
                'order_index': 1,
                'lessons': [
                    {'title': 'What is Python?', 'lesson_type': 'video', 'duration_minutes': 15},
                    {'title': 'Installing Python and IDE Setup', 'lesson_type': 'tutorial', 'duration_minutes': 20},
                    {'title': 'Your First Python Program', 'lesson_type': 'interactive', 'duration_minutes': 25},
                    {'title': 'Python Syntax Basics', 'lesson_type': 'video', 'duration_minutes': 30},
                ]
            },
            {
                'title': 'Variables and Data Types',
                'description': 'Learn about Python data types and variables',
                'order_index': 2,
                'lessons': [
                    {'title': 'Numbers and Strings', 'lesson_type': 'video', 'duration_minutes': 25},
                    {'title': 'Lists and Dictionaries', 'lesson_type': 'tutorial', 'duration_minutes': 35},
                    {'title': 'Working with Data - Practice', 'lesson_type': 'exercise', 'duration_minutes': 45},
                ]
            },
            {
                'title': 'Control Structures',
                'description': 'Conditional statements and loops in Python',
                'order_index': 3,
                'lessons': [
                    {'title': 'If Statements and Conditions', 'lesson_type': 'video', 'duration_minutes': 30},
                    {'title': 'For and While Loops', 'lesson_type': 'tutorial', 'duration_minutes': 40},
                    {'title': 'Loop Practice Problems', 'lesson_type': 'exercise', 'duration_minutes': 60},
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
                    order_index=i,
                    content=f"This is the content for {lesson_data['title']}. In a real implementation, this would contain the actual lesson content.",
                    **lesson_data
                )
        
        print(f"Created {len(modules_data)} modules with lessons for {python_course.title}")
    
    # Sample Course 2: Data Science Fundamentals
    ds_course, created = Course.objects.get_or_create(
        title='Data Science Fundamentals',
        defaults={
            'description': 'Introduction to data science concepts, tools, and techniques. Learn to analyze data and extract meaningful insights.',
            'instructor': instructor,
            'category': 'data-science',
            'difficulty_level': 'intermediate',
            'estimated_duration_hours': 60,
            'price': 99.99,
            'is_published': True,
            'is_active': True,
            'learning_objectives': [
                'Understand data science workflow and methodology',
                'Learn to use Python libraries for data analysis',
                'Master data visualization techniques',
                'Apply statistical analysis to real datasets',
                'Build basic machine learning models'
            ],
            'prerequisites': ['Basic Python programming', 'High school mathematics'],
            'target_audience': 'aspiring data scientists',
        }
    )
    
    if created:
        print(f"Created course: {ds_course.title}")
        ds_tags = CourseTag.objects.filter(name__in=['Data Science', 'AI/ML', 'Interactive'])
        ds_course.tags.set(ds_tags)
        
        # Create a sample module
        ds_module = CourseModule.objects.create(
            course=ds_course,
            title='Introduction to Data Science',
            description='Overview of data science field and tools',
            order_index=1
        )
        
        Lesson.objects.create(
            module=ds_module,
            title='What is Data Science?',
            lesson_type='video',
            duration_minutes=20,
            order_index=1,
            content='Introduction to the field of data science and its applications.'
        )


def create_sample_assessments():
    """Create sample assessments and questions."""
    print("Creating sample assessments...")
    
    from apps.assessments.models import Assessment, Question, GradingRubric
    from apps.courses.models import Course
    
    # Get a course to attach assessments to
    course = Course.objects.filter(title='Introduction to Python Programming').first()
    if not course:
        print("No course found for assessments")
        return
    
    # Create a quiz assessment
    quiz, created = Assessment.objects.get_or_create(
        title='Python Basics Quiz',
        defaults={
            'course': course,
            'assessment_type': 'quiz',
            'description': 'Test your understanding of Python basics',
            'max_score': 100,
            'passing_score': 70,
            'time_limit_minutes': 30,
            'max_attempts': 3,
            'is_active': True,
            'instructions': 'Answer all questions to the best of your ability. You have 30 minutes to complete this quiz.',
        }
    )
    
    if created:
        print(f"Created assessment: {quiz.title}")
        
        # Create sample questions
        questions_data = [
            {
                'question_text': 'What is the correct way to create a variable in Python?',
                'question_type': 'multiple_choice',
                'points': 10,
                'options': {
                    'choices': [
                        {'text': 'var x = 5', 'is_correct': False},
                        {'text': 'x = 5', 'is_correct': True},
                        {'text': 'int x = 5', 'is_correct': False},
                        {'text': 'declare x = 5', 'is_correct': False}
                    ]
                },
                'correct_answer': 'x = 5',
                'explanation': 'In Python, variables are created by simply assigning a value to a name.'
            },
            {
                'question_text': 'Which data type is used to store text in Python?',
                'question_type': 'multiple_choice',
                'points': 10,
                'options': {
                    'choices': [
                        {'text': 'int', 'is_correct': False},
                        {'text': 'float', 'is_correct': False},
                        {'text': 'str', 'is_correct': True},
                        {'text': 'bool', 'is_correct': False}
                    ]
                },
                'correct_answer': 'str',
                'explanation': 'The str (string) data type is used to store text in Python.'
            },
            {
                'question_text': 'Explain the difference between a list and a tuple in Python.',
                'question_type': 'text',
                'points': 20,
                'options': {},
                'correct_answer': 'Lists are mutable (can be changed) while tuples are immutable (cannot be changed). Lists use square brackets [] while tuples use parentheses ().',
                'explanation': 'This is an open-ended question to test understanding of data structures.'
            }
        ]
        
        for i, q_data in enumerate(questions_data, 1):
            Question.objects.create(
                assessment=quiz,
                order_index=i,
                **q_data
            )
        
        print(f"Created {len(questions_data)} questions for {quiz.title}")


def create_sample_communications():
    """Create sample forum posts and communication data."""
    print("Creating sample communications...")
    
    from apps.communications.models import Forum, Topic, Post
    from apps.users.models import User
    from apps.courses.models import Course
    
    # Get users and course
    instructor = User.objects.filter(role='instructor').first()
    student = User.objects.filter(role='student').first()
    course = Course.objects.first()
    
    if not all([instructor, student, course]):
        print("Missing required data for communications")
        return
    
    # Create course forum
    forum, created = Forum.objects.get_or_create(
        name=f'{course.title} - Discussion',
        defaults={
            'description': f'Discussion forum for {course.title}',
            'course': course,
            'is_active': True,
        }
    )
    
    if created:
        print(f"Created forum: {forum.name}")
        
        # Create a topic
        topic = Topic.objects.create(
            forum=forum,
            title='Welcome to Python Programming!',
            description='Introduce yourself and share your learning goals',
            created_by=instructor,
            is_pinned=True
        )
        
        # Create posts
        Post.objects.create(
            topic=topic,
            author=instructor,
            content='Welcome to the Python Programming course! Please introduce yourself and let us know what you hope to learn.',
            is_first_post=True
        )
        
        Post.objects.create(
            topic=topic,
            author=student,
            content='Hi everyone! I\'m excited to learn Python. I hope to use it for data analysis in my field.',
            is_first_post=False
        )
        
        print(f"Created topic and posts in {forum.name}")


def setup_database_extensions():
    """Set up PostgreSQL extensions if using PostgreSQL."""
    from django.db import connection
    
    if 'postgresql' in connection.vendor:
        print("Setting up PostgreSQL extensions...")
        
        try:
            with connection.cursor() as cursor:
                # Enable pgvector extension for embeddings
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # Enable full-text search extensions
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
                
                print("PostgreSQL extensions configured successfully")
        except Exception as e:
            print(f"Error setting up PostgreSQL extensions: {e}")
    else:
        print("Using SQLite - skipping extension setup")


def initialize_database():
    """Main initialization function."""
    print("Starting database initialization...")
    print("=" * 50)
    
    try:
        with transaction.atomic():
            # Set up database extensions
            setup_database_extensions()
            
            # Create users
            admin_user, instructor_user, student_user = create_admin_users()
            
            # Create sample courses
            create_sample_courses()
            
            # Create sample assessments
            create_sample_assessments()
            
            # Create sample communications
            create_sample_communications()
            
            print("=" * 50)
            print("Database initialization completed successfully!")
            print(f"Admin user: admin / admin123")
            print(f"Instructor user: instructor_demo / instructor123")
            print(f"Student user: student_demo / student123")
            print("Remember to change default passwords in production!")
            
    except Exception as e:
        print(f"Error during database initialization: {e}")
        raise


if __name__ == '__main__':
    initialize_database()
