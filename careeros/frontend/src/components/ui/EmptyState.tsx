import { cn } from '../../lib/utils';

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({ title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3 rounded-md border border-neutral-200 bg-surface-muted p-8 text-center', className)}>
      <p className="text-h3 text-neutral-900">{title}</p>
      {description && <p className="text-body text-neutral-500 max-w-md">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
