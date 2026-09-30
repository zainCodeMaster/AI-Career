import { cn } from '../../lib/utils';

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-md bg-neutral-200',
        className || 'h-4 w-full'
      )}
    />
  );
}
