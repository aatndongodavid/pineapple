// frontend/src/components/ui/Card.tsx

import React from 'react';
import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  variant?: 'flat' | 'neo-extruded' | 'neo-inset' | 'glass';
  className?: string;
}

const variantClasses: Record<NonNullable<CardProps['variant']>, string> = {
  flat: 'bg-white dark:bg-slate-800 rounded-2xl shadow-sm',
  'neo-extruded': 'bg-background-light dark:bg-background-dark rounded-2xl shadow-neo-extruded dark:shadow-neo-dark-extruded',
  'neo-inset': 'bg-background-light dark:bg-background-dark rounded-2xl shadow-neo-inset dark:shadow-neo-dark-inset',
  glass: 'glass-panel rounded-2xl',
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