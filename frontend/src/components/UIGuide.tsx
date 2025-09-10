import React from 'react';
import { 
  AcademicCapIcon, 
  BookOpenIcon, 
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  StarIcon,
  UserIcon,
  ChartBarIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const UIGuide: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-6">
        <div className="max-w-6xl mx-auto">
          <h1 className="mb-8">Intelligent LMS Design System</h1>
          <p className="text-xl text-gray-600 mb-12 max-w-3xl">
            A comprehensive design system built for academic excellence. This guide showcases 
            our typography, color palette, components, and patterns used throughout the LMS platform.
          </p>

          {/* Typography Section */}
          <section className="mb-16">
            <h2>Typography</h2>
            <div className="space-y-8">
              <div>
                <h3 className="mb-4">Headings</h3>
                <div className="space-y-4 bg-white p-6 rounded-lg border">
                  <h1>Heading 1 - Main Page Titles</h1>
                  <h2>Heading 2 - Section Headers</h2>
                  <h3>Heading 3 - Subsection Headers</h3>
                  <h4>Heading 4 - Component Titles</h4>
                  <h5>Heading 5 - Small Component Titles</h5>
                  <h6>Heading 6 - Micro Headers</h6>
                </div>
              </div>
              
              <div>
                <h3 className="mb-4">Body Text & Elements</h3>
                <div className="bg-white p-6 rounded-lg border space-y-4">
                  <p>
                    This is a paragraph with <strong>bold text</strong>, <em>italic text</em>, and a 
                    <a href="#"> link to another resource</a>. The paragraph demonstrates our base 
                    typography styles with proper line height and spacing.
                  </p>
                  <p>
                    Code can be displayed <code>inline like this</code> or in blocks:
                  </p>
                  <pre><code>{`function example() {
  console.log("Hello, LMS!");
}`}</code></pre>
                  <blockquote>
                    "Education is the most powerful weapon which you can use to change the world." 
                    - Nelson Mandela
                  </blockquote>
                </div>
              </div>
            </div>
          </section>

          {/* Color Palette */}
          <section className="mb-16">
            <h2>Color Palette</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              <ColorPaletteCard 
                title="Primary (Academic Blue)"
                colors={[
                  { name: '50', class: 'bg-primary-50', hex: '#f0f7ff' },
                  { name: '100', class: 'bg-primary-100', hex: '#e0efff' },
                  { name: '200', class: 'bg-primary-200', hex: '#b9ddff' },
                  { name: '300', class: 'bg-primary-300', hex: '#7cc4ff' },
                  { name: '400', class: 'bg-primary-400', hex: '#36a7ff' },
                  { name: '500', class: 'bg-primary-500', hex: '#0c8ce9' },
                  { name: '600', class: 'bg-primary-600', hex: '#0066cc' },
                  { name: '700', class: 'bg-primary-700', hex: '#0052a3' },
                  { name: '800', class: 'bg-primary-800', hex: '#003d7a' },
                  { name: '900', class: 'bg-primary-900', hex: '#003366' },
                ]}
              />
              
              <ColorPaletteCard 
                title="Secondary (Academic Gold)"
                colors={[
                  { name: '50', class: 'bg-secondary-50', hex: '#fffbeb' },
                  { name: '100', class: 'bg-secondary-100', hex: '#fef3c7' },
                  { name: '200', class: 'bg-secondary-200', hex: '#fde68a' },
                  { name: '300', class: 'bg-secondary-300', hex: '#fcd34d' },
                  { name: '400', class: 'bg-secondary-400', hex: '#fbbf24' },
                  { name: '500', class: 'bg-secondary-500', hex: '#f59e0b' },
                  { name: '600', class: 'bg-secondary-600', hex: '#d97706' },
                  { name: '700', class: 'bg-secondary-700', hex: '#b45309' },
                  { name: '800', class: 'bg-secondary-800', hex: '#92400e' },
                  { name: '900', class: 'bg-secondary-900', hex: '#78350f' },
                ]}
              />
              
              <ColorPaletteCard 
                title="Success (Progress Green)"
                colors={[
                  { name: '50', class: 'bg-success-50', hex: '#f0fdf4' },
                  { name: '100', class: 'bg-success-100', hex: '#dcfce7' },
                  { name: '200', class: 'bg-success-200', hex: '#bbf7d0' },
                  { name: '300', class: 'bg-success-300', hex: '#86efac' },
                  { name: '400', class: 'bg-success-400', hex: '#4ade80' },
                  { name: '500', class: 'bg-success-500', hex: '#22c55e' },
                  { name: '600', class: 'bg-success-600', hex: '#16a34a' },
                  { name: '700', class: 'bg-success-700', hex: '#15803d' },
                  { name: '800', class: 'bg-success-800', hex: '#166534' },
                  { name: '900', class: 'bg-success-900', hex: '#14532d' },
                ]}
              />
            </div>
          </section>

          {/* Buttons */}
          <section className="mb-16">
            <h2>Buttons</h2>
            <div className="bg-white p-8 rounded-lg border">
              <div className="space-y-6">
                <div>
                  <h4 className="mb-4">Primary Buttons</h4>
                  <div className="flex flex-wrap gap-4">
                    <button className="btn-primary">Primary Button</button>
                    <button className="btn-primary" disabled>Disabled Primary</button>
                    <button className="btn-primary">
                      <AcademicCapIcon className="w-4 h-4 mr-2" />
                      With Icon
                    </button>
                  </div>
                </div>
                
                <div>
                  <h4 className="mb-4">Secondary & Outline Buttons</h4>
                  <div className="flex flex-wrap gap-4">
                    <button className="btn-secondary">Secondary Button</button>
                    <button className="btn-outline">Outline Button</button>
                    <button className="btn-ghost">Ghost Button</button>
                  </div>
                </div>
                
                <div>
                  <h4 className="mb-4">Button Sizes</h4>
                  <div className="flex flex-wrap items-center gap-4">
                    <button className="btn-primary text-xs px-2 py-1">Small</button>
                    <button className="btn-primary">Regular</button>
                    <button className="btn-primary text-lg px-6 py-3">Large</button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Form Elements */}
          <section className="mb-16">
            <h2>Form Elements</h2>
            <div className="bg-white p-8 rounded-lg border">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h4 className="mb-4">Input Fields</h4>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email Address
                      </label>
                      <input 
                        type="email" 
                        className="input"
                        placeholder="student@university.edu"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Password
                      </label>
                      <input 
                        type="password" 
                        className="input"
                        placeholder="Enter your password"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Message
                      </label>
                      <textarea 
                        className="input h-24"
                        placeholder="Type your message here..."
                      />
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="mb-4">Select & Options</h4>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Course Level
                      </label>
                      <select className="input">
                        <option>Select a level</option>
                        <option>Beginner</option>
                        <option>Intermediate</option>
                        <option>Advanced</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Preferences
                      </label>
                      <div className="space-y-2">
                        <label className="flex items-center">
                          <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 mr-2" />
                          Email notifications
                        </label>
                        <label className="flex items-center">
                          <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 mr-2" />
                          SMS reminders
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Cards */}
          <section className="mb-16">
            <h2>Cards & Content Containers</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold">Course Card</h3>
                  <p className="text-sm text-gray-600">Introduction to Computer Science</p>
                </div>
                <div className="card-content">
                  <p className="text-gray-700 mb-4">
                    Learn the fundamentals of programming and computational thinking.
                  </p>
                  <div className="flex items-center space-x-2 mb-4">
                    <span className="badge-primary">CS 101</span>
                    <span className="badge-success">4 Credits</span>
                  </div>
                  <div className="progress progress-primary mb-2">
                    <div className="progress-bar" style={{ width: '75%' }}></div>
                  </div>
                  <p className="text-xs text-gray-500">75% Complete</p>
                </div>
                <div className="card-footer">
                  <button className="btn-primary w-full">Continue Learning</button>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold">Assignment Due</h3>
                  <p className="text-sm text-gray-600">Data Structures Project</p>
                </div>
                <div className="card-content">
                  <p className="text-gray-700 mb-4">
                    Implement a binary search tree with insertion and deletion operations.
                  </p>
                  <div className="flex items-center space-x-2 mb-4">
                    <ClockIcon className="w-4 h-4 text-warning-600" />
                    <span className="text-sm text-warning-700">Due in 2 days</span>
                  </div>
                </div>
                <div className="card-footer">
                  <button className="btn-outline w-full">View Assignment</button>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold">Grade Report</h3>
                  <p className="text-sm text-gray-600">Mid-term Performance</p>
                </div>
                <div className="card-content">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl font-bold text-gray-900">85%</span>
                    <ChartBarIcon className="w-8 h-8 text-primary-600" />
                  </div>
                  <p className="text-gray-700 text-sm">Above average performance</p>
                </div>
              </div>
            </div>
          </section>

          {/* Badges & Labels */}
          <section className="mb-16">
            <h2>Badges & Status Indicators</h2>
            <div className="bg-white p-8 rounded-lg border">
              <div className="space-y-6">
                <div>
                  <h4 className="mb-4">Status Badges</h4>
                  <div className="flex flex-wrap gap-2">
                    <span className="badge-primary">Active</span>
                    <span className="badge-secondary">Featured</span>
                    <span className="badge-success">Completed</span>
                    <span className="badge-warning">Pending</span>
                    <span className="badge-danger">Overdue</span>
                    <span className="badge-gray">Draft</span>
                  </div>
                </div>
                
                <div>
                  <h4 className="mb-4">Course Tags</h4>
                  <div className="flex flex-wrap gap-2">
                    <span className="badge-primary">Computer Science</span>
                    <span className="badge-secondary">Mathematics</span>
                    <span className="badge-success">Beginner</span>
                    <span className="badge-primary">4 Credits</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Alerts */}
          <section className="mb-16">
            <h2>Alerts & Notifications</h2>
            <div className="space-y-4">
              <div className="alert-success flex items-start">
                <CheckCircleIcon className="w-5 h-5 mr-3 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-semibold mb-1">Assignment Submitted Successfully!</h4>
                  <p>Your assignment has been submitted and will be reviewed by the instructor.</p>
                </div>
              </div>
              
              <div className="alert-warning flex items-start">
                <ExclamationTriangleIcon className="w-5 h-5 mr-3 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-semibold mb-1">Assignment Due Soon</h4>
                  <p>Your Data Structures project is due in 2 days. Don't forget to submit it on time.</p>
                </div>
              </div>
              
              <div className="alert-danger flex items-start">
                <ExclamationCircleIcon className="w-5 h-5 mr-3 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-semibold mb-1">Assignment Overdue</h4>
                  <p>Your assignment was due yesterday. Please contact your instructor immediately.</p>
                </div>
              </div>
              
              <div className="alert-info flex items-start">
                <InformationCircleIcon className="w-5 h-5 mr-3 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-semibold mb-1">New Course Available</h4>
                  <p>A new advanced algorithms course has been added to your recommended courses.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Loading States */}
          <section className="mb-16">
            <h2>Loading States</h2>
            <div className="bg-white p-8 rounded-lg border">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h4 className="mb-4">Spinners</h4>
                  <div className="flex items-center space-x-4">
                    <div className="spinner"></div>
                    <button className="btn-primary" disabled>
                      <div className="spinner mr-2"></div>
                      Loading...
                    </button>
                  </div>
                </div>
                
                <div>
                  <h4 className="mb-4">Skeleton Loading</h4>
                  <div className="space-y-3">
                    <div className="skeleton-title"></div>
                    <div className="skeleton-text"></div>
                    <div className="skeleton-text"></div>
                    <div className="flex items-center space-x-3">
                      <div className="skeleton-avatar"></div>
                      <div className="flex-1">
                        <div className="skeleton-text"></div>
                        <div className="skeleton-text w-1/2"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Progress Indicators */}
          <section className="mb-16">
            <h2>Progress Indicators</h2>
            <div className="bg-white p-8 rounded-lg border space-y-6">
              <div>
                <h4 className="mb-4">Course Progress</h4>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Introduction to Programming</span>
                      <span className="text-gray-600">85%</span>
                    </div>
                    <div className="progress progress-primary">
                      <div className="progress-bar" style={{ width: '85%' }}></div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Data Structures</span>
                      <span className="text-gray-600">60%</span>
                    </div>
                    <div className="progress progress-success">
                      <div className="progress-bar" style={{ width: '60%' }}></div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Algorithms</span>
                      <span className="text-gray-600">30%</span>
                    </div>
                    <div className="progress progress-warning">
                      <div className="progress-bar" style={{ width: '30%' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

        </div>
      </div>
    </div>
  );
};

interface ColorPaletteCardProps {
  title: string;
  colors: { name: string; class: string; hex: string }[];
}

const ColorPaletteCard: React.FC<ColorPaletteCardProps> = ({ title, colors }) => {
  return (
    <div className="bg-white rounded-lg border overflow-hidden">
      <div className="p-4 border-b">
        <h4 className="font-semibold text-gray-900">{title}</h4>
      </div>
      <div className="space-y-0">
        {colors.map((color) => (
          <div key={color.name} className="flex items-center">
            <div className={`w-16 h-12 ${color.class}`}></div>
            <div className="px-4 flex-1">
              <div className="text-sm font-medium text-gray-900">{color.name}</div>
              <div className="text-xs text-gray-500 font-mono">{color.hex}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default UIGuide;
