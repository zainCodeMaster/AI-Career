import { forwardRef } from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  description?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, description, error, id, className, ...props }, ref) => {
    const inputId = id || props.name;
    const errorId = `${inputId}-error`;
    const descriptionId = `${inputId}-description`;

    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={inputId} className="text-label text-neutral-700">
            {label}
          </label>
        )}
        {description && (
          <p id={descriptionId} className="text-caption">
            {description}
          </p>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : description ? descriptionId : undefined}
          className={[
            'w-full rounded-md border bg-white px-3 py-2 text-body',
            'placeholder:text-neutral-400',
            'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
            'disabled:bg-neutral-100 disabled:cursor-not-allowed',
            error ? 'border-error' : 'border-neutral-200 hover:border-neutral-300',
            className || '',
          ].join(' ')}
          {...props}
        />
        {error && (
          <p id={errorId} className="text-body-sm text-error">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
