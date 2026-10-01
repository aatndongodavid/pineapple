// frontend/src/components/ui/Badge.tsx

import React from 'react';
import { cn } from '@/lib/utils';

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'primary';
}

const variantClasses: Record<string, string> = {
  default: 'bg-stone-200/60 dark:bg-stone-800/60 text-stone-700 dark:text-stone-300 border-stone-300 dark:border-stone-700',
  primary: 'bg-orange-100 dark:bg-orange-950/40 text-orange-800 dark:text-orange-300 border-orange-300 dark:border-orange-800',
  success: 'bg-emerald-100 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800',
  warning: 'bg-amber-100 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-800',
  danger: 'bg-red-100 dark:bg-red-950/40 text-red-800 dark:text-red-300 border-red-300 dark:border-red-800',
  info: 'bg-sky-100 dark:bg-sky-950/40 text-sky-800 dark:text-sky-300 border-sky-300 dark:border-sky-800',
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  className,
  variant = 'default',
}) => {
  return (
    <span
      className={cn(
        'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border transition-colors',
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  );
};