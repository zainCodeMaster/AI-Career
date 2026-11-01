import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

const PAGE_TITLES: Record<string, string> = {
  '/jobs': 'Jobs',
  '/jobs/': 'Job Details',
  '/job-discovery': 'Job Discovery',
  '/resumes': 'Resume Studio',
  '/resumes/': 'Resume Editor',
  '/dashboard': 'Dashboard',
  '/applications': 'Applications',
  '/applications/': 'Application Details',
  '/pipeline': 'Pipeline',
  '/profile': 'Career Profile',
  '/career-brain': 'Career Brain',
  '/matches': 'Job Matches',
  '/matches/': 'Match Details',
  '/settings': 'Settings',
  '/career-data': 'Career Data',
  '/crm': 'CRM Workspace',
};

export function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-surface dark">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <div className={`transition-all duration-200 md:ml-64 ${sidebarCollapsed ? 'md:ml-16' : ''}`}>
        <TopBar title={PAGE_TITLES[window.location.pathname] || 'CareerOS'} />
        <main className="p-4 sm:p-6 lg:p-8" role="main" id="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}