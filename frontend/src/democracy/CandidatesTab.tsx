// frontend/src/features/democracy/CandidatesTab.tsx

import React from 'react';
import { motion } from 'framer-motion';
import { User, BadgeCheck } from 'lucide-react';
import { Card } from '@/components/ui/Card';

// ---------- Types ----------
interface Candidate {
  id: string;
  name: string;
  position: string; // ex: "Président", "Vice-président"
}

interface Movement {
  id: string;
  name: string;
  slogan: string;
  candidates: Candidate[];
}

// Données simulées (à remplacer par un appel API)
const mockMovements: Movement[] = [
  {
    id: 'mv1',
    name: 'Mouvement Bleu',
    slogan: 'Transparence et Progrès',
    candidates: [
      { id: 'c1', name: 'Alice Ndongo', position: 'Présidente' },
      { id: 'c2', name: 'Charlie Mbarga', position: 'Vice-président' },
      { id: 'c3', name: 'Diane Etoa', position: 'Secrétaire générale' },
    ],
  },
  {
    id: 'mv2',
    name: 'Alliance Innovation',
    slogan: 'Innover pour l’avenir',
    candidates: [
      { id: 'c4', name: 'Bob Kamga', position: 'Président' },
      { id: 'c5', name: 'Esther Fouda', position: 'Vice-présidente' },
      { id: 'c6', name: 'Franck Nkoa', position: 'Trésorier' },
    ],
  },
];

// ---------- Composant ----------
export const CandidatesTab: React.FC = () => {
  return (
    <div className="space-y-6">
      {mockMovements.map((movement, index) => (
        <motion.div
          key={movement.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <Card variant="neo-extruded" className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-pineapple/20 flex items-center justify-center text-pineapple font-bold">
                {movement.name.charAt(0)}
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
                  {movement.name}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 italic">
                  « {movement.slogan} »
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {movement.candidates.map((candidate) => (
                <div
                  key={candidate.id}
                  className="flex items-center gap-3 p-3 rounded-xl bg-background-light dark:bg-slate-800"
                >
                  <div className="w-9 h-9 rounded-full bg-white dark:bg-slate-700 flex items-center justify-center">
                    <User className="h-5 w-5 text-pineapple" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-800 dark:text-white">
                      {candidate.name}
                    </p>
                  </div>
                  <Badge variant="info" className="ml-auto">
                    {candidate.position}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        </motion.div>
      ))}
    </div>
  );
};