// frontend/src/features/opportunities/OpportunityCard.tsx

import React from 'react';
import { motion } from 'framer-motion';
import { Briefcase, CheckCircle, Clock } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

export type OpportunityType = 'PROJECT' | 'RESEARCH' | 'CHALLENGE' | 'INTERNSHIP' | 'STARTUP';
export type OpportunityStatus = 'OPEN' | 'CLOSED' | 'DRAFT' | 'ARCHIVED';

export interface Opportunity {
  id: string;
  title: string;
  type: OpportunityType;
  description: string;
  required_skills: string[];
  status: OpportunityStatus;
}

interface OpportunityCardProps {
  opportunity: Opportunity;
  onApply?: (id: string) => void;
}

export const OpportunityCard: React.FC<OpportunityCardProps> = ({
  opportunity,
  onApply,
}) => {
  const typeLabels: Record<OpportunityType, string> = {
    PROJECT: 'Projet',
    RESEARCH: 'Recherche',
    CHALLENGE: 'Défi Entreprise',
    INTERNSHIP: 'Stage',
    STARTUP: 'Startup',
  };

  const isOpen = opportunity.status === 'OPEN';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      <Card variant="neo-extruded" className="p-5 flex flex-col h-full">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-800 dark:text-white truncate">
              {opportunity.title}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {typeLabels[opportunity.type]}
            </p>
          </div>
          <Badge variant={isOpen ? 'success' : 'default'} className="ml-2 shrink-0">
            {isOpen ? (
              <><CheckCircle className="h-3 w-3 mr-1" /> Ouvert</>
            ) : (
              <><Clock className="h-3 w-3 mr-1" /> Fermé</>
            )}
          </Badge>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-3 flex-1">
          {opportunity.description}
        </p>

        <div className="mt-4 flex flex-wrap gap-1.5">
          {opportunity.required_skills.map((skill) => (
            <span
              key={skill}
              className="px-2 py-1 text-xs rounded-full bg-pineapple/10 text-pineapple"
            >
              {skill}
            </span>
          ))}
        </div>

        <div className="mt-4">
          <Button
            variant="primary"
            size="sm"
            className="w-full"
            onClick={() => onApply?.(opportunity.id)}
            disabled={!isOpen}
            icon={Briefcase}
          >
            Postuler
          </Button>
        </div>
      </Card>
    </motion.div>
  );
};