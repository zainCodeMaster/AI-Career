import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

interface EmptyStateProps extends HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export const EmptyState = forwardRef<HTMLDivElement, EmptyStateProps>(
  ({ className, title, description, icon, action, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('empty-state', className)}
        {...props}
      >
        {icon && <div className="empty-state-icon" aria-hidden="true">{icon}</div>}
        {children ? (
          children
        ) : (
          <>
            <h3 className="empty-state-title">{title}</h3>
            {description && <p className="empty-state-description">{description}</p>}
          </>
        )}
        {action && <div className="mt-4">{action}</div>}
      </div>
    );
  }
);

EmptyState.displayName = 'EmptyState';