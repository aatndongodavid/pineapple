// frontend/src/components/ui/StatusPill.tsx

import React from 'react';
import { cn } from '@/lib/utils';

interface StatusPillProps {
  status: string;
  className?: string;
}

const statusConfig: Record<string, { label: string; classes: string }> = {
  'Étudiant certifié': {
    label: 'Étudiant certifié',
    classes: 'bg-emerald-100 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800',
  },
  'Certification en attente': {
    label: 'Certification en attente',
    classes: 'bg-amber-100 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-800',
  },
  'Non certifié': {
    label: 'Non certifié',
    classes: 'bg-stone-200 dark:bg-stone-800 text-stone-700 dark:text-stone-300 border-stone-300 dark:border-stone-700',
  },
  'Archivé': {
    label: 'Archivé',
    classes: 'bg-red-100 dark:bg-red-950/40 text-red-800 dark:text-red-300 border-red-300 dark:border-red-800',
  },
  'Alumni': {
    label: 'Alumni',
    classes: 'bg-stone-200 dark:bg-stone-800 text-stone-700 dark:text-stone-300 border-stone-300 dark:border-stone-700',
  },
  'Enseignant vérifié': {
    label: 'Enseignant vérifié',
    classes: 'bg-emerald-100 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800',
  },
  'Administrateur': {
    label: 'Administrateur',
    classes: 'bg-orange-100 dark:bg-orange-950/40 text-orange-800 dark:text-orange-300 border-orange-300 dark:border-orange-800',
  },
};

export const StatusPill: React.FC<StatusPillProps> = ({ status, className }) => {
  const config = statusConfig[status] || {
    label: status,
    classes: 'bg-stone-200 dark:bg-stone-800 text-stone-700 dark:text-stone-300 border-stone-300 dark:border-stone-700',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border transition-colors',
        config.classes,
        className
      )}
    >
      {config.label}
    </span>
  );
};