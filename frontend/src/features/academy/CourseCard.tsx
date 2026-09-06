// frontend/src/features/academy/CourseCard.tsx

import React from 'react';
import { motion } from 'framer-motion';
import { BookOpen, Lock, Star, Eye, Clock } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

export type AcademyDocumentType = 'COURSE' | 'TD' | 'TP' | 'EXAM' | 'CORRIGE_PREMIUM' | 'RESEARCH_PAPER';

export interface CourseCardData {
  id: string;
  title: string;
  type: AcademyDocumentType;
  faculty: string;
  filiere: string;
  level: string;
  isPremium: boolean;
  price?: number; // en FCFA
  author?: string;
  views_count?: number;
}

interface CourseCardProps {
  data: CourseCardData;
  onConsult?: (id: string) => void;
  onPurchase?: (id: string) => void;
}

export const CourseCard: React.FC<CourseCardProps> = ({ data, onConsult, onPurchase }) => {
  const typeLabels: Record<AcademyDocumentType, string> = {
    COURSE: 'Cours',
    TD: 'TD',
    TP: 'TP',
    EXAM: 'Examen',
    CORRIGE_PREMIUM: 'Corrigé Premium',
    RESEARCH_PAPER: 'Article de recherche',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      <Card variant="glass" className="p-5 h-full flex flex-col">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-800 dark:text-white truncate">
              {data.title}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {typeLabels[data.type]} · {data.author || 'Enseignant'}
            </p>
          </div>
          {data.isPremium && (
            <Badge variant="warning" className="ml-2 shrink-0">
              <Lock className="h-3 w-3 mr-1" />
              Premium
            </Badge>
          )}
        </div>

        <div className="mt-2 flex flex-wrap gap-1 text-xs text-gray-600 dark:text-gray-300">
          <span className="px-2 py-1 rounded-full bg-background-light dark:bg-slate-800">
            {data.faculty}
          </span>
          <span className="px-2 py-1 rounded-full bg-background-light dark:bg-slate-800">
            {data.filiere}
          </span>
          <span className="px-2 py-1 rounded-full bg-background-light dark:bg-slate-800">
            Niveau {data.level}
          </span>
        </div>

        <div className="mt-4 flex items-center justify-between flex-1">
          {data.isPremium ? (
            <span className="text-lg font-bold text-amber-600 dark:text-amber-400">
              {data.price?.toLocaleString('fr-FR') || '—'} FCFA
            </span>
          ) : (
            <span className="text-sm text-gray-500 flex items-center gap-1">
              <BookOpen className="h-4 w-4" />
              Accès libre
            </span>
          )}
          {data.views_count !== undefined && (
            <span className="text-xs text-gray-400 flex items-center gap-1">
              <Eye className="h-3.5 w-3.5" /> {data.views_count}
            </span>
          )}
        </div>

        <div className="mt-4">
          {data.isPremium ? (
            <Button
              variant="primary"
              className="w-full"
              onClick={() => onPurchase?.(data.id)}
            >
              Acheter
            </Button>
          ) : (
            <Button
              variant="secondary"
              className="w-full"
              onClick={() => onConsult?.(data.id)}
            >
              Consulter
            </Button>
          )}
        </div>
      </Card>
    </motion.div>
  );
};