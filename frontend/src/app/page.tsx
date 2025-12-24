import Link from 'next/link';
import { FaGraduationCap, FaChalkboardTeacher, FaUserGraduate, FaBrain } from 'react-icons/fa';

export const dynamic = 'force-dynamic';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <nav className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FaGraduationCap className="text-4xl text-blue-600" />
            <span className="text-2xl font-bold text-gray-900">PupilPrep</span>
          </div>
          <div className="space-x-4">
            <Link
              href="/login"
              className="px-6 py-2 text-blue-600 hover:text-blue-700 font-medium transition"
            >
              Login
            </Link>
            <Link
              href="/register"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Get Started
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 animate-fade-in">
            AI-Powered Personalized
            <span className="block text-blue-600">Learning Platform</span>
          </h1>
          <p className="text-xl text-gray-600 mb-10 animate-slide-up">
            Empowering educators and students with intelligent content generation,
            adaptive learning paths, and comprehensive performance analytics.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/register?role=teacher"
              className="px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-lg font-semibold shadow-lg hover:shadow-xl"
            >
              I'm a Teacher
            </Link>
            <Link
              href="/register?role=student"
              className="px-8 py-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition text-lg font-semibold shadow-lg hover:shadow-xl"
            >
              I'm a Student
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Powerful Features for Modern Education
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <FaChalkboardTeacher className="text-2xl text-blue-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              For Teachers
            </h3>
            <ul className="space-y-2 text-gray-600">
              <li>• AI-powered content generation</li>
              <li>• Automated assessment creation</li>
              <li>• Real-time class management</li>
              <li>• Performance analytics</li>
              <li>• Learning gap identification</li>
            </ul>
          </div>

          {/* Feature 2 */}
          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <FaUserGraduate className="text-2xl text-purple-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              For Students
            </h3>
            <ul className="space-y-2 text-gray-600">
              <li>• 10 personalized learning modes</li>
              <li>• Adaptive remediation sessions</li>
              <li>• Interactive assessments</li>
              <li>• Progress tracking</li>
              <li>• Gamified learning experience</li>
            </ul>
          </div>

          {/* Feature 3 */}
          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <FaBrain className="text-2xl text-green-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              AI Intelligence
            </h3>
            <ul className="space-y-2 text-gray-600">
              <li>• Multi-modal content generation</li>
              <li>• Intelligent gap analysis</li>
              <li>• Personalized learning paths</li>
              <li>• Automated remediation</li>
              <li>• Context-aware recommendations</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Learning Modes Section */}
      <section className="container mx-auto px-4 py-20 bg-gray-50 rounded-3xl">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          10 Unique Learning Modes
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-6">
          {[
            { name: 'Reading', icon: '📖', color: 'blue' },
            { name: 'Writing', icon: '✍️', color: 'purple' },
            { name: 'Watching', icon: '🎥', color: 'red' },
            { name: 'Playing', icon: '🎮', color: 'green' },
            { name: 'Doing', icon: '🔬', color: 'yellow' },
            { name: 'Solving', icon: '🧮', color: 'indigo' },
            { name: 'Questioning', icon: '❓', color: 'pink' },
            { name: 'Listening', icon: '🎧', color: 'cyan' },
            { name: 'Assessment', icon: '📝', color: 'orange' },
            { name: 'AI Tutor', icon: '🤖', color: 'teal' },
          ].map((mode, index) => (
            <div
              key={index}
              className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition text-center"
            >
              <div className="text-4xl mb-3">{mode.icon}</div>
              <h4 className="font-semibold text-gray-900">{mode.name}</h4>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <h2 className="text-4xl font-bold text-gray-900 mb-6">
          Ready to Transform Education?
        </h2>
        <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
          Join thousands of educators and students already using PupilPrep
          to create personalized, engaging learning experiences.
        </p>
        <Link
          href="/register"
          className="inline-block px-10 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-lg font-semibold shadow-xl hover:shadow-2xl"
        >
          Start Free Trial
        </Link>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 border-t border-gray-200">
        <div className="text-center text-gray-600">
          <p>&copy; 2025 PupilPrep. Empowering Education with AI.</p>
        </div>
      </footer>
    </div>
  );
}
