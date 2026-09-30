import { cn } from '../../lib/utils';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({ title = 'Something went wrong', message, onRetry, className }: ErrorStateProps) {
  return (
    <div className={cn('rounded-md border border-error-light bg-error-light p-4', className)}>
      <p className="text-body font-medium text-error-dark">{title}</p>
      <p className="text-body-sm text-error mt-1">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 inline-flex items-center rounded-md border border-error px-3 py-1.5 text-body-sm text-error hover:bg-error-light focus:outline-none focus:ring-2 focus:ring-error focus:ring-offset-2"
        >
          Try again
        </button>
      )}
    </div>
  );
}
