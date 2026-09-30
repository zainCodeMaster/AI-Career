import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { MobileNav } from './MobileNav';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/Button';
import { useNavigate } from 'react-router-dom';

const PAGE_TITLES: Record<string, string> = {
  '/jobs': 'Jobs',
  '/job-discovery': 'Job Discovery',
  '/resumes': 'Resumes',
  '/dashboard': 'CRM Dashboard',
  '/applications': 'Applications',
  '/pipeline': 'Pipeline',
  '/profile': 'Career Profile',
  '/career-brain': 'Career Brain',
  '/matches': 'Job Matches',
  '/matches/': 'Match details',
  '/settings': 'Settings',
  '/career-data': 'Career Data',
  '/crm': 'CRM Workspace',
};

export function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <MobileNav />
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <div className={`transition-all duration-200 md:ml-64 ${sidebarCollapsed ? 'md:ml-16' : ''}`}>
        <TopBar
          title={PAGE_TITLES[window.location.pathname] || 'CareerOS'}
          actions={
            user ? (
              <Button variant="secondary" onClick={handleLogout} className="hidden md:flex">
                Logout
              </Button>
            ) : null
          }
        />
        <main className="p-6" role="main" id="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
