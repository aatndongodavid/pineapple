// frontend/src/components/ui/Button.tsx

import React, { forwardRef } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { Loader2, LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

type ButtonVariant = 'primary' | 'secondary' | 'neo' | 'glass' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  children?: React.ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  icon?: LucideIcon;
  className?: string;
  disabled?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-white hover:bg-primary-dark active:bg-orange-800 focus-visible:ring-primary',
  secondary: 'bg-secondary text-white hover:bg-secondary-dark active:bg-emerald-800 focus-visible:ring-secondary',
  neo: 'bg-white dark:bg-slate-800 text-stone-800 dark:text-stone-100 border border-stone-200 dark:border-stone-700 shadow-card hover:bg-stone-50 dark:hover:bg-slate-700 focus-visible:ring-primary',
  glass: 'glass-panel text-white hover:bg-white/20 focus-visible:ring-primary',
  ghost: 'bg-transparent text-stone-700 dark:text-stone-200 hover:bg-stone-100 dark:hover:bg-white/10 focus-visible:ring-stone-400',
  danger: 'bg-danger text-white hover:bg-red-700 active:bg-red-800 focus-visible:ring-danger',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm rounded-lg',
  md: 'px-4 py-2 text-base rounded-xl',
  lg: 'px-6 py-3 text-lg rounded-2xl',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      icon: Icon,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    const content = isLoading ? (
      <Loader2 className="animate-spin h-5 w-5" />
    ) : (
      <>
        {Icon && <Icon className="h-5 w-5" />}
        {children}
      </>
    );

    return (
      <motion.button
        ref={ref}
        whileTap={disabled ? undefined : { scale: 0.98 }}
        className={cn(
          'inline-flex items-center justify-center gap-2 font-medium transition-colors duration-200',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {content}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';
