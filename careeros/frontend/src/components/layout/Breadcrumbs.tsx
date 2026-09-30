import { Link } from 'react-router-dom';
import { cn } from '../../lib/utils';

interface BreadcrumbItem {
  label: string;
  to?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  return (
    <nav aria-label="Breadcrumb" className={cn('flex items-center gap-2 text-body-sm', className)}>
      <ol className="flex items-center gap-2">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <li key={index} className="flex items-center gap-2">
              {index > 0 && <span className="text-neutral-400">/</span>}
              {item.to && !isLast ? (
                <Link to={item.to} className="text-primary hover:underline">
                  {item.label}
                </Link>
              ) : (
                <span className={cn(isLast ? 'font-medium text-neutral-900' : 'text-neutral-500')}>
                  {item.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
