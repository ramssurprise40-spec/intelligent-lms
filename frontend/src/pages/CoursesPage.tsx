import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpenIcon,
  ClockIcon,
  UserGroupIcon,
  AcademicCapIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  CalendarDaysIcon,
  StarIcon,
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { cn } from '../utils/cn';
import { useAuth } from '../contexts/AuthContext';

const courses = [
  {
    id: 1,
    code: 'CS 485',
    title: 'Advanced Machine Learning',
    instructor: 'Dr. Sarah Wilson',
    semester: 'Fall 2024',
    credits: 3,
    progress: 75,
    grade: 'A-',
    status: 'active',
    schedule: 'MWF 10:00-11:00 AM',
    room: 'Engineering Building 201',
    enrollment: { current: 28, max: 35 },
    nextAssignment: 'Neural Networks Project',
    nextAssignmentDue: '2025-09-15',
    description: 'Advanced topics in machine learning including deep learning, neural networks, and AI applications.',
    rating: 4.5,
  },
  {
    id: 2,
    code: 'CS 370',
    title: 'Database Systems Design',
    instructor: 'Prof. Michael Chen',
    semester: 'Fall 2024',
    credits: 4,
    progress: 45,
    grade: 'B+',
    status: 'active',
    schedule: 'TTh 2:00-3:30 PM',
    room: 'Computer Science Building 105',
    enrollment: { current: 32, max: 40 },
    nextAssignment: 'SQL Optimization Lab',
    nextAssignmentDue: '2025-09-12',
    description: 'Comprehensive study of database design, implementation, and optimization techniques.',
    rating: 4.2,
  },
  {
    id: 3,
    code: 'CS 290',
    title: 'Web Development Fundamentals',
    instructor: 'Dr. Emily Rodriguez',
    semester: 'Fall 2024',
    credits: 3,
    progress: 90,
    grade: 'A',
    status: 'nearly-complete',
    schedule: 'MW 1:00-2:30 PM',
    room: 'Technology Center 302',
    enrollment: { current: 45, max: 50 },
    nextAssignment: 'Final Project Presentation',
    nextAssignmentDue: '2025-09-18',
    description: 'Introduction to modern web development technologies including HTML5, CSS3, JavaScript, and frameworks.',
    rating: 4.8,
  },
  {
    id: 4,
    code: 'MATH 320',
    title: 'Statistics for Computer Science',
    instructor: 'Prof. David Kumar',
    semester: 'Fall 2024',
    credits: 3,
    progress: 60,
    grade: 'B',
    status: 'active',
    schedule: 'MWF 9:00-10:00 AM',
    room: 'Mathematics Building 150',
    enrollment: { current: 38, max: 45 },
    nextAssignment: 'Probability Theory Quiz',
    nextAssignmentDue: '2025-09-14',
    description: 'Statistical methods and probability theory with applications in computer science and data analysis.',
    rating: 4.0,
  },
];

const semesters = ['All Semesters', 'Fall 2024', 'Spring 2024', 'Summer 2024'];
const statuses = ['All Statuses', 'Active', 'Completed', 'Dropped'];

