import React from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpenIcon,
  ClipboardDocumentListIcon,
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  SparklesIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  PlusIcon,
  HandRaisedIcon,
} from '@heroicons/react/24/outline';
import { cn } from '../utils/cn';
import { useAuth } from '../contexts/AuthContext';

const stats = [
  { 
    name: 'Enrolled Courses', 
    value: '12', 
    change: '+4.75%', 
    changeType: 'positive', 
    icon: BookOpenIcon,
    href: '/courses'
  },
  { 
    name: 'Pending Assessments', 
    value: '8', 
    change: '-2.02%', 
    changeType: 'negative', 
    icon: ClipboardDocumentListIcon,
    href: '/assessments'
  },
  { 
    name: 'Unread Messages', 
    value: '24', 
    change: '+12.5%', 
    changeType: 'positive', 
    icon: ChatBubbleLeftRightIcon,
    href: '/messages'
  },
  { 
    name: 'Average Score', 
    value: '92%', 
    change: '+5.4%', 
    changeType: 'positive', 
    icon: ChartBarIcon,
    href: '/analytics'
  },
];

const recentCourses = [
  {
    id: 1,
    name: 'Advanced Machine Learning',
    progress: 75,
    instructor: 'Dr. Sarah Wilson',
    nextClass: '2025-09-10T14:00:00Z',
    status: 'active',
  },
  {
    id: 2,
    name: 'Database Systems Design',
    progress: 45,
    instructor: 'Prof. Michael Chen',
    nextClass: '2025-09-11T10:00:00Z',
    status: 'active',
  },
  {
    id: 3,
    name: 'Web Development Fundamentals',
    progress: 90,
    instructor: 'Dr. Emily Rodriguez',
    nextClass: '2025-09-12T16:00:00Z',
    status: 'nearly-complete',
  },
];

const recentActivities = [
  {
    id: 1,
    type: 'assignment_submitted',
    title: 'Machine Learning Project Phase 2',
    course: 'Advanced Machine Learning',
    time: '2 hours ago',
    status: 'submitted',
  },
  {
    id: 2,
    type: 'quiz_completed',
    title: 'SQL Fundamentals Quiz',
    course: 'Database Systems Design',
    time: '5 hours ago',
    status: 'graded',
    score: 95,
  },
  {
    id: 3,
    type: 'message_received',
    title: 'New message from Dr. Sarah Wilson',
    course: 'Advanced Machine Learning',
    time: '1 day ago',
    status: 'unread',
  },
  {
    id: 4,
    type: 'content_released',
    title: 'Week 8 Materials Available',
    course: 'Web Development Fundamentals',
    time: '2 days ago',
    status: 'new',
  },
];

