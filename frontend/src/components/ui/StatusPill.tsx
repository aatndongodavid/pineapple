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
    classes: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  },
  'Certification en attente': {
    label: 'Certification en attente',
    classes: 'bg-orange-100 text-orange-800 border-orange-300',
  },
  'Non certifié': {
    label: 'Non certifié',
    classes: 'bg-gray-200 text-gray-700 border-gray-300',
  },
  'Archivé': {
    label: 'Archivé',
    classes: 'bg-red-900 text-red-100 border-red-700',
  },
  'Alumni': {
    label: 'Alumni',
    classes: 'bg-blue-100 text-blue-800 border-blue-300',
  },
  'Enseignant vérifié': {
    label: 'Enseignant vérifié',
    classes: 'bg-violet-100 text-violet-800 border-violet-300',
  },
};

export const StatusPill: React.FC<StatusPillProps> = ({ status, className }) => {
  const config = statusConfig[status] || {
    label: status,
    classes: 'bg-gray-200 text-gray-700 border-gray-300',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border',
        config.classes,
        className
      )}
    >
      {config.label}
    </span>
  );
};