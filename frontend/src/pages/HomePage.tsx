import React from 'react';
import { Link } from 'react-router-dom';
import { 
  AcademicCapIcon, 
  SparklesIcon, 
  ChartBarIcon, 
  ChatBubbleLeftRightIcon,
  ArrowRightIcon 
} from '@heroicons/react/24/outline';

const features = [
  {
    name: 'AI-Powered Content Generation',
    description: 'Automatically generate summaries, quizzes, and learning objectives from your course materials.',
    icon: SparklesIcon,
  },
  {
    name: 'Intelligent Assessments',
    description: 'Create adaptive quizzes with AI-assisted grading and detailed feedback for students.',
    icon: AcademicCapIcon,
  },
  {
    name: 'Smart Analytics',
    description: 'Track student progress with AI insights and predictive analytics to identify at-risk learners.',
    icon: ChartBarIcon,
  },
  {
    name: 'Enhanced Communication',
    description: 'AI-assisted email drafting and sentiment analysis to improve student-instructor interactions.',
    icon: ChatBubbleLeftRightIcon,
  },
];

export default function HomePage() {
  return (
    <div className="bg-white">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="bg-primary-600 rounded-lg p-2">
                <AcademicCapIcon className="h-8 w-8 text-white" />
              </div>
              <div className="ml-3">
                <h1 className="text-2xl font-bold text-gray-900">Intelligent LMS</h1>
                <p className="text-sm text-gray-500">AI-Powered Learning Management</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/login"
                className="btn-outline"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="btn-primary"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero section */}
      <div className="relative bg-white overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="relative z-10 pb-8 bg-white sm:pb-16 md:pb-20 lg:max-w-2xl lg:w-full lg:pb-28 xl:pb-32">
            <main className="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
              <div className="sm:text-center lg:text-left">
                <h1 className="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                  <span className="block xl:inline">Modern Learning with</span>{' '}
                  <span className="block text-primary-600 xl:inline">AI Intelligence</span>
                </h1>
                <p className="mt-3 text-base text-gray-500 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                  Transform your educational experience with our AI-native Learning Management System. 
                  Streamline course creation, enhance assessments, and provide personalized learning paths 
                  for every student.
                </p>
                <div className="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start">
                  <div className="rounded-md shadow">
                    <Link
                      to="/dashboard"
                      className="btn-primary w-full flex items-center justify-center px-8 py-3 text-base font-medium"
                    >
                      Get Started
                      <ArrowRightIcon className="ml-2 h-5 w-5" />
                    </Link>
                  </div>
                  <div className="mt-3 sm:mt-0 sm:ml-3">
                    <a
                      href="#features"
                      className="btn-outline w-full flex items-center justify-center px-8 py-3 text-base font-medium"
                    >
                      Learn More
                    </a>
                  </div>
                </div>
              </div>
            </main>
          </div>
        </div>
        <div className="lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2">
          <div className="h-56 w-full bg-gradient-to-br from-primary-400 to-primary-600 sm:h-72 md:h-96 lg:w-full lg:h-full flex items-center justify-center">
            <div className="text-center text-white">
              <SparklesIcon className="mx-auto h-24 w-24 mb-4 opacity-80" />
              <h3 className="text-xl font-semibold">AI-Powered Education</h3>
              <p className="text-primary-100 mt-2">The future of learning is here</p>
            </div>
          </div>
        </div>
      </div>

      {/* Features section */}
      <div id="features" className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="lg:text-center">
            <h2 className="text-base text-primary-600 font-semibold tracking-wide uppercase">Features</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
              Everything you need for modern education
            </p>
            <p className="mt-4 max-w-2xl text-xl text-gray-500 lg:mx-auto">
              Our AI-powered LMS combines the best of traditional learning management with cutting-edge artificial intelligence.
            </p>
          </div>

          <div className="mt-10">
            <dl className="space-y-10 md:space-y-0 md:grid md:grid-cols-2 md:gap-x-8 md:gap-y-10">
              {features.map((feature) => (
                <div key={feature.name} className="relative">
                  <dt>
                    <div className="absolute flex items-center justify-center h-12 w-12 rounded-md bg-primary-500 text-white">
                      <feature.icon className="h-6 w-6" aria-hidden="true" />
                    </div>
                    <p className="ml-16 text-lg leading-6 font-medium text-gray-900">{feature.name}</p>
                  </dt>
                  <dd className="mt-2 ml-16 text-base text-gray-500">{feature.description}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>

      {/* CTA section */}
      <div className="bg-primary-700">
        <div className="max-w-2xl mx-auto text-center py-16 px-4 sm:py-20 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-extrabold text-white sm:text-4xl">
            <span className="block">Ready to revolutionize learning?</span>
            <span className="block">Start your AI-powered journey today.</span>
          </h2>
          <p className="mt-4 text-lg leading-6 text-primary-200">
            Join thousands of educators and students already benefiting from intelligent learning management.
          </p>
          <Link
            to="/login"
            className="mt-8 w-full inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-primary-600 bg-white hover:bg-primary-50 sm:w-auto"
          >
            Get Started Now
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 md:flex md:items-center md:justify-between lg:px-8">
          <div className="flex justify-center space-x-6 md:order-2">
            <p className="text-gray-400 text-sm">
              © 2025 Intelligent LMS. Built with AI for the future of education.
            </p>
          </div>
          <div className="mt-8 md:mt-0 md:order-1">
            <div className="flex items-center">
              <div className="bg-primary-600 rounded-lg p-1">
                <AcademicCapIcon className="h-6 w-6 text-white" />
              </div>
              <span className="ml-2 text-xl font-bold text-gray-900">Intelligent LMS</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
