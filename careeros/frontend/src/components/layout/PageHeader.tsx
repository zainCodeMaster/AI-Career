import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

interface PageHeaderProps extends HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  actions?: React.ReactNode;
  breadcrumbs?: { label: string; to?: string }[];
}

export const PageHeader = forwardRef<HTMLDivElement, PageHeaderProps>(
  ({ className, title, description, subtitle, action, actions, breadcrumbs, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('section-header mb-6', className)}
        {...props}
      >
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between min-w-0">
          <div className="min-w-0">
            {breadcrumbs && breadcrumbs.length > 0 && (
              <nav className="mb-2" aria-label="Breadcrumb">
                <ol className="flex items-center gap-1.5 text-caption text-text-muted">
                  {breadcrumbs.map((item, index) => (
                    <li key={item.label} className="flex items-center gap-1.5">
                      {index > 0 && (
                        <span className="text-text-muted/50" aria-hidden="true">/</span>
                      )}
                      {item.to ? (
                        <a
                          href={item.to}
                          className="hover:text-text-primary transition-colors"
                        >
                          {item.label}
                        </a>
                      ) : (
                        <span className="text-text-primary font-medium">{item.label}</span>
                      )}
                    </li>
                  ))}
                </ol>
              </nav>
            )}
            <h1 className="text-display text-text-primary truncate">{title}</h1>
            {subtitle && <p className="text-body text-text-muted">{subtitle}</p>}
            {description && <p className="mt-1 text-body-sm text-text-muted max-w-2xl">{description}</p>}
          </div>
          <div className="flex items-center gap-2 shrink-0 mt-4 sm:mt-0">
            {action && <div>{action}</div>}
            {actions && <div className="flex items-center gap-2">{actions}</div>}
          </div>
        </div>
        {children && <div className="mt-4">{children}</div>}
      </div>
    );
  }
);

PageHeader.displayName = 'PageHeader';