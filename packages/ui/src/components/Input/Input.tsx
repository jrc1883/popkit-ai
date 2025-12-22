import * as React from 'react'
import { AlertCircle, CheckCircle2 } from 'lucide-react'

import { cn } from '../../utils/cn'

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string
  success?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  inputSize?: 'sm' | 'default' | 'lg'
}

const sizeClasses = {
  sm: 'h-8 px-2 text-xs',
  default: 'h-9 px-3 py-1 text-base md:text-sm',
  lg: 'h-12 px-4 text-base',
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      type,
      error,
      success,
      leftIcon,
      rightIcon,
      inputSize = 'default',
      ...props
    },
    ref
  ) => {
    const hasError = !!error
    const hasSuccess = success && !hasError

    return (
      <div className="relative w-full">
        {leftIcon && (
          <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
            {leftIcon}
          </div>
        )}
        <input
          type={type}
          data-slot="input"
          className={cn(
            'flex w-full min-w-0 rounded-md border bg-background transition-[color,box-shadow] outline-none',
            'file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground',
            'placeholder:text-muted-foreground',
            'selection:bg-primary selection:text-primary-foreground',
            'disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50',
            'dark:bg-input/30',
            sizeClasses[inputSize],
            leftIcon && 'pl-10',
            (rightIcon || hasError || hasSuccess) && 'pr-10',
            // Error state
            hasError &&
              'border-destructive focus-visible:border-destructive focus-visible:ring-destructive/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive',
            // Success state
            hasSuccess &&
              'border-success focus-visible:border-success focus-visible:ring-success/50 focus-visible:ring-[3px]',
            // Normal state
            !hasError &&
              !hasSuccess &&
              'border-input shadow-xs focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]',
            className
          )}
          ref={ref}
          aria-invalid={hasError}
          aria-describedby={hasError ? `${props.id}-error` : undefined}
          {...props}
        />
        {(rightIcon || hasError || hasSuccess) && (
          <div
            className={cn(
              'pointer-events-none absolute right-3 top-1/2 -translate-y-1/2',
              hasError && 'text-destructive',
              hasSuccess && 'text-success',
              !hasError && !hasSuccess && 'text-muted-foreground'
            )}
          >
            {hasError && <AlertCircle className="h-4 w-4" />}
            {hasSuccess && !hasError && <CheckCircle2 className="h-4 w-4" />}
            {!hasError && !hasSuccess && rightIcon}
          </div>
        )}
        {hasError && (
          <p
            id={props.id ? `${props.id}-error` : undefined}
            className="mt-1.5 text-xs text-destructive"
            role="alert"
          >
            {error}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export { Input }
