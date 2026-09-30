import { cn } from '../../lib/utils';

interface CardProps {
  className?: string;
  children: React.ReactNode;
  as?: 'div' | 'section' | 'article';
  onClick?: () => void;
}

export function Card({ className, children, as: Component = 'div', onClick }: CardProps) {
  return (
    <Component
      onClick={onClick}
      className={cn(
        'rounded-md border border-neutral-200 bg-surface p-4 shadow-sm',
        onClick && 'cursor-pointer',
        className
      )}
    >
      {children}
    </Component>
  );
}