export default function DashboardPage() {
  const { user } = useAuth();
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center">
            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
              Welcome back, {user?.first_name}!
            </h2>
            <div className="ml-3 flex-shrink-0">
              <HandRaisedIcon className="h-6 w-6 text-primary-500" />
            </div>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Here's what's happening with your courses today.
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button className="btn-outline mr-3">
            <SparklesIcon className="h-4 w-4 mr-2" />
            AI Assistant
          </button>
          <button className="btn-primary">
            <PlusIcon className="h-4 w-4 mr-2" />
            New Course
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((item) => (
          <Link
            key={item.name}
            to={item.href}
            className="card hover:shadow-md transition-shadow duration-200"
          >
            <div className="card-content">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <item.icon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {item.name}
                    </dt>
                    <dd>
                      <div className="flex items-baseline">
                        <div className="text-2xl font-semibold text-gray-900">
                          {item.value}
                        </div>
                        <div
                          className={cn(
                            'ml-2 flex items-baseline text-sm font-semibold',
                            item.changeType === 'positive'
                              ? 'text-green-600'
                              : 'text-red-600'
                          )}
                        >
                          {item.changeType === 'positive' ? (
                            <ArrowUpIcon
                              className="self-center flex-shrink-0 h-4 w-4 text-green-500"
                              aria-hidden="true"
                            />
                          ) : (
                            <ArrowDownIcon
                              className="self-center flex-shrink-0 h-4 w-4 text-red-500"
                              aria-hidden="true"
                            />
                          )}
                          <span className="sr-only">
                            {item.changeType === 'positive' ? 'Increased' : 'Decreased'} by
                          </span>
                          {item.change}
                        </div>
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent Courses */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Recent Courses
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Your active courses and progress
            </p>
          </div>
          <div className="card-content">
            <div className="space-y-4">
              {recentCourses.map((course) => (
                <div key={course.id} className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 bg-primary-100 rounded-lg flex items-center justify-center">
                      <BookOpenIcon className="h-5 w-5 text-primary-600" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {course.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {course.instructor}
                    </p>
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={cn(
                            "h-2 rounded-full",
                            course.progress > 80 ? "bg-green-600" : 
                            course.progress > 50 ? "bg-blue-600" : "bg-yellow-600"
                          )}
                          style={{ width: `${course.progress}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {course.progress}% complete
                      </p>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <span
                      className={cn(
                        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                        course.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-blue-100 text-blue-800'
                      )}
                    >
                      {course.status === 'active' ? 'Active' : 'Nearly Complete'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6">
              <Link
                to="/courses"
                className="w-full text-center btn-outline"
              >
                View All Courses
              </Link>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Recent Activity
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Your latest learning activities
            </p>
          </div>
          <div className="card-content">
            <div className="flow-root">
              <ul className="-mb-8">
                {recentActivities.map((activity, activityIdx) => (
                  <li key={activity.id}>
                    <div className="relative pb-8">
                      {activityIdx !== recentActivities.length - 1 ? (
                        <span
                          className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                          aria-hidden="true"
                        />
                      ) : null}
                      <div className="relative flex space-x-3">
                        <div>
                          <span
                            className={cn(
                              "h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white",
                              activity.type === 'assignment_submitted' ? "bg-blue-500" :
                              activity.type === 'quiz_completed' ? "bg-green-500" :
                              activity.type === 'message_received' ? "bg-yellow-500" :
                              "bg-gray-500"
                            )}
                          >
                            {activity.type === 'assignment_submitted' && (
                              <ClipboardDocumentListIcon className="h-4 w-4 text-white" />
                            )}
                            {activity.type === 'quiz_completed' && (
                              <ChartBarIcon className="h-4 w-4 text-white" />
                            )}
                            {activity.type === 'message_received' && (
                              <ChatBubbleLeftRightIcon className="h-4 w-4 text-white" />
                            )}
                            {activity.type === 'content_released' && (
                              <BookOpenIcon className="h-4 w-4 text-white" />
                            )}
                          </span>
                        </div>
                        <div className="min-w-0 flex-1">
                          <div>
                            <div className="text-sm">
                              <span className="font-medium text-gray-900">
                                {activity.title}
                              </span>
                            </div>
                            <p className="mt-0.5 text-sm text-gray-500">
                              {activity.course}
                            </p>
                            {activity.score && (
                              <p className="mt-0.5 text-sm text-green-600 font-medium">
                                Score: {activity.score}%
                              </p>
                            )}
                          </div>
                          <div className="mt-2 text-sm text-gray-500">
                            <time>{activity.time}</time>
                          </div>
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
            <div className="mt-6">
              <a
                href="#"
                className="w-full text-center btn-outline"
              >
                View All Activity
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* AI Insights */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center">
            <SparklesIcon className="h-5 w-5 text-purple-500 mr-2" />
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              AI Insights
            </h3>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Personalized recommendations based on your learning patterns
          </p>
        </div>
        <div className="card-content">
          <div className="bg-purple-50 border border-purple-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <SparklesIcon className="h-5 w-5 text-purple-400" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-purple-800">
                  Study Recommendation
                </h3>
                <div className="mt-2 text-sm text-purple-700">
                  <p>
                    You're performing excellently in Machine Learning! Consider tackling 
                    the bonus advanced topics to deepen your understanding. Also, spend 
                    some extra time on Database Systems - you have an exam coming up next week.
                  </p>
                </div>
                <div className="mt-4">
                  <div className="-mx-2 -my-1.5 flex">
                    <button className="bg-purple-100 px-2 py-1.5 rounded-md text-xs font-medium text-purple-800 hover:bg-purple-200 mr-2">
                      Schedule Study Time
                    </button>
                    <button className="bg-purple-100 px-2 py-1.5 rounded-md text-xs font-medium text-purple-800 hover:bg-purple-200">
                      Get More Tips
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
