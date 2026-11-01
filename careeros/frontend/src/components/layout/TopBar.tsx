import { Breadcrumbs } from './Breadcrumbs';
import { Search, Bell, Moon, Sun, LogOut, User, Settings, X } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface TopBarProps {
  title?: string;
  breadcrumbs?: { label: string; to?: string }[];
  actions?: React.ReactNode;
  showSearch?: boolean;
}

export function TopBar({ title, breadcrumbs, actions, showSearch = true }: TopBarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchOpen, setSearchOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [isDark, setIsDark] = useState(true);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (searchOpen && searchRef.current) {
      searchRef.current.focus();
    }
  }, [searchOpen]);

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const toggleTheme = () => {
    setIsDark((prev) => {
      const next = !prev;
      document.documentElement.classList.toggle('dark', next);
      localStorage.setItem('theme', next ? 'dark' : 'light');
      return next;
    });
  };

  // Initialize theme from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const shouldBeDark = savedTheme ? savedTheme === 'dark' : prefersDark;
    setIsDark(shouldBeDark);
    document.documentElement.classList.toggle('dark', shouldBeDark);
  }, []);

  return (
    <header className="sticky top-0 z-40 h-16 flex items-center justify-between border-b border-surface-border bg-surface/95 backdrop-blur-xl px-4 sm:px-6">
      <div className="flex items-center gap-4 min-w-0 flex-1">
        {/* Breadcrumbs or Title */}
        <div className="flex items-center gap-3 min-w-0 flex-1">
          {breadcrumbs && breadcrumbs.length > 0 ? (
            <Breadcrumbs items={breadcrumbs} />
          ) : title ? (
            <h1 className="text-h2 text-text-primary truncate">{title}</h1>
          ) : null}
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {/* Global Search */}
        {showSearch && (
          <div className="relative hidden sm:block">
            <button
              onClick={() => setSearchOpen(true)}
              className="flex items-center gap-2 w-64 sm:w-80 px-3 py-2 rounded-lg bg-surface-input border border-surface-border text-text-muted hover:border-brand-500/50 focus-within:border-brand-500 transition-all duration-150"
              type="button"
            >
              <Search size={18} className="text-text-muted shrink-0" aria-hidden="true" />
              <span className="text-body-sm truncate">Search jobs, skills, companies…</span>
              <kbd className="hidden md:inline-flex items-center gap-1 px-1.5 py-0.5 text-caption text-text-muted bg-surface-muted rounded">
                <kbd className="text-xs">⌘</kbd>
                <kbd className="text-xs">K</kbd>
              </kbd>
            </button>

            {/* Search Modal */}
            {searchOpen && (
              <div
                className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-black/50 backdrop-blur-sm animate-fade-in"
                onClick={() => setSearchOpen(false)}
              >
                <div
                  className="w-full max-w-2xl mx-4 bg-surface-card border border-surface-border rounded-xl shadow-xl overflow-hidden animate-slide-down"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="relative p-4">
                    <div className="relative">
                      <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" aria-hidden="true" />
                      <input
                        ref={searchRef}
                        type="search"
                        placeholder="Search jobs, skills, companies, people…"
                        className="w-full pl-10 pr-12 py-3 rounded-lg bg-surface-input border border-surface-border text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                        autoFocus
                        onKeyDown={(e) => e.key === 'Escape' && setSearchOpen(false)}
                        onClick={(e) => e.stopPropagation()}
                      />
                      <button
                        onClick={() => setSearchOpen(false)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-text-muted hover:text-text-primary transition-colors"
                        aria-label="Close search"
                      >
                        <X size={20} />
                      </button>
                    </div>
                    <div className="mt-3 flex items-center gap-2 text-caption text-text-muted">
                      <kbd className="px-2 py-1 bg-surface-muted rounded">⌘</kbd>
                      <kbd className="px-2 py-1 bg-surface-muted rounded">K</kbd>
                      <span>to open</span>
                      <span className="divider-vertical mx-1" />
                      <kbd className="px-2 py-1 bg-surface-muted rounded">Esc</kbd>
                      <span>to close</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-text-muted hover:bg-surface-muted hover:text-text-primary transition-colors"
          aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          type="button"
        >
          {isDark ? <Sun size={20} /> : <Moon size={20} />}
        </button>

        {/* Notifications */}
        <button
          className="relative p-2 rounded-lg text-text-muted hover:bg-surface-muted hover:text-text-primary transition-colors"
          aria-label="Notifications"
          type="button"
        >
          <Bell size={20} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-error rounded-full" />
        </button>

        {/* Custom Actions */}
        {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}

        {/* User Menu */}
        {user && (
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-surface-muted transition-colors"
              aria-expanded={userMenuOpen}
              aria-haspopup="true"
              type="button"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-brandViolet-500 flex items-center justify-center text-white font-medium">
                {user.full_name?.charAt(0) || user.email?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <span className="hidden md:block text-body text-text-primary truncate max-w-[120px]">
                {user.full_name || user.email}
              </span>
            </button>

            {userMenuOpen && (
              <div
                ref={userMenuRef}
                className="absolute right-0 mt-2 w-56 bg-surface-card border border-surface-border rounded-xl shadow-xl py-1 animate-slide-down"
                role="menu"
              >
                <div className="px-4 py-3 border-b border-surface-border">
                  <p className="text-body font-medium text-text-primary truncate">
                    {user.full_name || user.email}
                  </p>
                  <p className="text-caption text-text-muted truncate">
                    {user.email}
                  </p>
                </div>
                <button
                  onClick={() => { navigate('/profile'); setUserMenuOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-body text-text-secondary hover:bg-surface-muted hover:text-text-primary transition-colors"
                  role="menuitem"
                  type="button"
                >
                  <User size={18} />
                  Profile
                </button>
                <button
                  onClick={() => { navigate('/settings'); setUserMenuOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-body text-text-secondary hover:bg-surface-muted hover:text-text-primary transition-colors"
                  role="menuitem"
                  type="button"
                >
                  <Settings size={18} />
                  Settings
                </button>
                <div className="border-t border-surface-border my-1" />
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-body text-error hover:bg-error/10 transition-colors"
                  role="menuitem"
                  type="button"
                >
                  <LogOut size={18} />
                  Logout
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}