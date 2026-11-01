import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  GitBranch,
  Settings,
  ChevronLeft,
  ChevronRight,
  Contact,
  Brain,
  Sparkles,
  Database,
  Menu,
  BriefcaseBusiness,
  FolderKanban,
  Activity,
} from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

const NAV_SECTIONS = [
  {
    title: 'Core',
    items: [
      { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { to: '/jobs', label: 'Jobs', icon: Briefcase },
      { to: '/job-discovery', label: 'Discovery Status', icon: Activity },
      { to: '/resumes', label: 'Resume Studio', icon: FileText },
    ],
  },
  {
    title: 'Career Intelligence',
    items: [
      { to: '/career-brain', label: 'Career Brain', icon: Brain },
      { to: '/matches', label: 'Job Matches', icon: Sparkles },
      { to: '/career-data', label: 'Career Data', icon: Database },
    ],
  },
  {
    title: 'Applications',
    items: [
      { to: '/applications', label: 'Applications', icon: FolderKanban },
      { to: '/pipeline', label: 'Pipeline', icon: GitBranch },
      { to: '/crm', label: 'CRM Workspace', icon: BriefcaseBusiness },
    ],
  },
  {
    title: 'Profile',
    items: [
      { to: '/profile', label: 'Career Profile', icon: Contact },
    ],
  },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();
  const { user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleClose = () => {
    setMobileOpen(false);
  };

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={handleClose}
          aria-hidden="true"
        />
      )}

      {/* Mobile toggle button */}
      <button
        className="md:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-surface-card border border-surface-border text-text-primary shadow-lg"
        onClick={() => setMobileOpen(true)}
        aria-label="Open navigation menu"
        type="button"
      >
        <Menu size={22} />
      </button>

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col border-r border-surface-border bg-surface transition-all duration-300 ease-in-out md:flex ${
          collapsed ? 'w-16' : 'w-64'
        } ${mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}
        aria-label="Main navigation"
      >
        <div className="flex h-16 shrink-0 items-center justify-between border-b border-surface-border px-4">
          {!collapsed && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brandViolet-500 flex items-center justify-center">
                <Sparkles size={18} className="text-white" />
              </div>
              <span className="text-h3 font-semibold text-text-primary">CareerOS</span>
            </div>
          )}
          <button
            onClick={onToggle}
            className="rounded-lg p-1.5 text-text-muted hover:bg-surface-muted hover:text-text-primary focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            type="button"
          >
            {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        <nav className="min-h-0 flex-1 overflow-y-auto px-2 py-4" aria-label="Main navigation">
          {NAV_SECTIONS.map((section) => (
            <div key={section.title} className="mb-6 animate-slide-up">
              {!collapsed && (
                <p className="mb-3 px-2 text-label text-text-muted">
                  {section.title}
                </p>
              )}
              <ul className="space-y-1" role="list">
                {section.items.map((item) => {
                  const isActive =
                    location.pathname === item.to || location.pathname.startsWith(`${item.to}/`);
                  const Icon = item.icon;

                  return (
                    <li key={item.to}>
                      <NavLink
                        to={item.to}
                        onClick={handleClose}
                        className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-body transition-all duration-150 ${
                          isActive
                            ? 'bg-brand-500/10 text-brand-400 border-l-2 border-brand-500'
                            : 'text-text-secondary hover:bg-surface-muted hover:text-text-primary'
                        }`}
                        aria-current={isActive ? 'page' : undefined}
                      >
                        <Icon size={20} className="shrink-0" aria-hidden="true" />
                        {!collapsed && <span className="truncate">{item.label}</span>}
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        <div className="shrink-0 border-t border-surface-border p-3 animate-slide-up">
          {!collapsed && user && (
            <div className="mb-3 p-3 rounded-lg bg-surface-muted">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-500 to-brandViolet-500 flex items-center justify-center text-white font-medium">
                  {user.email?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-body font-medium text-text-primary truncate">
                    {user.full_name || user.email}
                  </p>
                  <p className="text-caption text-text-muted truncate">
                    {user.email}
                  </p>
                </div>
              </div>
            </div>
          )}
          <NavLink
            to="/settings"
            onClick={handleClose}
            className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-body transition-all duration-150 ${
              location.pathname === '/settings'
                ? 'bg-brand-500/10 text-brand-400 border-l-2 border-brand-500'
                : 'text-text-secondary hover:bg-surface-muted hover:text-text-primary'
            }`}
            aria-current={location.pathname === '/settings' ? 'page' : undefined}
            aria-label={collapsed ? 'Settings' : undefined}
          >
            <Settings size={20} className="shrink-0" aria-hidden="true" />
            {!collapsed && <span>Settings</span>}
          </NavLink>
        </div>
      </aside>
    </>
  );
}