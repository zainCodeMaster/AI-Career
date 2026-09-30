import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Menu,
  X,
  LayoutDashboard,
  Briefcase,
  FileText,
  Users,
  GitBranch,
  Contact,
  Brain,
  Sparkles,
  Database,
} from 'lucide-react';

const MOBILE_NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/job-discovery', label: 'Discovery Status', icon: Briefcase },
  { to: '/resumes', label: 'Resumes', icon: FileText },
  { to: '/applications', label: 'Applications', icon: Users },
  { to: '/pipeline', label: 'Pipeline', icon: GitBranch },
  { to: '/profile', label: 'Profile', icon: Contact },
  { to: '/career-brain', label: 'Career Brain', icon: Brain },
  { to: '/matches', label: 'Job Matches', icon: Sparkles },
  { to: '/career-data', label: 'Career Data', icon: Database },
  { to: '/crm', label: 'CRM Workspace', icon: Users },
];

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed top-4 left-4 z-50 rounded-md border border-neutral-200 bg-white p-2 shadow-sm md:hidden"
        aria-label="Open navigation menu"
      >
        <Menu size={20} />
      </button>

      {open && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setOpen(false)} />
          <nav
            className="absolute inset-y-0 left-0 w-64 bg-white shadow-lg"
            aria-label="Mobile navigation"
          >
            <div className="flex items-center justify-between h-14 px-4 border-b border-neutral-200">
              <span className="text-h3 text-neutral-900 font-semibold">CareerOS</span>
              <button
                onClick={() => setOpen(false)}
                className="rounded-md p-1.5 text-neutral-500 hover:bg-neutral-100"
                aria-label="Close navigation menu"
              >
                <X size={20} />
              </button>
            </div>
            <ul className="py-4 px-2 space-y-1">
              {MOBILE_NAV_ITEMS.map((item) => {
                const isActive =
                  location.pathname === item.to || location.pathname.startsWith(item.to + '/');
                const Icon = item.icon;
                return (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      onClick={() => setOpen(false)}
                      className={`
                        flex items-center gap-3 rounded-md px-3 py-2 text-body transition-colors
                        ${
                          isActive
                            ? 'bg-primary-light text-primary-dark font-medium'
                            : 'text-neutral-600 hover:bg-neutral-100'
                        }
                      `}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <Icon size={18} />
                      <span>{item.label}</span>
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>
      )}
    </>
  );
}
