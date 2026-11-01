import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular' | 'card';
  width?: string | number;
  height?: string | number;
}

export const Skeleton = forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, variant = 'text', width, height, ...props }, ref) => {
    const variantClasses = {
      text: 'h-4 w-full',
      circular: 'rounded-full',
      rectangular: 'rounded-lg',
      card: 'rounded-xl',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'skeleton animate-pulse bg-surface-muted',
          variantClasses[variant],
          className
        )}
        style={{ width, height }}
        {...props}
      />
    );
  }
);

Skeleton.displayName = 'Skeleton';

export const SkeletonText = ({ lines = 3, ...props }: { lines?: number } & Omit<SkeletonProps, 'variant'>) => (
  <div className="space-y-2" {...props}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton key={i} variant="text" width={i === lines - 1 ? '60%' : '100%'} />
    ))}
  </div>
);

export const SkeletonCard = ({ ...props }: Omit<SkeletonProps, 'variant'>) => (
  <Skeleton variant="card" className="h-32" {...props} />
);

export const SkeletonAvatar = ({ size = 'md', ...props }: { size?: 'sm' | 'md' | 'lg' | 'xl' } & Omit<SkeletonProps, 'variant' | 'width' | 'height'>) => {
  const sizes = { sm: 32, md: 40, lg: 48, xl: 64 };
  return <Skeleton variant="circular" width={sizes[size]} height={sizes[size]} {...props} />;
};

export const SkeletonTable = ({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) => (
  <div className="table-container">
    <table className="table">
      <thead>
        <tr>
          {Array.from({ length: columns }).map((_, i) => (
            <th key={i}><Skeleton variant="text" width="80%" height={24} /></th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Array.from({ length: rows }).map((_, row) => (
          <tr key={row}>
            {Array.from({ length: columns }).map((_, col) => (
              <td key={col}><Skeleton variant="text" width="90%" height={20} /></td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);