export default function CoursesPage() {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSemester, setSelectedSemester] = useState('All Semesters');
  const [selectedStatus, setSelectedStatus] = useState('All Statuses');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const filteredCourses = courses.filter(course => {
    const matchesSearch = course.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         course.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         course.instructor.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSemester = selectedSemester === 'All Semesters' || course.semester === selectedSemester;
    const matchesStatus = selectedStatus === 'All Statuses' || 
                         (selectedStatus === 'Active' && course.status === 'active') ||
                         (selectedStatus === 'Completed' && course.status === 'completed') ||
                         (selectedStatus === 'Dropped' && course.status === 'dropped');
    return matchesSearch && matchesSemester && matchesStatus;
  });

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      i < Math.floor(rating) ? (
        <StarIconSolid key={i} className="h-4 w-4 text-yellow-400" />
      ) : (
        <StarIcon key={i} className="h-4 w-4 text-gray-300" />
      )
    ));
  };

  const getProgressColor = (progress: number) => {
    if (progress >= 80) return 'bg-green-500';
    if (progress >= 50) return 'bg-blue-500';
    return 'bg-yellow-500';
  };

  const getGradeColor = (grade: string) => {
    if (grade.startsWith('A')) return 'bg-green-100 text-green-800';
    if (grade.startsWith('B')) return 'bg-blue-100 text-blue-800';
    if (grade.startsWith('C')) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            My Courses
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            {user?.role === 'student' ? 'Your enrolled courses for this semester' : 'Courses you are teaching'}
          </p>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search courses, instructors, or course codes..."
                className="input pl-10 w-full"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          
          {/* Semester Filter */}
          <div className="sm:w-48">
            <select
              className="input w-full"
              value={selectedSemester}
              onChange={(e) => setSelectedSemester(e.target.value)}
            >
              {semesters.map(semester => (
                <option key={semester} value={semester}>{semester}</option>
              ))}
            </select>
          </div>
          
          {/* Status Filter */}
          <div className="sm:w-36">
            <select
              className="input w-full"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
            >
              {statuses.map(status => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Course Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="card-content">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BookOpenIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Courses</p>
                <p className="text-2xl font-semibold text-gray-900">{filteredCourses.length}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="card-content">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <AcademicCapIcon className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Credits</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {filteredCourses.reduce((sum, course) => sum + course.credits, 0)}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="card-content">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ChartBarIcon className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Avg Progress</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {Math.round(filteredCourses.reduce((sum, course) => sum + course.progress, 0) / filteredCourses.length)}%
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="card-content">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <StarIcon className="h-6 w-6 text-yellow-500" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Avg Rating</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {(filteredCourses.reduce((sum, course) => sum + course.rating, 0) / filteredCourses.length).toFixed(1)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Courses Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {filteredCourses.map((course) => (
          <Link
            key={course.id}
            to={`/courses/${course.id}`}
            className="card hover:shadow-lg transition-shadow duration-200"
          >
            <div className="card-content">
              {/* Course Header */}
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{course.title}</h3>
                  <p className="text-sm text-gray-500">{course.code} • {course.semester}</p>
                </div>
                <span className={cn(
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                  getGradeColor(course.grade)
                )}>
                  {course.grade}
                </span>
              </div>

              {/* Instructor and Rating */}
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm text-gray-600">{course.instructor}</p>
                <div className="flex items-center space-x-1">
                  {renderStars(course.rating)}
                  <span className="text-xs text-gray-500 ml-1">({course.rating})</span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Progress</span>
                  <span>{course.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={cn('h-2 rounded-full', getProgressColor(course.progress))}
                    style={{ width: `${course.progress}%` }}
                  />
                </div>
              </div>

              {/* Course Info */}
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center">
                  <ClockIcon className="h-4 w-4 mr-2" />
                  <span>{course.schedule}</span>
                </div>
                <div className="flex items-center">
                  <UserGroupIcon className="h-4 w-4 mr-2" />
                  <span>{course.enrollment.current}/{course.enrollment.max} enrolled</span>
                </div>
                <div className="flex items-center">
                  <AcademicCapIcon className="h-4 w-4 mr-2" />
                  <span>{course.credits} credits</span>
                </div>
              </div>

              {/* Next Assignment */}
              {course.nextAssignment && (
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                  <div className="flex items-start">
                    <CalendarDaysIcon className="h-4 w-4 text-yellow-600 mt-0.5 mr-2" />
                    <div>
                      <p className="text-sm font-medium text-yellow-800">{course.nextAssignment}</p>
                      <p className="text-xs text-yellow-700">Due: {new Date(course.nextAssignmentDue).toLocaleDateString()}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Link>
        ))}
      </div>

      {/* Empty State */}
      {filteredCourses.length === 0 && (
        <div className="text-center py-12">
          <BookOpenIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No courses found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm || selectedSemester !== 'All Semesters' || selectedStatus !== 'All Statuses'
              ? 'Try adjusting your search or filters.'
              : 'You are not enrolled in any courses yet.'}
          </p>
        </div>
      )}
    </div>
  );
}
