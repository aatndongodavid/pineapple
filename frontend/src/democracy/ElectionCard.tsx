// frontend/src/features/democracy/ElectionCard.tsx

import React from 'react';
import { motion } from 'framer-motion';
import { Calendar, Clock, ChevronRight } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';

type ElectionStatus = 'DRAFT' | 'CAMPAIGN' | 'VOTING_OPEN' | 'VOTING_CLOSED' | 'RESULTS_PUBLISHED' | 'ARCHIVED';

interface ElectionCardData {
  id: string;
  title: string;
  electionType: string;
  status: ElectionStatus;
  votingStartAt: string;
  votingEndAt: string;
}

interface ElectionCardProps {
  election: ElectionCardData;
  onClick?: () => void;
  className?: string;
}

function getStatusLabel(status: ElectionStatus): string {
  switch (status) {
    case 'DRAFT': return 'Brouillon';
    case 'CAMPAIGN': return 'Campagne';
    case 'VOTING_OPEN': return 'Vote ouvert';
    case 'VOTING_CLOSED': return 'Dépouillement';
    case 'RESULTS_PUBLISHED': return 'Résultats publiés';
    case 'ARCHIVED': return 'Archivée';
  }
}

function getStatusVariant(status: ElectionStatus): 'default' | 'success' | 'warning' | 'danger' | 'info' {
  switch (status) {
    case 'VOTING_OPEN': return 'success';
    case 'VOTING_CLOSED': return 'warning';
    case 'RESULTS_PUBLISHED': return 'info';
    case 'ARCHIVED': return 'default';
    case 'DRAFT': return 'default';
    case 'CAMPAIGN': return 'info';
  }
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }) +
    ' ' + date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

export const ElectionCard: React.FC<ElectionCardProps> = ({ election, onClick, className }) => {
  const statusVariant = getStatusVariant(election.status);
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <button
        onClick={onClick}
        className={cn(
          'w-full text-left p-4 rounded-2xl bg-white/20 dark:bg-slate-800/50 backdrop-blur-md border border-white/30 dark:border-slate-700',
          'hover:bg-white/30 dark:hover:bg-slate-800/70 transition-colors shadow-neo-extruded dark:shadow-neo-dark-extruded',
          className
        )}
      >
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-800 dark:text-white truncate">{election.title}</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">{election.electionType}</p>
          </div>
          <Badge variant={statusVariant} className="ml-2">
            {getStatusLabel(election.status)}
          </Badge>
        </div>
        <div className="mt-3 flex flex-wrap gap-3 text-xs text-gray-500 dark:text-gray-400">
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            {formatDate(election.votingStartAt)}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {formatDate(election.votingEndAt)}
          </span>
        </div>
        <div className="mt-2 flex justify-end">
          <ChevronRight className="h-4 w-4 text-gray-400" />
        </div>
      </button>
    </motion.div>
  );
};