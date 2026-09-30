import { Breadcrumbs } from './Breadcrumbs';

interface TopBarProps {
  title: string;
  breadcrumbs?: { label: string; to?: string }[];
  actions?: React.ReactNode;
}

export function TopBar({ title, breadcrumbs, actions }: TopBarProps) {
  return (
    <header className="sticky top-0 z-30 h-14 flex items-center justify-between border-b border-neutral-200 bg-surface/95 px-6 backdrop-blur">
      <div className="flex items-center gap-4 min-w-0">
        {breadcrumbs && breadcrumbs.length > 0 ? (
          <Breadcrumbs items={breadcrumbs} />
        ) : (
          <h1 className="text-h1 text-neutral-900 truncate">{title}</h1>
        )}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </header>
  );
}
