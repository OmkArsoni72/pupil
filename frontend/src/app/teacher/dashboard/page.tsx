'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { apiClient } from '@/lib/api/client';
import { FaBook, FaClipboardList, FaUsers, FaChartLine, FaPlus, FaClock, FaCheckCircle } from 'react-icons/fa';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

export default function TeacherDashboard() {
  const user = useAuthStore((state) => state.user);
  const [stats, setStats] = useState({
    totalClasses: 0,
    totalStudents: 0,
    activeContent: 0,
    completedAssessments: 0,
  });
  const [recentSessions, setRecentSessions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      
      try {
        // Load classes
        const classes = await apiClient.getTeacherClasses();
        
        // Load recent sessions
        const sessions = await apiClient.getSessions({ limit: 5 });
        
        setStats({
          totalClasses: classes.length || 0,
          totalStudents: classes.reduce((sum: number, c: any) => sum + (c.students?.length || 0), 0),
          activeContent: 12, // Mock data
          completedAssessments: 8, // Mock data
        });
        
        setRecentSessions(sessions.items || sessions || []);
      } catch (apiError) {
        console.error('API Error:', apiError);
        // Use mock data on error
        setStats({
          totalClasses: 0,
          totalStudents: 0,
          activeContent: 12,
          completedAssessments: 8,
        });
        setRecentSessions([]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const statCards = [
    { title: 'My Classes', value: stats.totalClasses, icon: FaUsers, color: 'blue' },
    { title: 'Total Students', value: stats.totalStudents, icon: FaChartLine, color: 'green' },
    { title: 'Active Content', value: stats.activeContent, icon: FaBook, color: 'purple' },
    { title: 'Assessments', value: stats.completedAssessments, icon: FaClipboardList, color: 'orange' },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Welcome back, {user?.name}!</h1>
          <p className="text-gray-600 mt-1">Here's what's happening with your classes today.</p>
        </div>
        <Link
          href="/teacher/content"
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition shadow-md hover:shadow-lg flex items-center space-x-2"
        >
          <FaPlus />
          <span>Generate Content</span>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <div
            key={index}
            className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">{stat.title}</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {isLoading ? '...' : stat.value}
                </p>
              </div>
              <div className={`w-12 h-12 bg-${stat.color}-100 rounded-lg flex items-center justify-center`}>
                <stat.icon className={`text-2xl text-${stat.color}-600`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-6">
        <Link
          href="/teacher/content"
          className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-xl p-6 hover:shadow-xl transition"
        >
          <FaBook className="text-3xl mb-3" />
          <h3 className="text-xl font-bold mb-2">Generate Content</h3>
          <p className="text-blue-100">Create multi-modal learning content for your classes</p>
        </Link>

        <Link
          href="/teacher/assessments"
          className="bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-xl p-6 hover:shadow-xl transition"
        >
          <FaClipboardList className="text-3xl mb-3" />
          <h3 className="text-xl font-bold mb-2">Create Assessment</h3>
          <p className="text-purple-100">Generate AI-powered assessments and quizzes</p>
        </Link>

        <Link
          href="/teacher/classes"
          className="bg-gradient-to-br from-green-500 to-green-600 text-white rounded-xl p-6 hover:shadow-xl transition"
        >
          <FaUsers className="text-3xl mb-3" />
          <h3 className="text-xl font-bold mb-2">Manage Classes</h3>
          <p className="text-green-100">View student performance and learning gaps</p>
        </Link>
      </div>

      {/* Recent Sessions */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Recent Sessions</h2>
          <Link href="/teacher/sessions" className="text-blue-600 hover:text-blue-700 font-medium">
            View All
          </Link>
        </div>

        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Loading sessions...</div>
        ) : recentSessions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FaClock className="text-4xl mx-auto mb-3 text-gray-300" />
            <p>No recent sessions yet</p>
            <Link href="/teacher/content" className="text-blue-600 hover:text-blue-700 mt-2 inline-block">
              Create your first session
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {recentSessions.slice(0, 5).map((session: any) => (
              <div
                key={session._id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition"
              >
                <div className="flex items-center space-x-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    session.status === 'completed' ? 'bg-green-100' : 
                    session.status === 'live' ? 'bg-blue-100' : 'bg-gray-100'
                  }`}>
                    {session.status === 'completed' ? (
                      <FaCheckCircle className="text-green-600" />
                    ) : (
                      <FaClock className={session.status === 'live' ? 'text-blue-600' : 'text-gray-600'} />
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{session.topic || 'Session'}</h3>
                    <p className="text-sm text-gray-600">
                      {session.subject} • Grade {session.grade}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium capitalize text-gray-700">{session.status}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(session.session_date).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tips Section */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-100">
        <h3 className="text-lg font-bold text-gray-900 mb-3">💡 Quick Tips</h3>
        <ul className="space-y-2 text-gray-700">
          <li>• Use content generation to create engaging learning materials in 10 different modes</li>
          <li>• Monitor student performance in real-time during live classes</li>
          <li>• Let AI identify learning gaps and generate personalized remediation content</li>
          <li>• Create assessments that adapt to your curriculum and student needs</li>
        </ul>
      </div>
    </div>
  );
}
