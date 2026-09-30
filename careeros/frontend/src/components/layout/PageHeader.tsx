import { cn } from '../../lib/utils';

interface PageHeaderProps {
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, description, action, className }: PageHeaderProps) {
  return (
    <header className={cn('flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between mb-6', className)}>
      <div>
        <h1 className="text-h1 text-neutral-900">{title}</h1>
        {description && <div className="text-metadata text-neutral-500 mt-1">{description}</div>}
      </div>
      {action && <div className="flex items-center gap-2">{action}</div>}
    </header>
  );
}
