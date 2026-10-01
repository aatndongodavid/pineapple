// frontend/src/components/ui/Card.tsx

import React from 'react';
import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  variant?: 'default' | 'flat' | 'outline' | 'glass' | 'neo-extruded' | 'neo-inset';
  className?: string;
}

const variantClasses: Record<NonNullable<CardProps['variant']>, string> = {
  default: 'bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl shadow-card',
  flat: 'bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl shadow-card',
  outline: 'bg-background-light/50 dark:bg-stone-950/50 border border-stone-200/80 dark:border-stone-800/80 rounded-2xl',
  glass: 'glass-panel rounded-2xl',
  'neo-extruded': 'bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl shadow-card',
  'neo-inset': 'bg-background-light/50 dark:bg-stone-950/50 border border-stone-200/80 dark:border-stone-800/80 rounded-2xl',
};

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'flat',
  className,
}) => {
  return (
    <div className={cn(variantClasses[variant], className)}>
      {children}
    </div>
  );
};