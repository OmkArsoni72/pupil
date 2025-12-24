'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import Link from 'next/link';
import { FaHome, FaBook, FaClipboardList, FaChartLine, FaTrophy, FaCog, FaSignOutAlt } from 'react-icons/fa';

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
    if (!isAuthenticated) {
      router.push('/login');
    } else if (user?.role !== 'student') {
      router.push('/teacher/dashboard');
    }
  }, [isAuthenticated, user, router]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (!isHydrated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  const menuItems = [
    { name: 'Dashboard', icon: FaHome, href: '/student/dashboard' },
    { name: 'My Learning', icon: FaBook, href: '/student/learn' },
    { name: 'Assessments', icon: FaClipboardList, href: '/student/assessments' },
    { name: 'Progress', icon: FaChartLine, href: '/student/progress' },
    { name: 'Achievements', icon: FaTrophy, href: '/student/achievements' },
    { name: 'Settings', icon: FaCog, href: '/student/settings' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-lg fixed h-full">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-purple-600">PupilLearn</h2>
          <p className="text-sm text-gray-600 mt-1">{user?.name}</p>
          <div className="mt-3 flex items-center space-x-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div className="bg-purple-600 h-2 rounded-full" style={{ width: '65%' }} />
            </div>
            <span className="text-xs font-bold text-purple-600">Lvl {user?.gamification?.level || 1}</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">{user?.gamification?.points || 0} XP</p>
        </div>
        
        <nav className="p-4 space-y-2">
          {menuItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-purple-50 hover:text-purple-600 transition group"
            >
              <item.icon className="text-gray-400 group-hover:text-purple-600" />
              <span className="font-medium text-gray-700 group-hover:text-purple-600">{item.name}</span>
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-0 w-64 p-4 border-t border-gray-200">
          <button
            onClick={handleLogout}
            className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-red-50 hover:text-red-600 transition w-full"
          >
            <FaSignOutAlt />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="ml-64 flex-1 p-8">
        {children}
      </main>
    </div>
  );
}
