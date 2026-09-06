// frontend/src/features/democracy/ResultsTab.tsx

import React from 'react';
import { motion } from 'framer-motion';
import { Download, BarChart3, CheckCircle2 } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

// Types
interface ResultItem {
  movement: string;
  votes: number;
  percentage: number;
}

const mockResults: ResultItem[] = [
  { movement: 'Mouvement Bleu', votes: 1650, percentage: 56.5 },
  { movement: 'Alliance Innovation', votes: 1267, percentage: 43.5 },
];

export const ResultsTab: React.FC = () => {
  const totalVotes = mockResults.reduce((acc, curr) => acc + curr.votes, 0);

  const handleDownloadReport = () => {
    // Simulation d'un téléchargement
    alert('Téléchargement du rapport électoral (simulation)');
  };

  return (
    <div className="space-y-6">
      <Card variant="neo-extruded" className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="h-6 w-6 text-pineapple" />
          <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
            Résultats officiels
          </h2>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          Total des bulletins dépouillés : {totalVotes}
        </p>

        <div className="space-y-5">
          {mockResults.map((result) => (
            <div key={result.movement}>
              <div className="flex justify-between mb-1">
                <span className="font-medium text-gray-800 dark:text-white">{result.movement}</span>
                <span className="text-sm text-gray-500">{result.votes} voix ({result.percentage.toFixed(1)}%)</span>
              </div>
              <div className="h-3 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${result.percentage}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                  className="h-full bg-gradient-to-r from-pineapple to-emerald-400"
                />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8">
          <Button
            variant="primary"
            onClick={handleDownloadReport}
            icon={Download}
          >
            Télécharger le rapport PDF
          </Button>
          <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
            <CheckCircle2 className="h-4 w-4" />
            Généré à partir de l'Audit Ledger immuable
          </p>
        </div>
      </Card>
    </div>
  );
};