import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';
import { Button } from './Button';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface ErrorStateProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
  showHomeLink?: boolean;
}

export const ErrorState = forwardRef<HTMLDivElement, ErrorStateProps>(
  ({ className, title = 'Something went wrong', message, onRetry, retryLabel = 'Try again', showHomeLink = true, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('card p-6 text-center max-w-md mx-auto', className)}
        role="alert"
        {...props}
      >
        <div className="w-12 h-12 rounded-full bg-error/10 flex items-center justify-center mx-auto mb-4">
          <AlertTriangle size={24} className="text-error" aria-hidden="true" />
        </div>
        <h3 className="text-h3 text-text-primary mb-2">{title}</h3>
        <p className="text-body text-text-muted mb-6">{message}</p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          {onRetry && (
            <Button variant="primary" onClick={onRetry}>
              <RefreshCw size={18} className="mr-2" />
              {retryLabel}
            </Button>
          )}
          {showHomeLink && (
            <a href="/dashboard" className="btn btn-secondary">
              <Home size={18} className="mr-2" />
              Go to Dashboard
            </a>
          )}
        </div>
      </div>
    );
  }
);

ErrorState.displayName = 'ErrorState';