import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  Users,
  GitBranch,
  Settings,
  ChevronLeft,
  ChevronRight,
  Contact,
  Brain,
  Sparkles,
  Database,
} from 'lucide-react';

const NAV_SECTIONS = [
  {
    title: 'Core',
    items: [
      { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { to: '/jobs', label: 'Jobs', icon: Briefcase },
      { to: '/job-discovery', label: 'Discovery Status', icon: Briefcase },
      { to: '/resumes', label: 'Resumes', icon: FileText },
    ],
  },
  {
    title: 'Career',
    items: [
      { to: '/applications', label: 'Applications', icon: Users },
      { to: '/pipeline', label: 'Pipeline', icon: GitBranch },
      { to: '/profile', label: 'Profile', icon: Contact },
      { to: '/career-brain', label: 'Career Brain', icon: Brain },
      { to: '/matches', label: 'Job Matches', icon: Sparkles },
      { to: '/career-data', label: 'Career Data', icon: Database },
      { to: '/crm', label: 'CRM Workspace', icon: Users },
    ],
  },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 hidden h-screen flex-col border-r border-neutral-200 bg-surface transition-all duration-200 md:flex ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="flex h-14 shrink-0 items-center justify-between border-b border-neutral-200 px-4">
        {!collapsed && <span className="text-h3 font-semibold text-neutral-900">CareerOS</span>}
        <button
          onClick={onToggle}
          className="rounded-md p-1.5 text-neutral-500 hover:bg-neutral-100 focus:outline-none focus:ring-2 focus:ring-primary"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          type="button"
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <nav className="min-h-0 flex-1 overflow-y-auto px-2 py-4" aria-label="Main navigation">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title} className="mb-4">
            {!collapsed && (
              <p className="mb-2 px-2 text-caption uppercase tracking-wider text-neutral-500">
                {section.title}
              </p>
            )}
            <ul className="space-y-1">
              {section.items.map((item) => {
                const isActive =
                  location.pathname === item.to || location.pathname.startsWith(`${item.to}/`);
                const Icon = item.icon;

                return (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      className={`flex items-center gap-3 rounded-md px-3 py-2 text-body transition-colors ${
                        isActive
                          ? 'bg-primary-light font-medium text-primary-dark'
                          : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
                      }`}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <Icon size={18} className="shrink-0" aria-hidden="true" />
                      {!collapsed && <span>{item.label}</span>}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="shrink-0 border-t border-neutral-200 p-2">
        <NavLink
          to="/settings"
          className="flex items-center gap-3 rounded-md px-3 py-2 text-body text-neutral-600 transition-colors hover:bg-neutral-100 hover:text-neutral-900"
          aria-label={collapsed ? 'Settings' : undefined}
        >
          <Settings size={18} className="shrink-0" aria-hidden="true" />
          {!collapsed && <span>Settings</span>}
        </NavLink>
      </div>
    </aside>
  );
}
