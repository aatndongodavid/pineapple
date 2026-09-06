// frontend/src/features/democracy/CampaignTab.tsx

import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, TrendingUp } from 'lucide-react';
import { Card } from '@/components/ui/Card';

// ---------- Types ----------
interface MovementCampaign {
  id: string;
  name: string;
  program: string;
  engagementScore: number; // score d'engagement observé (ex: 78)
}

// Données simulées
const mockCampaigns: MovementCampaign[] = [
  {
    id: 'mv1',
    name: 'Mouvement Bleu',
    program:
      'Amélioration des infrastructures, plus de transparence dans la gestion du BDE, création d’un espace de coworking étudiant.',
    engagementScore: 82,
  },
  {
    id: 'mv2',
    name: 'Alliance Innovation',
    program:
      'Digitalisation des services administratifs, soutien aux projets étudiants, mise en place de partenariats avec des entreprises tech.',
    engagementScore: 76,
  },
];

// ---------- Composant ----------
export const CampaignTab: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Avertissement permanent */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 flex items-start gap-3"
      >
        <AlertTriangle className="h-6 w-6 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <div>
          <h3 className="font-semibold text-amber-800 dark:text-amber-200">
            Garde-fou de neutralité
          </h3>
          <p className="text-sm text-amber-700 dark:text-amber-300">
            Le Campaign Engagement Score mesure uniquement l’engagement observé en ligne
            (vues, réactions, participation aux événements). Il ne constitue en aucun cas
            une prédiction du résultat électoral et ne doit pas être interprété comme tel.
          </p>
        </div>
      </motion.div>

      {/* Liste des programmes */}
      <div className="space-y-4">
        {mockCampaigns.map((campaign, index) => (
          <motion.div
            key={campaign.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card variant="neo-extruded" className="p-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
                  {campaign.name}
                </h3>
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-pineapple/10 text-pineapple">
                  <TrendingUp className="h-4 w-4" />
                  <span className="text-sm font-medium">
                    Engagement : {campaign.engagementScore}
                  </span>
                </div>
              </div>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {campaign.program}
              </p>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
};