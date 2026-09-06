// frontend/src/components/ui/Badge.tsx

import React from 'react';
import { cn } from '@/lib/utils';

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
}

const variantClasses: Record<string, string> = {
  default: 'bg-white/20 text-white border-white/20',
  success: 'bg-emerald-100/20 text-emerald-200 border-emerald-300/30',
  warning: 'bg-yellow-100/20 text-yellow-200 border-yellow-300/30',
  danger: 'bg-red-100/20 text-red-200 border-red-300/30',
  info: 'bg-blue-100/20 text-blue-200 border-blue-300/30',
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  className,
  variant = 'default',
}) => {
  return (
    <span
      className={cn(
        'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium',
        'backdrop-blur-md border transition-colors',
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  );
};