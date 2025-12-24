'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { FaBook, FaFire, FaTrophy, FaCalendarCheck, FaClock, FaPlay, FaStar } from 'react-icons/fa';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

export default function StudentDashboard() {
  const user = useAuthStore((state) => state.user);
  const [todaysTasks, setTodaysTasks] = useState([
    { id: 1, title: 'Physics - Newton\'s Laws', type: 'learn_by_reading', status: 'pending', duration: 30 },
    { id: 2, title: 'Math Practice Problems', type: 'learn_by_solving', status: 'in_progress', duration: 45 },
    { id: 3, title: 'Chemistry Experiment', type: 'learn_by_doing', status: 'pending', duration: 60 },
  ]);

  const stats = [
    { title: 'Daily Streak', value: '🔥 12 Days', icon: FaFire, color: 'orange' },
    { title: 'Tasks Completed', value: '24/30', icon: FaCalendarCheck, color: 'green' },
    { title: 'Total XP', value: user?.gamification?.points || 0, icon: FaStar, color: 'yellow' },
    { title: 'Achievements', value: user?.gamification?.badges?.length || 0, icon: FaTrophy, color: 'purple' },
  ];

  const learningModes = [
    { id: 'reading', name: 'Reading', icon: '📖', count: 5 },
    { id: 'watching', name: 'Watching', icon: '🎥', count: 3 },
    { id: 'solving', name: 'Solving', icon: '🧮', count: 8 },
    { id: 'playing', name: 'Playing', icon: '🎮', count: 2 },
  ];

  return (
    <div className="space-y-8">
      {/* Greeting */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl p-8 shadow-xl">
        <h1 className="text-3xl font-bold mb-2">Welcome back, {user?.name?.split(' ')[0]}! 👋</h1>
        <p className="text-purple-100">You're doing great! Keep up the amazing work.</p>
        <div className="mt-4 flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <FaFire className="text-orange-300 text-2xl" />
            <div>
              <p className="text-xs text-purple-200">Daily Streak</p>
              <p className="text-xl font-bold">12 Days</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <FaStar className="text-yellow-300 text-2xl" />
            <div>
              <p className="text-xs text-purple-200">Level</p>
              <p className="text-xl font-bold">{user?.gamification?.level || 1}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition">
            <div className="flex items-center justify-between mb-2">
              <p className="text-gray-600 text-sm font-medium">{stat.title}</p>
              <stat.icon className={`text-${stat.color}-600 text-xl`} />
            </div>
            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Today's Tasks */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Today's Learning Tasks</h2>
          <Link href="/student/learn" className="text-purple-600 hover:text-purple-700 font-medium">
            View All
          </Link>
        </div>

        <div className="space-y-4">
          {todaysTasks.map((task) => (
            <div
              key={task.id}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-purple-50 transition"
            >
              <div className="flex items-center space-x-4">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                  task.status === 'in_progress' ? 'bg-blue-100' : 'bg-gray-100'
                }`}>
                  {task.status === 'in_progress' ? (
                    <FaPlay className="text-blue-600" />
                  ) : (
                    <FaClock className="text-gray-600" />
                  )}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{task.title}</h3>
                  <p className="text-sm text-gray-600">
                    {task.type.replace('learn_by_', '').replace('_', ' ')} • {task.duration} min
                  </p>
                </div>
              </div>
              <Link
                href={`/student/learn/${task.id}`}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
              >
                {task.status === 'in_progress' ? 'Continue' : 'Start'}
              </Link>
            </div>
          ))}
        </div>
      </div>

      {/* Learning Modes Overview */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Your Learning Modes</h2>
        <div className="grid md:grid-cols-4 gap-4">
          {learningModes.map((mode) => (
            <Link
              key={mode.id}
              href={`/student/learn?mode=${mode.id}`}
              className="p-4 border border-gray-200 rounded-lg hover:border-purple-400 hover:shadow-md transition text-center"
            >
              <div className="text-4xl mb-2">{mode.icon}</div>
              <h3 className="font-semibold text-gray-900 mb-1">{mode.name}</h3>
              <p className="text-sm text-gray-600">{mode.count} tasks available</p>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Achievements */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Progress Chart */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Weekly Progress</h2>
          <div className="space-y-3">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, index) => {
              const progress = [80, 90, 75, 95, 85, 0, 0][index];
              return (
                <div key={day} className="flex items-center space-x-3">
                  <span className="text-sm font-medium text-gray-600 w-12">{day}</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-purple-600 h-3 rounded-full transition-all"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-gray-900 w-12">{progress}%</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Badges */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Achievements</h2>
          <div className="grid grid-cols-3 gap-4">
            {['🏆', '⭐', '🎯', '🔥', '💪', '🎓'].map((badge, index) => (
              <div
                key={index}
                className="aspect-square bg-gradient-to-br from-purple-100 to-blue-100 rounded-xl flex items-center justify-center text-4xl hover:scale-110 transition"
              >
                {badge}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Motivational Quote */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-100">
        <p className="text-lg font-medium text-gray-800 italic">
          "The beautiful thing about learning is that no one can take it away from you."
        </p>
        <p className="text-sm text-gray-600 mt-2">- B.B. King</p>
      </div>
    </div>
  );
}
