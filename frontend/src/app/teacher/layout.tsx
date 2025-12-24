'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import Link from 'next/link';
import { FaHome, FaBook, FaClipboardList, FaUsers, FaCalendarAlt, FaChartBar, FaCog, FaSignOutAlt } from 'react-icons/fa';

export default function TeacherLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
    if (!isAuthenticated) {
      router.push('/login');
    } else if (user?.role !== 'teacher' && user?.role !== 'admin' && user?.role !== 'hod') {
      router.push('/student/dashboard');
    }
  }, [isAuthenticated, user, router]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (!isHydrated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  const menuItems = [
    { name: 'Dashboard', icon: FaHome, href: '/teacher/dashboard' },
    { name: 'Content Generation', icon: FaBook, href: '/teacher/content' },
    { name: 'Assessments', icon: FaClipboardList, href: '/teacher/assessments' },
    { name: 'My Classes', icon: FaUsers, href: '/teacher/classes' },
    { name: 'Timetable', icon: FaCalendarAlt, href: '/teacher/timetable' },
    { name: 'Reports', icon: FaChartBar, href: '/teacher/reports' },
    { name: 'Settings', icon: FaCog, href: '/teacher/settings' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-lg fixed h-full">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-blue-600">PupilTeach</h2>
          <p className="text-sm text-gray-600 mt-1">{user?.name}</p>
          <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
        </div>
        
        <nav className="p-4 space-y-2">
          {menuItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition group"
            >
              <item.icon className="text-gray-400 group-hover:text-blue-600" />
              <span className="font-medium text-gray-700 group-hover:text-blue-600">{item.name}</span>
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
